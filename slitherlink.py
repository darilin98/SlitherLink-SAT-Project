import subprocess
from argparse import ArgumentParser

def load_instance(input_file_name):
    
    board = []
    with open(input_file_name, "r") as input:
        global GRID_LENGTH, GRID_HEIGTH, EDGE_COUNT, ID_OFFSET
        # Load cell constraint values
        for line in input:
            elements = line.split()
            board.append([int(x) if x!= '.' else None for x in elements])


    GRID_HEIGTH = len(board)
    GRID_LENGTH = len(board[0]) if GRID_HEIGTH > 0 else 0

    # total number of edges formula
    EDGE_COUNT = GRID_HEIGTH * (GRID_LENGTH + 1) + GRID_LENGTH * (GRID_HEIGTH + 1)
   
    ID_OFFSET = EDGE_COUNT + 1 

    return board

def encode(instance): 
    # given the instance, create a cnf formula, 
    # i.e. a list of lists of integers
    # also return the total number of variables used

    cnf = []
    # every edge holds information if it exists and if it is reachable
    variable_count = EDGE_COUNT
    
    def generate_cell_one(e1, e2, e3, e4):
        result = []
        edges = [e1, e2, e3, e4]
        #At leaast one is true
        result.append([e1, e2, e3, e4, 0])
        
        #At most one is true
        for i in range(4):
            for j in range(i + 1, 4):
                result.append([-edges[i], -edges[j], 0])

        return result

    def generate_cell_two(e1, e2, e3, e4):
        result = []

        #At least two are true
        result.append([e1,e2,e3,e4,0])
        for i in range(4):
            clause = [e1, e2, e3, e4, 0]
            clause[i] = -clause[i]
            result.append(clause)
        #At most two are true
        result.append([-e1, -e2, -e3, 0])
        result.append([-e1, -e2, -e4, 0])
        result.append([-e1, -e3, -e4, 0])
        result.append([-e2, -e3, -e4, 0])
        
        return result

    def generate_cell_three(e1, e2, e3, e4):
        result = []
        edges = [e1,e2,e3,e4]
        
        #At least one is false
        result.append([-e1,-e2,-e3,-e4,0])

        #At most one is false
        for i in range(4):
            for j in range(i + 1, 4):
                result.append([edges[i], edges[j], 0])

        return result


        
    # generate cell constraints from input
    for y in range(GRID_HEIGTH):
        for x in range(GRID_LENGTH):
            cell_constraint = instance[y][x]
            combinations = [[]]
            if cell_constraint == 0:
                combinations = [[-edge_ID(x,y,"H"), 0], [-edge_ID(x,y,"V"), 0], [-edge_ID(x,y+1,"H"), 0], [-edge_ID(x+1,y,"V"), 0]]
            elif cell_constraint == 1:
                combinations = generate_cell_one(edge_ID(x,y,"H"), edge_ID(x,y,"V"), edge_ID(x,y+1,"H"), edge_ID(x+1,y,"V"))
            elif cell_constraint == 2:
                combinations = generate_cell_two(edge_ID(x,y,"H"), edge_ID(x,y,"V"), edge_ID(x,y+1,"H"), edge_ID(x+1,y,"V"))
            elif cell_constraint == 3:
                combinations = generate_cell_three(edge_ID(x,y,"H"), edge_ID(x,y,"V"), edge_ID(x,y+1,"H"), edge_ID(x+1,y,"V"))

            if len(combinations[0]) != 0:
                for combination in combinations:
                    cnf.append(combination)


    def add_loop_constraints(x,y,orientation):
        
        edge = edge_ID(x,y,orientation)

        a1, a2, a3, b1, b2, b3 = [0] * 6

        if orientation == "V":
            #Top neighbour
            if is_within_range(x, y, "H"):
                a1 = edge_ID(x, y, "H")
            if is_within_range(x, y-1, "V"):
                a2 = edge_ID(x, y-1, "V")
            if is_within_range(x-1, y, "H"):
                a3 = edge_ID(x-1, y, "H")

            #Bottom neighbours
            if is_within_range(x, y + 1, "H"):
                b1 = edge_ID(x, y + 1, "H")
            if is_within_range(x, y + 1, "V"):
                b2 = edge_ID(x, y + 1, "V")
            if is_within_range(x - 1, y + 1, "H"):
                b3 = edge_ID(x - 1, y + 1, "H")        

        elif orientation == "H":
            # Left neighbors
            if is_within_range(x, y,"V"):
                a1 = edge_ID(x, y, "V")
            if is_within_range(x - 1, y, "H"):
                a2 = edge_ID(x - 1, y, "H")
            if is_within_range(x, y - 1, "V"):
                a3 = edge_ID(x, y - 1, "V")

            # Right neighbors
            if is_within_range(x + 1, y - 1, "V"):
                b1 = edge_ID(x + 1, y - 1, "V")
            if is_within_range(x + 1, y, "H"):
                b2 = edge_ID(x + 1, y, "H")
            if is_within_range(x + 1, y, "V"):
                b3 = edge_ID(x + 1, y, "V")

        #For an edge to be true, exactly one neighbour from side a and 
        #exactly one neighbour from side b bust be true
        clauses = []
        
        def generate_neigbour_clauses(e, n1, n2, n3):
            result_clauses = []
            # Filter out undefined edges (neighbors represented as 0)
            neighbors = [n for n in [n1, n2, n3] if n != 0]

            # At least one neighbor is true if the edge is active
            result_clauses.append([-e] + neighbors)

            # At most one neighbor is true if the edge is active
            for i in range(len(neighbors)):
                for j in range(i + 1, len(neighbors)):
                    result_clauses.append([-e, -neighbors[i], -neighbors[j]])

            cnf_form = []
            for row in result_clauses:
                cnf_form.append(row + [0])
            
            return cnf_form

        for clause in generate_neigbour_clauses(edge, a1, a2, a3):
            clauses.append(clause)
        
        for clause in generate_neigbour_clauses(edge, b1, b2, b3):
            clauses.append(clause)
        
                       
        return clauses

    #generate simple loop constraint - every edge has either 1 neighbour on each side and is true
    #or is false
    for y in range(GRID_HEIGTH + 1):
        for x in range(GRID_LENGTH + 1):
            if x < GRID_LENGTH:
                for clause in add_loop_constraints(x,y,"H"):
                    cnf.append(clause)
            if y < GRID_HEIGTH:
                for clause in add_loop_constraints(x,y,"V"):
                    cnf.append(clause)

    return cnf, variable_count

