from .algorithm1 import Algorithm
from .cp_ortools import CPModel1
from .loop_solver import Loop_solver

solvers = \
    dict(default=Algorithm,
         ortools=CPModel1,
         solver_EJ=Loop_solver)

# factory of solvers
def get_solver(name='default'):
    return solvers.get(name)
