# hackathon baobab 2020

The problem consists of scheduling all jobs by deciding when and in which mode the job is executed.
There are two types of resources: renewable resources (R) are consumed *each period* and have an availability that is recovered each period of time; non-renewable resources (N) are consumed *once per job* and have an availability for the whole planning horizon.
The objective is to reduce the finishing time (start time + duration) of the last job.

The instances for the problem are found here:

http://www.om-db.wi.tum.de/psplib/getdata_mm.html

On the `data` directory of this repository we have copied the smallest instances.
For the format of the solution, since there is no example that we know of, we'll be using the one in `data/solutions/c15mm/c1564_9.output.json`

Below are the instructions to use the helper functions and checker (they are optional).
To understand the format of the input data file, you can check how we parse it in python in the function `Instance.from_mm(path)` in the file`core/instance.py`

## Installation

python>=3.5 is needed. I'm assuming a Windows installation.

```
cd hackathonbaobab2020
python -m venv venv
venv/Scripts/activate
pip install -r requirements.txt
```

## How to add a new solver

These are the steps to add a solver and make it compatible with the command line and the python functions:

1. Add a file inside the `solvers` directory with a subclass of `core.experiment.Experiment` that implements, at least, the `solve()` method *with the same argument names*.
1. Your `solve` method needs to return an integer with the status of the solving process. Current values are `{4: "Optimal", 2: "Feasible", 3: "Infeasible", 0: "Unknown"}`.
1. Your `solve` method also needs to store the best solution found in `self.solution`. It needs to be an instance of the `Solution` object.
1. Edit the `solvers/__init__.py` to import your solver and edit the `solvers` dictionary by giving your solver a name.
1. If the `requirements.txt` file is missing some package you need for your solver, add it at the bottom of the list.

**Additional considerations**:

1. One way to see if the solver is correctly integrated is to test solving with it via the command line (see below).
2. Everything that your solver needs should be inside the `solvers` directory (you can put more than one file). Do not edit the files outside the `solvers` directories with code from your solver!

## How to run tests

These tests are run also in github and test some small example problems with a `timelimit` of 120 s (check the `options` dictionary).
```
python tests/tests.py 
 ```

## Command line

The command line app has three main ways to use it.

### To execute instances

To get all possible commands just run:

    python main.py solve-scenarios --help

The following assumes you have downloaded the zip `j30.mm.zip` of input instances, and you have stored it in the `data` directory. It solves instance `j301_1.mm` with the solver that is in `solvers/algorithm1` named `default` in `solvers/__init__.py`.
    
    python main.py solve-scenarios --directory=data --scenario=j30.mm.zip --solver=default --instance=j3010_1.mm --no-test

You can also solve multiple scenarios or multiple instances by passing the `--instances` and `--scenarios` arguments. Just be careful with the string format:

    python main.py solve-scenarios --directory=data --scenarios='["c15.mm.zip", "c21.mm.zip", "j10.mm.zip", "j30.mm.zip", "m1.mm.zip", "m5.mm.zip", "n0.mm.zip", "n1.mm.zip", "n3.mm.zip", "r1.mm.zip", "r4.mm.zip", "r5.mm.zip"]' --solver=default

With the option argument, a json with the solving configuration is passed:

    python main.py solve-scenarios --directory=data --scenario=j30.mm.zip --solver=default --instance=j3010_1.mm --no-test --options='{"DEBUG": 1, "timeLimit": 120}'

Finally, if you pass the `zip` option you create a nice little zip at the end.

The output format is always the same:

    solver_name/scenario_name/instance_name/(input.json, output.json, options.json)

The `options.json` file contains some information from the solver such as the time it took to solve, the status (Optimal, Feasible, Infeasible, etc.), the name of the solver, etc.

### To get statistics from a solution

You first need to have a zip with the results you want to get statistics from. For this, the easiest is to pass the `zip` option to the `solve-scenarios` function above.

Then you do something like:

    python main.py export-table --path=data/default.zip --path_out=data_default.csv

This generates a table in a csv with several columns: scenario, name (instance), objective (function value), solver, (solving) time, (number of) errors (in the solution).

To easily read the contents you can do:

```python

import pandas as pd
df = pd.read_csv('data_default.csv')
print(df.head().to_markdown())

```

Which should print something like this:

|    | scenario   | name      |   objective | solver   |        time |   errors |
|---:|:-----------|:----------|------------:|:---------|------------:|---------:|
|  0 | n3.mm      | n311_1.mm |          44 | default  | 0.000282581 |        1 |
|  1 | n0.mm      | n013_7.mm |          35 | default  | 0.000227326 |        0 |
|  2 | r4.mm      | r452_6.mm |          46 | default  | 0.00025893  |        1 |
|  3 | n3.mm      | n343_4.mm |          37 | default  | 0.000268723 |        1 |
|  4 | n1.mm      | n121_4.mm |          55 | default  | 0.000254337 |        0 |


## Using python objects

We use the following helper objects:

1. `Instance` to represent input data.
2. `Solution` to represent a solution.
3. `Experiment` to represent input data+solution.
4. `Algorithm(Experiment)` to represent a resolution approach.

An example of the last one (4) is found in `solvers/algorithm1.py`. It schedules one job at a time while respecting the sequence. It passes all tests except the non-renewables, sometimes.

There are helper functions to read and write an instance and a solution to/from a file.

A small example of how to use the existing code is available in `execution/test_script.py`.
Below an example:

```python
from hackathonbaobab2020.core import Instance
from hackathonbaobab2020.solvers import get_solver

# get mm file
path = "data/c15.mm/c154_3.mm"
# initialize an instance object
instance = Instance.from_mm(path)
# get the default solver (in solvers/algorithm1.py)
solver = get_solver('default')
# initialize the solver with the instance
exp = solver(instance=instance)
# solve the instance using the solver
exp.solve({})
# The next functions do not depend on the solver and should not be overwritten:
# print the possible errors on the solution obtained from the solver
print(exp.check_solution())
# print the objective function of the solution
print(exp.get_objective())
# produce a gantt chart of the job's schedule, with a color per mode.
exp.graph()
```






