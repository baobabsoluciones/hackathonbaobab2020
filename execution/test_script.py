from core import Instance
from solvers import get_solver


def solve_example_problem_json(dataset, instance_name, solver_name='default'):
    directory = 'data/'
    path = '{}{}/{}.mm'.format(directory, dataset, instance_name)
    instance = Instance.from_mm(path)
    solver = get_solver(solver_name)
    exp = solver(instance=instance)
    exp.solve({})
    print("Errors:")
    print(exp.check_solution())
    print("Objective function:")
    print(exp.get_objective())
    return exp


if __name__ == '__main__':
    # dataset = 'j30.mm'
    # instance_name = 'j3064_10'
    # dataset = 'r5.mm'
    # instance_name = 'r564_10'
    dataset = 'm5.mm'
    instance_name = 'm564_10'

    # solve_example_problem_json(dataset, instance_name, solver='')
    exp = solve_example_problem_json(dataset, instance_name, solver_name='ortools')
    exp.graph()

