from core import Instance, Experiment
from example.algorithm1 import Algorithm
import click


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    directory = '/home/pchtsp/Documents/projects/hackathonbaobab2020/data'
    path = '{}/c15.mm/c1564_9.mm'.format(directory)
    instance = Instance.from_mm(path)
    exp = Algorithm(instance=instance)
    exp.solve({})
    path_sol = '{}/solutions/c15.mm/c1564_9/output.json'.format(directory)
    path_inst = '{}/solutions/c15.mm/c1564_9/input.json'.format(directory)
    exp.solution.to_json(path_sol)
    exp.instance.to_json(path_inst)
    exp.instance.from_json(path_inst)
    exp.check_solution()

#