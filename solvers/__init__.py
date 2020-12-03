from .algorithm1 import Algorithm
from .cp_ortools import CPModel1


# factory of solvers
def get_solver(name=None):
    if name == 'default':
        return Algorithm
    if name == 'ortools':
        return CPModel1
    return None
