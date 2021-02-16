import warnings
from .algorithm1 import Algorithm

try:
    from .cp_ortools import CPModel1
    from .Milp1 import Milp1
    from .Iterator1 import Iterator1
    from .loop_solver import Loop_solver
    from .brute_solver import Brute_solver
    from .fix_loop_solver import Fix_loop_solver
except ImportError:
    solvers = \
        dict(default=Algorithm,
             )
    warnings.warn(
        "Only solver='default' is available. \n" +
        "To install dependencies for the other solvers: \n" +
        "`pip install hackathonbaobab2020[solvers]`")
else:
    solvers = \
        dict(default=Algorithm,
             Milp_LP_HL=Milp1,
             ortools=CPModel1,
             Iterator_HL=Iterator1,
             loop_EJ=Loop_solver,
             brute_EJ=Brute_solver,
             fix_loop_EF_JS=Fix_loop_solver
             )


# factory of solvers
def get_solver(name='default'):
    return solvers.get(name)
