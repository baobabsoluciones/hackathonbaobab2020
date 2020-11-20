from core import Instance, Experiment
from example.algorithm1 import Algorithm


def solve_example_problem_json():
    directory = 'data/'
    path = '{}c15.mm/c1564_9.mm'.format(directory)
    instance = Instance.from_mm(path)
    exp = Algorithm(instance=instance)
    exp.solve({})
    print(exp.check_solution())
    path_sol = '{}solutions/c15.mm/c1564_9/output.json'.format(directory)
    path_inst = '{}solutions/c15.mm/c1564_9/input.json'.format(directory)
    exp.solution.to_json(path_sol)
    exp.instance.to_json(path_inst)
    exp.instance.from_json(path_inst)
    exp.solution.from_json(path_sol)


if __name__ == '__main__':
    solve_example_problem_json()
