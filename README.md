# Documentation

## Problem description

Slither Link is a Japanese logic puzzle. It is played on a board that consists of dots arranged into squares. The goal of the game is to connect adjacent dots in a such a way
that they form a singular loop with no loose ends. Inside each square there can be a number from 0 to 3 indicating
how many of the square's sides need to be included in the final loop.

## Encoding

### Variables

To encode this problem we will be using a single variable:

$Edge(x,y,orientation)$ is a boolean that indicates whether an edge is present in the loop
We need to specify whether an edge is vertical or horizontal otherwise we wouldn't be able to index them

This variable is crucial to determine which route our loop is taking - what edges are a part of it
Loading cell values (number constraints) from the input will determine which permutations of edges are valid
For example if a cell has the value 3 there are 4 combinations of edges with (3 true, 1 false) which are valid

### Constraints

Every vertex must have either 2 or no edges going through it - in any different case the loop would not adhere to the rules
We can apply this rule on our variable by saying that every true edge must have 2 adjacent true edges

#### Cell number constraint

If the cell has the value 1, exactly one edge is true:

1. At least one edge is true:

   $$
   e_1 \lor e_2 \lor e_3 \lor e_4
   $$

2. At most one edge is true:

   for each pair:

   $$
   \neg e_i \lor \neg e_j
   $$

If the cell has the value 3, the clauses are just mirrored (exactly one is false)

Finally, if the cell value is 2, exactly 2 edges are true which can be described as: At least two are true and At most two are true

#### Basic loop constraint

Every vertex must have either 2 or no edges going through it - in any different case the loop would not adhere to the rules
We can apply this rule on our variable by saying that every true edge must have 2 ad

1. At least one neighbor from each side is true if the original edge is true

2. At most one neighbor from each side is true if the original edge is true

The following formula is applied to both ends of the edge:

$$
\bigwedge_{1 \leq i \leq 3} \left( \neg e \lor n_1 \lor n_2 \lor n_3 \right)
\quad \bigwedge_{1 \leq i < j \leq 3} \left( \neg e \lor \neg n_i \lor \neg n_j \right)
$$

Some of the adjacent edges can be non-existent, in that case they are removed from the list of neigbors before the generation of clauses

## User documentation

Basic usage:

```
sliding_puzzle.py [-h] [-i INPUT] [-o OUTPUT] [-s SOLVER] [-v {0,1}]
```

Command-line options:

- `-h`, `--help` : Show a help message and exit.
- `-i INPUT`, `--input INPUT` : The instance file. Default: "input.in".
- `-o OUTPUT`, `--output OUTPUT` : Output file for the DIMACS format (i.e. the CNF formula).
- `-s SOLVER`, `--solver SOLVER` : The SAT solver to be used.
- `-v {0,1}`, `--verb {0,1}` : Verbosity of the SAT solver used.

## Example instances

- `input-2by2.in`: A 2x2 instance solvable in two steps.
- `input-2by2-unsat.in`: An unsolvable 2x2 instance.
- `input-3by3-unsat.in`: An unsolvable 3x3 instance (5 steps, the instance is solvable in 6 steps)
- `input-3by3.in`: An easy, solvable 3x3 instance
- `input-4by4.in`: An easy, solvable 3x3 instance
- `input-4by4-hard.in`: A solvable instance that takes approximately 18s to solve on our machine

## Experiments

Experiments were run on Intel Core i5-1035G1i5 CPU (1.0 GHz) and 8 GB RAM on Ubuntu inside WSL2 (Windows 11). Time was measured with `hyperfine`.

We focus on the puzzle from input-4by4-hard.in, and modulate the number of steps. The setup is far from ideal, and to get reproducible results we would need to test many different instances, so consider this only a toy experiment.

| _max steps_ | _time (s)_ | _solvable?_ |
| ----------: | :--------- | :---------: |
|           3 | 0.08       |      N      |
|           6 | 0.12       |      N      |
|           9 | 0.25       |      N      |
|          12 | 0.38       |      N      |
|          15 | 0.49       |      N      |
|          18 | 0.64       |      N      |
|          21 | 0.9        |      N      |
|          24 | 1.5        |      N      |
|          27 | 2.9        |      N      |
|          30 | 9          |      N      |
|          33 | 18         |      Y      |
|          36 | 20         |      Y      |
|          39 | 24         |      Y      |
|          42 | 43         |      Y      |

![A plot of the results](plot.jpg)

Looking at the data, we can make a guess that time grows exponentially with respect to the number of steps. Moreover, note that finding a solution is generally faster than showing that no solution exists. (The optimal number of steps for the puzzle above is 33.) Feel free to conduct more comprehensive expriments in your projects!
