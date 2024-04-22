from typing import Dict
from .core import Instance, Experiment, Solution, Batch, ZipBatch
from .execution import *
from .solver import (
    solvers,
    get_solver,
    Brute_solver,
    Loop_solver,
    Fix_loop_solver,
    Milp1,
    CPModel1,
    Algorithm,
    Iterator1,
)
from .tests import get_test_instance
from cornflow_client import ApplicationCore, get_empty_schema


class HackathonApp(ApplicationCore):
    name = "hk_2020_dag"
    instance = Instance
    solution = Solution
    solvers = solvers
    schema = get_empty_schema(
        properties=dict(
            timeLimit=dict(type="number"),
            gapAbs=dict(type="number"),
            gapRel=dict(type="number"),
        ),
        solvers=list(solvers.keys()),
    )

    @property
    def test_cases(self) -> List[Dict]:
        return [
            {
                "name": "J102_4",
                "instance": get_test_instance("j10.mm.zip", "j102_4.mm").to_dict(),
                "description": "Test instance with 12 jobs and 4 resources and up to 3 modes per job.",
            },
            {
                "name": "J102_5",
                "instance": get_test_instance("j10.mm.zip", "j102_5.mm").to_dict(),
                "description": "Test instance with 12 jobs, 4 resources and up to 3 modes per job.",
            },
            {
                "name": "J102_6",
                "instance": get_test_instance("j10.mm.zip", "j102_6.mm").to_dict(),
                "description": "Test instance with 12 jobs, 4 resources and up to 3 modes per job.",
            },
        ]
