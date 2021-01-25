from .algorithm1 import Algorithm
from .cp_ortools import CPModel1
from .loop_solver import Loop_solver
from .brute_solver import Brute_solver

solvers = \
    dict(default=Algorithm,
         ortools=CPModel1,
         loop_EF_JS=Loop_solver,
         brute_EF_JS=Brute_solver)

# factory of solvers
def get_solver(name='default'):
    return solvers.get(name)
