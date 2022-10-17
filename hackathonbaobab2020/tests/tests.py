import sys, os

prev_dir = os.path.join(os.path.dirname(__file__), "..", "..")
print(prev_dir)
sys.path.insert(1, prev_dir)
import unittest
import shutil
from jsonschema import Draft7Validator
from hackathonbaobab2020 import solve_zip, Experiment, HackathonApp


class BaseSolverTest:
    class HackathonTests(unittest.TestCase):
        solver = None

        def setUp(self):
            test_dir = os.path.dirname(os.path.abspath(__file__))
            self.path_out = os.path.join(test_dir, "../../data/" + self.solver + "/")

        def tearDown(self):
            shutil.rmtree(self.path_out)

        def run_scenario_instance(self, scenario, instance):
            path_in = os.path.dirname(os.path.abspath(__file__))
            try:
                solve_zip(
                    zip_name="./{}.zip".format(scenario),
                    path_out=self.path_out,
                    path_in=path_in,
                    solver_name=self.solver,
                    test=False,
                    instances=[instance],
                    options=dict(timeLimit=300, gapRel=1),
                )
                experiment = Experiment.from_json(
                    self.path_out + scenario + "/" + instance
                )
                return experiment.check_solution()
            except Exception as e:
                raise TestFail("Test failed for solver {}: {}".format(self.solver, e))

        # def test_j10(self):
        #     return self.run_scenario_instance('j10.mm', 'j102_2.mm')

        def test_j10_2(self):
            return self.run_scenario_instance("j10.mm", "j102_4.mm")

        def test_j10_3(self):
            return self.run_scenario_instance("j10.mm", "j102_5.mm")

        def test_j10_4(self):
            return self.run_scenario_instance("j10.mm", "j102_6.mm")


class TestAlgorithm(BaseSolverTest.HackathonTests):
    solver = "default"


class TestMilp1(BaseSolverTest.HackathonTests):
    solver = "Milp_LP_HL"


class TestCPModel1(BaseSolverTest.HackathonTests):
    solver = "ortools"

    def test_c15(self):
        return self.run_scenario_instance("c15.mm", "c154_3.mm")

    def test_c15_3(self):
        return self.run_scenario_instance("c15.mm", "c158_3.mm")

    def test_c15_2(self):
        return self.run_scenario_instance("c15.mm", "c158_4.mm")


class TestIterator1(BaseSolverTest.HackathonTests):
    solver = "Iterator_HL"


class TestLoop_solver(BaseSolverTest.HackathonTests):
    solver = "loop_EJ"


class TestApp(unittest.TestCase):
    def test_app(self):
        app = HackathonApp()
        solvers = ["default", "ortools"]
        for solver in solvers:
            config = dict(solver=solver, timeLimit=30)
            for case in app.test_cases:
                sol, sol_checks, inst_checks, log_txt, log = app.solve(case, config)
                instance = app.instance.from_dict(case)
                solution = app.solution.from_dict(sol)
                experiment = Experiment(instance, solution)
                experiment.check_solution()
                validator = Draft7Validator(experiment.schema_checks)
                if not validator.is_valid(sol_checks):
                    raise TestFail("The solution checks have invalid format")


class TestFail(Exception):
    pass


if __name__ == "__main__":

    unittest.main()
