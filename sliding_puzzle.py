import subprocess
from argparse import ArgumentParser

def load_instance(input_file_name):
    # read the input instance
    # the instance is the makespan to be used, the size of the grid, and the placement of tiles in the grid
    # tile 0 is the empty space
    global MAKESPAN, GRID_SIZE, NR_TILES, NR_EDGES, NR_AT_VAR
    tiles = []
    with open(input_file_name, "r") as file:
        MAKESPAN = int(next(file))      # first line is the makespan
        GRID_SIZE = int(next(file))     # second line is the grid size
        for line in file:
            line = line.split()
            if line:
                line = [int(i) for i in line]
                tiles.extend(line)
    
    NR_TILES = GRID_SIZE*GRID_SIZE
    NR_EDGES = 2*(NR_TILES-GRID_SIZE)
    NR_AT_VAR = NR_TILES*NR_TILES*(MAKESPAN+1)

    return tiles

def encode(instance):
    # given the instance, create a cnf formula, i.e. a list of lists of integers
    # also return the total number of variables used

    # varaibles At(n,p,t) encode that tile n is at position p in timestep t
    # variables Swap(p1,p2,t) encode that the tile at position p1 swaped with the tile at position p2 
    #   - this does not give us information which tile is at postion p1 or p2
    #   - this infomation is extrapolated by connecting the variables using clauses
    # each variable is represented by an integer, varaibles are numbered from 1
    # since we know min and max values for n, p, t, it is easy to calculate the corresponding variable number
    # alternatively, you can use a dictionary

    cnf = []
    edges = create_edges()
    nr_vars = NR_AT_VAR + NR_EDGES*(MAKESPAN) # At vars + swap vars
    
    # the initial positions
    for p, n in enumerate(instance):
        cnf.append([pos_to_atID(n, p, 0), 0])

    # the goal positions
    for p in range(NR_TILES):
        cnf.append([pos_to_atID(p, p, MAKESPAN), 0])

    # no two tiles are at the same place at the same time, i.e. at most 1 of n is in p, t
    for t in range(MAKESPAN+1):
        for p in range(NR_TILES):
            for n1 in range(NR_TILES):
                for n2 in range(n1+1, NR_TILES):
                    cnf.append([-pos_to_atID(n1,p,t), -pos_to_atID(n2,p,t), 0])

    # a tile can not be at two places at the same time, i.e. at most 1 of p is in n, t
    for t in range(MAKESPAN+1):
        for n in range(NR_TILES):
            for p1 in range(NR_TILES):
                for p2 in range(p1+1, NR_TILES):
                    cnf.append([-pos_to_atID(n,p1,t), -pos_to_atID(n,p2,t), 0])

    # there is at most one swap at any timestep
    # if we added also "at most one" constraint, using larger makespan that the optimum might cause the CNF to be UNSAT
    # by not including "at most one", we allow "no op" actions
    for t in range(MAKESPAN):
        #at_least_one = []
        for e1 in range(len(edges)):
            #at_least_one.append(edge_to_swapID(e1, t))
            for e2 in range(e1+1,len(edges)):
                cnf.append([-edge_to_swapID(e1, t), -edge_to_swapID(e2, t), 0])
        #at_least_one.append(0)
        #cnf.append(at_least_one)

    # if the tiles are swaping, one of them has to be 0
    for t in range(MAKESPAN):
        for e in range(len(edges)):
            u,v = edges[e]
            cnf.append([-edge_to_swapID(e, t), pos_to_atID(0,u,t), pos_to_atID(0,v,t), 0])

    # if something is swaping from u to v and tile n is in u, it will be in v in the next timestep
    # and symmetricaly for v
    for t in range(MAKESPAN):
        for e in range(len(edges)):
            u,v = edges[e]
            for n in range(NR_TILES):
                cnf.append([-edge_to_swapID(e, t), -pos_to_atID(n,u,t), pos_to_atID(n,v,t+1), 0])
                cnf.append([-edge_to_swapID(e, t), -pos_to_atID(n,v,t), pos_to_atID(n,u,t+1), 0])

    # if there is no swap from a position, the tile remains in the position
    for t in range(MAKESPAN):
        for p in range(NR_TILES):
            outgoing_edges = get_outgoing_edges(p, edges)
            for n in range(NR_TILES):
                clause = [-pos_to_atID(n,p,t), pos_to_atID(n,p,t+1)]
                for e in outgoing_edges:
                    clause.append(edge_to_swapID(e, t))
                clause.append(0)
                cnf.append(clause)

    return (cnf, nr_vars)

