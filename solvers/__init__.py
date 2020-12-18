from .algorithm1 import Algorithm
from .cp_ortools import CPModel1

solvers = \
    dict(default=Algorithm,
         ortools=CPModel1)

# factory of solvers
def get_solver(name='default'):
    return solvers.get(name)
