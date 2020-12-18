
from solvers.milp_LP_HL.model import get_model
from pyomo.environ import SolverFactory
from core import Experiment, Solution
from solvers.milp_LP_HL.pyomo_utils import is_feasible, get_status, var_to_dict
from solvers.milp_LP_HL.configuration import SOLVER_PARAMETERS, MAX_PERIOD
from solvers.milp_LP_HL.project_utils import reverse_dict, get_status_value


class Milp1(Experiment):
    """
    Milp model created with Pyomo.
    """

    def __init__(self, instance, solution=None):
        if solution is None:
            solution = {}
        super().__init__(instance, solution)
        return

    def get_input_data(self, max_period=MAX_PERIOD):
        """
        Prepair the data for the milp model.
        """
    
        data = self.instance.to_dict()
        print(data)
        self.input_data = {}
    
        jobs = list(set([j["id"] for j in data["jobs"]]))
        periods = [p for p in range(max_period)]
        resources = [r["id"] for r in data["resources"]]
        modes = list(set([d["mode"] for d in data["durations"]]))
        resources_needs = {(n["job"], n["resource"], n["mode"]): n["need"] for n in data["needs"]}
        jobs_precedence_1 = [(j["id"], j["successors"]) for j in data["jobs"]]
        jobs_precedence = sum([[(a, c) for c in b] for (a, b) in jobs_precedence_1], [])
    
        jobs_durations = {(d["job"], d["mode"]): d["duration"] for d in data["durations"]}
        total_resources = {r["id"]: r["available"] for r in data["resources"]}
    
        self.input_data["sJobs"] = {None: jobs}
        self.input_data["sPeriods"] = {None: periods}
        self.input_data["sRResources"] = {None: [r for r in resources if "R" in r]}
        self.input_data["sNResources"] = {None: [r for r in resources if "N" in r]}
        self.input_data["sResources"] = {None: resources}
        self.input_data["sModes"] = {None: modes}
        self.input_data["sJobsPrecedence"] = {None: jobs_precedence}
        self.input_data["sJobsModes"] = {None: [i for i in jobs_durations.keys()]}
        self.input_data["pResourcesUsed"] = resources_needs
        self.input_data["pDuration"] = jobs_durations
        self.input_data["pMaxResources"] = total_resources
        self.input_data["pWeightMakespan"] = {None: 1}
        self.input_data["pWeightResources"] = {None: 0}
    
        return {None: self.input_data}
    
    def solve(self, options):
        """
        Solve the problem.
        """
        model = get_model()
        data = self.get_input_data()
        print(data)
        model_instance = model.create_instance(data, report_timing=True)
        opt = SolverFactory('cbc')
        opt.options.update(SOLVER_PARAMETERS)
        result = opt.solve(model_instance, tee=True)
        
        self.status = get_status(result)
        self.model_solution = model_instance
        print(self.status)

        if is_feasible(self.status):
            self.print_instance()
            data = self.format_solution()
            self.solution = Solution(data)
        else:
            self.solution = Solution({})

        print(self.print_instance())
        
        return get_status_value(self.status)
    
    def print_instance(self):
        print("printing instance")
        with open("instance_display.txt", "w") as f:
            self.model_solution.display(ostream=f)
    
    def format_solution(self):
        
        instance = self.model_solution
        dict_start = var_to_dict(instance.vStart)
        dict_mode = var_to_dict(instance.v01Mode)
        set_jobs = [i for i in instance.sJobs]
        
        mode_no_denso = dict()
        for a, b in dict_mode.keys():
            if dict_mode[a, b] == 1:
                mode_no_denso.update({a: b})
        
        if len(mode_no_denso)==0:
            return {}
        
        final = dict()
        for j in set_jobs:
            final[j] = dict()
            final[j].update({'period': dict_start[j], 'mode': mode_no_denso[j]})
        return final
        