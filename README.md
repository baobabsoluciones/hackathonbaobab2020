# hackathonbaobab2020

## Installation

```
cd hackathonbaobab2020
python -m venv venv
venv/Scripts/activate
pip install -r requirements.txt
```

## Usage

The command line use is still Work in Progress.

```
cd hackathonbaobab2020
venv/Scripts/activate
python main.py -ARGUMENTS
```

## Code

We use the following objects:

1. `Instance` to represent input data.
2. `Solution` to represent a solution.
3. `Experiment` to represent input data+solution.
4. `Algorithm(Experiment)` to represent a solution approach.

There are helper functions to read and write an instance and a solution.

An example of how to use the existing code is available in `example/test_script.py`.

