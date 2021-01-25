import sys, os
prev_dir = os.path.join(sys.path[0], '..')
sys.path.insert(1, prev_dir)
import unittest
import hackathonbaobab2020.execution.run_batch as run
from hackathonbaobab2020 import core as exp, solvers as pkg_solvers
import shutil


class TestLoaderWithKwargs(unittest.TestLoader):
    """A test loader which allows to parse keyword arguments to the
       test case class."""
    def loadTestsFromTestCase(self, testCaseClass, **kwargs):
        """Return a suite of all tests cases contained in
           testCaseClass."""
        if issubclass(testCaseClass, unittest.suite.TestSuite):
            raise TypeError("Test cases should not be derived from " +
                            "TestSuite. Maybe you meant to derive from" +
                            " TestCase?")
        testCaseNames = self.getTestCaseNames(testCaseClass)
        if not testCaseNames and hasattr(testCaseClass, 'runTest'):
            testCaseNames = ['runTest']

        # Modification here: parse keyword arguments to testCaseClass.
        test_cases = []
        for test_case_name in testCaseNames:
            test_cases.append(testCaseClass(test_case_name, **kwargs))
        loaded_suite = self.suiteClass(test_cases)

        return loaded_suite


class HackathonTests(unittest.TestCase):

    def __init__(self, testName, solver, *args, **kwargs):
        unittest.TestCase.__init__(self, testName)
        self.solver = solver
        self.path_out = 'data/' + self.solver + '/'

    def tearDown(self):
        shutil.rmtree(self.path_out)

    def run_scenario_instance(self, scenario, instance):
        try:
            run.solve_zip(
                zip_name='./{}.zip'.format(scenario),
                path_out=self.path_out,
                path_in='tests/',
                solver_name=self.solver,
                test=False,
                instances=[instance],
                options=dict(timeLimit=120, gapRel=1)
            )

            experiment = exp.Experiment.from_json(self.path_out + scenario + '/' + instance)
            return experiment.check_solution()
        except Exception as e:
            raise TestFail("Test failed for solver {}: {}".format(
                self.solver, e
            ))

    # def test_j10(self):
    #     return self.run_scenario_instance('j10.mm', 'j102_2.mm')

    def test_j10_2(self):
        return self.run_scenario_instance('j10.mm', 'j102_4.mm')

    def test_j10_3(self):
        return self.run_scenario_instance('j10.mm', 'j102_5.mm')

    def test_j10_4(self):
        return self.run_scenario_instance('j10.mm', 'j102_6.mm')

    # def test_c15(self):
    #     return self.run_scenario_instance('c15.mm', 'c154_3.mm')

    # def test_c15_3(self):
    #     return self.run_scenario_instance('c15.mm', 'c158_3.mm')
    #
    # def test_c15_2(self):
    #     return self.run_scenario_instance('c15.mm', 'c158_4.mm')


def testAll():
    runner = unittest.TextTestRunner()
    suite_all = suite()
    # we run all tests at the same time
    ret = runner.run(suite_all)
    if not ret.wasSuccessful():
        raise RuntimeError("Tests were not passed")


def suite():
    solvers = pkg_solvers.solvers.keys()
    loader = TestLoaderWithKwargs()
    suite = unittest.TestSuite()
    for solver in solvers:
        print("Testing solver {}".format(solver))
        tests = loader.loadTestsFromTestCase(HackathonTests, solver=solver)
        suite.addTests(tests)
    return suite


class TestFail(Exception):
    pass

if __name__ == '__main__':
    # Tests
    testAll()

