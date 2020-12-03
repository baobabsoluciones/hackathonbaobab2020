from core import Instance
from example.algorithm1 import Algorithm
from solvers.modelo_entero_inicializacion_algoritmo import Model


def solve_example_problem_json(dataset, instance_name, solver=''):
    directory = '../data/'
    path = '{}{}/{}.mm'.format(directory, dataset, instance_name)
    instance = Instance.from_mm(path)
    print(instance.__dict__)
    exp = Model(instance=instance, algorithm=Algorithm(instance=instance))
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
    dataset = 'c15.mm'
    instance_name = 'c1564_9'

    # solve_example_problem_json(dataset, instance_name, solver='')
    exp = solve_example_problem_json(dataset, instance_name, solver='ORTOOLS')
    exp.graph()

