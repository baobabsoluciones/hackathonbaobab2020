from core import Instance, Experiment
from solve.algorithm import Algorithm
import os


def solve_example_problem_json():
    directory = 'data/'
    instance_name = 'c1564_3'
    path = '{}c15.mm/{}.mm'.format(directory, instance_name)
    instance = Instance.from_mm(path)
    exp = Algorithm(instance=instance)
    exp.solve({})
    path_solution = '{}solutions/c15.mm/{}'.format(directory, instance_name)
    if not os.path.exists(path_solution):
        os.mkdir(path_solution)
    path_in = '{}/input.json'.format(path_solution)
    path_out = '{}/output.json'.format(path_solution)
    exp.instance.to_json(path_in)
    exp.solution.to_json(path_out)
    exp.instance.from_json(path_in)
    print(exp.instance.from_json(path_in))
    exp.solution.from_json(path_out)


if __name__ == '__main__':
    solve_example_problem_json()
