from core import Instance, Experiment
from example.algorithm1 import Algorithm
from solvers.cp_ortools import CPModel1
import os


def solve_example_problem_json(dataset, instance_name, solver=''):
    directory = 'data/'
    path = '{}{}/{}.mm'.format(directory, dataset, instance_name)
    instance = Instance.from_mm(path)
    if solver=='ORTOOLS':
        exp = CPModel1(instance=instance)
    else:
        exp = Algorithm(instance=instance)
    exp.solve({})
    print("Errors:")
    print(exp.check_solution())
    print("Objective function:")
    print(exp.get_objective())
    # path_solution = '{}solutions/{}/{}'.format(directory, dataset, instance_name)
    # if not os.path.exists(path_solution):
    #     os.mkdir(path_solution)
    # path_in = '{}/input.json'.format(path_solution)
    # path_out = '{}/output.json'.format(path_solution)
    # exp.instance.to_json(path_in)
    # exp.solution.to_json(path_out)
    # exp.instance.from_json(path_in)
    # exp.solution.from_json(path_out)


if __name__ == '__main__':
    # dataset = 'j30.mm'
    # instance_name = 'j3064_10'
    # dataset = 'r5.mm'
    # instance_name = 'r564_10'
    dataset = 'm5.mm'
    instance_name = 'm564_10'

    solve_example_problem_json(dataset, instance_name, solver='')
    solve_example_problem_json(dataset, instance_name, solver='ORTOOLS')
