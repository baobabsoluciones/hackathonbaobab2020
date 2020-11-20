# hackathonbaobab2020

The problem consists of scheduling all jobs by deciding when and in which mode the job is executed.
There are two types of resources: (R) renewables have an availability that is recovered each period of time, (N) non-renewables have an availability for the whole planning horizon.
The objective is to reduce the finishing time (start time + duration) of the last job.

The instances for the problem are found here:

http://www.om-db.wi.tum.de/psplib/getdata_mm.html

On the `data` directory of this repository we have copied the smallest instances.
For the format of the solution, since there is no example that we know of, we'll be using the one in `data/solutions/c15mm/c1564_9.output.json`

Below are the instructions to use the helper functions and checker (they are optional).
To understand the format of the input data file, you can check how we parse it in python in the function `Instance.from_mm(path)` in the file`core/instance.py`

## Installation

python>=3.5 is needed. I'm assuming a windows installation.

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

We use the following helper objects:

1. `Instance` to represent input data.
2. `Solution` to represent a solution.
3. `Experiment` to represent input data+solution.
4. `Algorithm(Experiment)` to represent a resolution approach.

The last one (4) includes an example of a solution approach. It schedules one job at a time while respecting the sequence. Apparently, it passes the tests.

There are helper functions to read and write an instance and a solution to/from a file.

An small example of how to use the existing code is available in `example/test_script.py`.

