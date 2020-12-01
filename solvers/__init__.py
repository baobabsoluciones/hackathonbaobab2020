# factory of solvers
from .algorithm1 import Algorithm

def get_solver(name=None):
    if name == 'default':
        return Algorithm
    return None
