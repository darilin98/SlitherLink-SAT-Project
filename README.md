# Example homework solution 

This is an example solution to homework for Propositional and Predicate Logic (NAIL062). The provided Python code encodes, solves, and decodes the sliding tile puzzle via reduction to SAT (i.e. propositional logic formula).

The SAT solver used is [Glucose](https://www.labri.fr/perso/lsimon/research/glucose/), more specifically [Glucose 4.2.1](https://github.com/audemard/glucose/releases/tag/4.2.1). The source code is compiled using

```
cmake .
make
```

This example contains a compiled UNIX binary of the Glucose solver. For optimal experience, we encourage the user to compile the SAT solver themselves. Note that the solver, as well as the Python script, are assumed to work on UNIX-based systems. In case you prefer using Windows, we recommend to use WSL.

Note that the provided encoding for the sliding tile puzzle is not the only existing encoding. Usually, there are several equivalent encodings one might use. Choosing the encoding is up to the user based on experience and experiments.

Also note, that the puzzle is an optimization problem (i.e. try to solve it in as few steps as possible), however, SAT is a decision problem, therefore, we transfer the puzzle into a decision problem for a specific number of moves (i.e. is there a solution with this many moves?). To find the minimum number of moves, one has to solve a sequence of decision problems with a different number of moves allowed.

The following documentation is an acceptable solution format that should accompany your code.

# Documentation

## Problem description

The sliding tile puzzle challenges the player to reorganize tiles in a grid in such a way that they match predetermined positions. Specifically, in an $n \times n$ grid there are $n^2 - 1$ tiles. At each timestep, one tile may be moved orthogonally into the singular empty position. It is known that not all starting positions are solvable and for the $4 \times 4$ variant of the puzzle (sometimes called the 15 puzzle), the hardest position takes at most 80 moves. More information about the puzzle may be found [online](https://en.wikipedia.org/wiki/Sliding_puzzle).

An example of a valid input format is:

```
4
3
1 4 2
3 5 0
6 7 8
```

where the first line is the number of timesteps to be tested. Second line is the size of the grid.
Lastly, the starting positions of the tiles in the grid are present. Tile 0 is the empty place.

The target position increases from left to right, from top to bottom. For a grid of $3 \times 3$ the target position is:

```
0 1 2 
3 4 5 
6 7 8 
```

## Encoding

The problem is encoded using two sets of variables. Variables $At(n,p,t)$ represent that tile number $n$ is located in position $p$ at timestep $t$. Variables $Swap((p_1,p_2),t)$ represent that any tile located at position $p_1$ swaps places with any tile located at position $p_2$ at timestep $t$. Note that this variable does not tell us which tile is located at $p_1$ or $p_2$. We create $Swap$ variables only for adjacent places, therefore $(p_1,p_2)$ may be treated as an edge $e$. To simplify the following notation, we will sometimes use $e$ instead of $(p_1,p_2)$.

To represent the decision problem if there is a solution to the sliding tile puzzle in MAKESPAN number of moves, we use the following constraints:

- The initial position of the tiles

    $At(n,start(n),0)$ for each $n$, where $start(n)$ is the starting position of tile $n$.

- The target position of the tiles

    $At(n,n,MAKESPAN)$ for each $n$.

- No two tiles are at the same place at the same time

    $\bigwedge_{n_1 < n_2} \neg At(n_1,p,t) \vee \neg At(n_2,p,t)$ for each $p$ and $t$

- A tile can not be at two places at the same time

    $\bigwedge_{p_1 < p_2} \neg At(n,p_1,t) \vee \neg At(n,p_2,t)$ for each $n$ and $t$

- There is at most one switch at any timestep

    $\bigwedge_{e_1 < e_2} \neg Swap(e_1,t) \vee \neg Swap(e_2,t)$ for $t$ and any ordering of edges.

- If the tiles are switching, one of them has to be tile $0$

    $Swap((p_1,p_2), t) \implies (At(0,p_1,t) \vee At(0,p_2,t))$ for each $(p_1,p_2)$ and $t$

- If a tile is switching from $p_1$ to $p_2$ and tile $n$ is in $p_1$, it will be in $p_2$ in the next timestep and symmetrically for $p_2$

    $(Swap((p_1,p_2), t) \wedge At(n,p_1,t)) \implies At(n,p_2,t+1)$ for each $n$, $(p_1,p_2)$, and $t \setminus MAKESPAN$

    $(Swap((p_1,p_2), t) \wedge At(n,p_2,t)) \implies At(n,p_1,t+1)$ for each $n$, $(p_1,p_2)$, and $t \setminus MAKESPAN$

- If there is no swap from a position, the tile in that position remains there

    $(\bigwedge_{e \in N(p)} \neg Switch(e,t) \wedge At(n,p,t)) \implies At(n,p,t+1)$ for each $n$, $p$, and $t \setminus MAKESPAN$, where $N(p)$ are neighbors of position $p$.

## User documentation


Basic usage: 
```
sliding_puzzle.py [-h] [-i INPUT] [-o OUTPUT] [-s SOLVER] [-v {0,1}]
```

Command-line options:

* `-h`, `--help` : Show a help message and exit.
* `-i INPUT`, `--input INPUT` : The instance file. Default: "input.in".
* `-o OUTPUT`, `--output OUTPUT` : Output file for the DIMACS format (i.e. the CNF formula).
* `-s SOLVER`, `--solver SOLVER` : The SAT solver to be used.
*  `-v {0,1}`, `--verb {0,1}` :  Verbosity of the SAT solver used.

## Example instances

* `input-2by2.in`: A 2x2 instance solvable in two steps.
* `input-2by2-unsat.in`: An unsolvable 2x2 instance.
* `input-3by3-unsat.in`: An unsolvable 3x3 instance (5 steps, the instance is solvable in 6 steps)
* `input-3by3.in`: An easy, solvable 3x3 instance
* `input-4by4.in`: An easy, solvable 3x3 instance
* `input-4by4-hard.in`: A solvable instance that takes approximately 18s to solve on our machine

## Experiments

Experiments were run on Intel Core i5-1035G1i5 CPU (1.0 GHz) and 8 GB RAM on Ubuntu inside WSL2 (Windows 11). Time was measured with `hyperfine`. 

We focus on the puzzle from input-4by4-hard.in, and modulate the number of steps. The setup is far from ideal, and to get reproducible results we would need to test many different instances, so consider this only a toy experiment.

| *max steps* | *time (s)* | *solvable?* |
|------------:|:-----------|:-----------:|
  3 | 0.08 | N
  6 | 0.12 | N
  9 | 0.25 | N
 12 | 0.38 | N
 15 | 0.49 | N
 18 | 0.64 | N
 21 | 0.9  | N
 24 | 1.5  | N
 27 | 2.9  | N
 30 | 9    | N
 33 | 18   | Y
 36 | 20   | Y
 39 | 24   | Y
 42 | 43   | Y


![A plot of the results](plot.jpg)

Looking at the data, we can make a guess that time grows exponentially with respect to the number of steps. Moreover, note that finding a solution is generally faster than showing that no solution exists. (The optimal number of steps for the puzzle above is 33.) Feel free to conduct more comprehensive expriments in your projects!
