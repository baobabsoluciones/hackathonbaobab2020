
from hackathonbaobab2020.solvers.milp_LP_HL.model import get_model
from pyomo.environ import SolverFactory
from hackathonbaobab2020.core import Experiment, Solution
from hackathonbaobab2020.solvers.milp_LP_HL.pyomo_utils import is_feasible, get_status, var_to_dict
from hackathonbaobab2020.solvers.milp_LP_HL.configuration import SOLVER_PARAMETERS, MAX_PERIOD
from hackathonbaobab2020.solvers.milp_LP_HL.project_utils import reverse_dict, get_status_value

import pytups as pt


class Milp1(Experiment):
    """
    Milp model created with Pyomo.
    """

    def __init__(self, instance, solution=None):
        if solution is None:
            solution = Solution({})
        super().__init__(instance, solution)
        print("\nSolving with Milp1")

    def get_input_data(self, max_period=MAX_PERIOD):
        """
        Prepair the data for the milp model.
        """
    
        data = self.instance.to_dict()
        self.input_data = {}
    
        jobs = list(set([j["id"] for j in data["jobs"]]))
        
        resources = [r["id"] for r in data["resources"]]
        modes = list(set([d["mode"] for d in data["durations"]]))
        resources_needs = {(n["job"], n["resource"], n["mode"]): n["need"] for n in data["needs"]}
        jobs_precedence_1 = [(j["id"], j["successors"]) for j in data["jobs"]]
        jobs_precedence = sum([[(a, c) for c in b] for (a, b) in jobs_precedence_1], [])
    
        jobs_durations = {(d["job"], d["mode"]): d["duration"] for d in data["durations"]}
        total_resources = {r["id"]: r["available"] for r in data["resources"]}
        
        max_duration = {j: max(jobs_durations[j, m] for m in modes if (j, m) in jobs_durations.keys()) for j in jobs}
        periods = [p for p in range(sum(v for v in max_duration.values()))]

        self.input_data['max_duration'] = max_duration
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
        self.input_data["pWeightResources"] = {None: 10}
    
        return {None: self.input_data}
        
    def solve(self, options, print_file=False):
        """
        Solve the problem.
        """
        model = get_model()
        data = self.get_input_data()
        
        if options is None:
            options = {}
        if "timeLimit" in options:
            if "SOLVER_PARAMETERS" in options:
                options["SOLVER_PARAMETERS"]["sec"] = options["timeLimit"]
            else:
                options["SOLVER_PARAMETERS"] = {"sec":options["timeLimit"]}
        else:
            options["SOLVER_PARAMETERS"] = SOLVER_PARAMETERS
        
        model_instance = model.create_instance(data, report_timing=False)
        opt = SolverFactory('cbc')
        opt.options.update(options["SOLVER_PARAMETERS"])
        result = opt.solve(model_instance, tee=False)
        
        self.status = get_status(result)
        self.model_solution = model_instance
        obj = model_instance.f_obj()
        print("Status: {} Objective value: {}".format(self.status, obj))

        if is_feasible(self.status):
            if print_file:
                self.print_instance()
            data = self.format_solution()
            self.solution = Solution(data)
        else:
            self.solution = Solution({})
        
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
        
        #final = dict()
        final = pt.SuperDict()
        for j in set_jobs:
            final[j] = dict()
            final[j].update({'period': int(dict_start[j]), 'mode': int(mode_no_denso[j])})
        return final
        