def pos_to_atID(n, p, t):
    return t*NR_TILES*NR_TILES + p*NR_TILES + n + 1

def edge_to_swapID(e, t):
    return NR_EDGES*t + e + 1 + NR_AT_VAR # swap varaibles are indexed after at variables

def create_edges():
    edges = []
    for n in range(NR_TILES):
        if (n+1) % GRID_SIZE != 0:
            edges.append((n, n+1))
        if n+GRID_SIZE < NR_TILES:
            edges.append((n, n+GRID_SIZE))
    return edges

def get_outgoing_edges(p, edges):
    outgoing_edges = []
    for i, e in enumerate(edges):
        if p in e:
            outgoing_edges.append(i)
    return outgoing_edges

def call_solver(cnf, nr_vars, output_name, solver_name, verbosity):
    # print CNF into formula.cnf in DIMACS format
    with open(output_name, "w") as file:
        file.write("p cnf " + str(nr_vars) + " " + str(len(cnf)) + '\n')
        for clause in cnf:
            file.write(' '.join(str(lit) for lit in clause) + '\n')

    # call the solver and return the output
    return subprocess.run(['./' + solver_name, '-model', '-verb=' + str(verbosity) , output_name], stdout=subprocess.PIPE)

def print_result(result):
    for line in result.stdout.decode('utf-8').split('\n'):
        print(line)                 # print the whole output of the SAT solver to stdout, so you can see the raw output for yourself

    # check the returned result
    if (result.returncode == 20):       # returncode for SAT is 10, for UNSAT is 20
        return

    # parse the model from the output of the solver
    # the model starts with 'v'
    model = []
    for line in result.stdout.decode('utf-8').split('\n'):
        if line.startswith("v"):    # there might be more lines of the model, each starting with 'v'
            vars = line.split(" ")
            vars.remove("v")
            model.extend(int(v) for v in vars)      
    model.remove(0) # 0 is the end of the model, just ignore it

    print()
    print("##################################################################")
    print("###########[ Human readable result of the tile puzzle ]###########")
    print("##################################################################")
    print()

    # decode the meaning of the assignment
    for t in range(MAKESPAN+1):
        print("Timestep " + str(t) + ":")
        for p in range(NR_TILES):
            for n in range(NR_TILES):
                if model[pos_to_atID(n,p,t) - 1] > 0:
                    print(n, end=" ")
            if (p+1) % GRID_SIZE == 0:
                print()
        print()

if __name__ == "__main__":

    parser = ArgumentParser()

    parser.add_argument(
        "-i",
        "--input",
        default="input.in",
        type=str,
        help=(
            "The instance file."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        default="formula.cnf",
        type=str,
        help=(
            "Output file for the DIMACS format (i.e. the CNF formula)."
        ),
    )
    parser.add_argument(
        "-s",
        "--solver",
        default="glucose-syrup",
        type=str,
        help=(
            "The SAT solver to be used."
        ),
    )
    parser.add_argument(
        "-v",
        "--verb",
        default=1,
        type=int,
        choices=range(0,2),
        help=(
            "Verbosity of the SAT solver used."
        ),
    )
    args = parser.parse_args()

    # get the input instance
    instance = load_instance(args.input)

    # encode the problem to create CNF formula
    cnf, nr_vars = encode(instance)

    # call the SAT solver and get the result
    result = call_solver(cnf, nr_vars, args.output, args.solver, args.verb)

    # interpret the result and print it in a human-readable format
    print_result(result)