def is_within_range(x, y, orientation):
    if (x < 0) or (y < 0):
        return False
    if orientation == "H":
        return (1 <= edge_ID(x,y,orientation) <= GRID_LENGTH * (GRID_HEIGTH + 1))
    if orientation == "V":
        return ((GRID_LENGTH * (GRID_HEIGTH + 1) + 1) <= edge_ID(x,y,orientation) < ID_OFFSET)
    
def edge_ID(x, y, orientation):
    if orientation == "H":
        return x * (GRID_HEIGTH + 1) + y + 1
    elif orientation == "V":
        offset = GRID_LENGTH * (GRID_HEIGTH + 1)
        return offset + x + (y * (GRID_LENGTH + 1)) + 1
    return 

def call_solver(cnf, nr_vars, output_name, solver_name, verbosity):
    # print CNF into formula.cnf in DIMACS format
    with open(output_name, "w") as file:
        # for row in cnf:
        #     print(row)
        file.write("p cnf " + str(nr_vars) + " " + str(len(cnf)) + '\n')
        for clause in cnf:
            file.write(' '.join(str(lit) for lit in clause) + '\n')

    # call the solver and return the output
    return subprocess.run(['./' + solver_name, '-model', '-verb=' + str(verbosity) , output_name], stdout=subprocess.PIPE)

def print_result(result):
    for line in result.stdout.decode('utf-8').split('\n'):
        print(line)     # print the whole output of the SAT solver to stdout, so you can see the raw output for yourself

    # check the returned result
    if (result.returncode == 20):   # returncode for SAT is 10, for UNSAT is 20
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
    
    true_edge = 0
    for element in model:
        if element > 0:
            true_edge = element
            break
    if true_edge == 0:
        print("Loop Not Possible")
    vertical_index = GRID_LENGTH * (GRID_HEIGTH + 1)
    horizontal_index = 0
    offset = GRID_LENGTH * (GRID_HEIGTH + 1)
    
    grid = [['' for _ in range(GRID_LENGTH + 1)] for _ in range(GRID_LENGTH + GRID_HEIGTH + 1)]

    for row_index in range(GRID_LENGTH + GRID_HEIGTH + 1):
        if row_index % 2 == 0:
            horizontal_index = row_index // 2
            for i in range(GRID_LENGTH):
                if model[horizontal_index] > 0:
                    grid[row_index][i+1] = "-----"
                else:
                    grid[row_index][i+1] = "     "
                horizontal_index += GRID_HEIGTH + 1
        else:
            for j in range(GRID_LENGTH + 1):
                if model[vertical_index] > 0:
                    grid[row_index][j] = "|    "
                else:
                    grid[row_index][j] = "     "
                vertical_index += 1
        

    for i, row in enumerate(grid, 1):
        # Join the row contents into a single line string
        row_str = ' '.join(map(str, row))
        
        # If the row index is odd (1-based), print it three times
        if i % 2 == 0:
            print(row_str)
            print(row_str)
            print(row_str)
        else:
            print(row_str)

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
