from .algorithm1 import Algorithm
from .cp_ortools import CPModel1
from .Milp1 import Milp1

solvers = \
    dict(default=Algorithm,
		Milp_LP_HL = Milp1,
         ortools=CPModel1)

# factory of solvers
def get_solver(name='default'):
    return solvers.get(name)
