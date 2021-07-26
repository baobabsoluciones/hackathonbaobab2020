import sys, os

prev_dir = os.path.join(os.path.dirname(__file__), "..", "..")
print(prev_dir)
sys.path.insert(1, prev_dir)
import unittest
import shutil
from hackathonbaobab2020 import solve_zip, Experiment

# from hackathonbaobab2020 import solver as pkg_solvers
# list(pkg_solvers.solvers.values())[0]


class BaseSolverTest:
    class HackathonTests(unittest.TestCase):
        solver = None

        def setUp(self):
            self.path_out = "data/" + self.solver + "/"

        def tearDown(self):
            shutil.rmtree(self.path_out)

        def run_scenario_instance(self, scenario, instance):
            path_in = os.path.dirname(__file__)
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

        # def test_c15(self):
        #     return self.run_scenario_instance('c15.mm', 'c154_3.mm')

        # def test_c15_3(self):
        #     return self.run_scenario_instance('c15.mm', 'c158_3.mm')
        #
        # def test_c15_2(self):
        #     return self.run_scenario_instance('c15.mm', 'c158_4.mm')


class TestAlgorithm(BaseSolverTest.HackathonTests):
    solver = "default"


class TestMilp1(BaseSolverTest.HackathonTests):
    solver = "Milp_LP_HL"


class TestCPModel1(BaseSolverTest.HackathonTests):
    solver = "ortools"


class TestIterator1(BaseSolverTest.HackathonTests):
    solver = "Iterator_HL"


class TestLoop_solver(BaseSolverTest.HackathonTests):
    solver = "loop_EJ"


if __name__ == "__main__":

    unittest.main()
