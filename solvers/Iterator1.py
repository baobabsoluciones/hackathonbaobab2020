
from solvers.milp_LP_HL.model import get_model
from pyomo.environ import SolverFactory
from core import Experiment, Solution
from solvers.milp_LP_HL.pyomo_utils import is_feasible, get_status, var_to_dict,\
    deactivate_constraint, activate_constraint
from solvers.milp_LP_HL.configuration import SOLVER_PARAMETERS, MAX_PERIOD
from solvers.milp_LP_HL.project_utils import reverse_dict, get_status_value
from solvers.milp_LP_HL.generic_iterator import BaseIterator
from solvers.milp_LP_HL.function_utils import Chrono
from itertools import product
import pytups as pt
import pyomo.environ as pyo

class Iterator1(Experiment):
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
        
        jobs_modes = [(j, m) for (j, m) in jobs_durations.keys()
            if all([resources_needs[j, r, m] <= total_resources[r] for r in resources])]
        print(jobs_modes)
        max_duration = {j:max(jobs_durations[j, m] for m in modes if (j, m) in jobs_modes) for j in jobs}
        
        self.input_data['max_duration'] = max_duration
        self.input_data["sJobs"] = {None: jobs}
        self.input_data["sPeriods"] = {None: periods}
        self.input_data["sRResources"] = {None: [r for r in resources if "R" in r]}
        self.input_data["sNResources"] = {None: [r for r in resources if "N" in r]}
        self.input_data["sResources"] = {None: resources}
        self.input_data["sModes"] = {None: modes}
        self.input_data["sJobsPrecedence"] = {None: jobs_precedence}
        self.input_data["sJobsModes"] = {None: jobs_modes}
        self.input_data["pResourcesUsed"] = resources_needs
        self.input_data["pDuration"] = jobs_durations
        self.input_data["pMaxResources"] = total_resources
        self.input_data["pWeightMakespan"] = {None: 1}
        self.input_data["pWeightResources"] = {None: 1}
    
        return {None: self.input_data}
    
    def solve(self, options, print_file=False):
        """
        Solve the problem.
        """
        model = get_model()
        data = self.get_input_data()
        
        model_instance = model.create_instance(data, report_timing=True)
        opt = SolverFactory('cbc')
        opt.options.update(options["SOLVER_PARAMETERS"])
        self.iterator = BaseIterator(model_instance, opt, verbose=True)
        self.get_initial_solution(step=5, modes_steps=3)
        
        result = opt.solve(model_instance, tee=True)
        
        self.status = get_status(result)
        self.model_solution = model_instance
        print(self.status)

        if is_feasible(self.status):
            if print_file:
                self.print_instance()
            data = self.format_solution()
            self.solution = Solution(data)
        else:
            self.solution = Solution({})
        
        return get_status_value(self.status)
    
    
    def get_modes_order(self, current_resources=None):
        
        pResourcesUsed = self.input_data["pResourcesUsed"]
        pMaxResources = self.input_data["pMaxResources"]
        sNResources = self.input_data["sNResources"][None]
        sJobsModes = self.input_data["sJobsModes"][None]
        sModes = self.input_data["sModes"][None]
        sJobs = self.input_data["sJobs"][None]
        
        if current_resources is not None:
            resources_left = {r:(pMaxResources[r] - current_resources[r]) for r in sNResources}
        else:
            resources_left = pMaxResources
        print(resources_left)
        modes_n_resources = {(j, m): sum((pResourcesUsed[(j, r, m)] / resources_left[r])
                                        for r in sNResources if (j, r, m) in pResourcesUsed) for (j, m) in sJobsModes}
    
        jobs_modes = {j: [m for m in sModes if (j, m) in sJobsModes] for j in sJobs}
    
        modes_order = {j: sorted(jobs_modes[j], key=lambda m: modes_n_resources[j, m]) for j in sJobs}
        
        return modes_order
    
    def get_initial_solution(self, step, modes_steps):
    
        chrono = Chrono("construction of a first solution", silent=False)
        
        var_map = {
            "v01Start": ["sJobs", "sPeriods"],
            "v01End": ["sJobs", "sPeriods"],
            "v01Work": ["sJobs", "sPeriods"],
            "v01Mode": ["sJobsModes"],
            "vResources": ["sResources", "sJobs", "sPeriods"],
            "vStart": ["sJobs"],
            "vEnd": ["sJobs"]
        }

        sJobs = self.input_data["sJobs"][None]
        
        modes_order = self.get_modes_order()
        first_modes = [(j, modes_order[j][0]) for j in sJobs]
        
        self.iterator.set_variable_map(var_map)
    
        self.iterator.set_var_initial_values()
        
        k = 0
        i = 0
        free_indices = {"sJobs":[], "sPeriods":[], "sJobsModes":[], "sResources": self.input_data["sResources"][None]}
        fixed_indices = {"sJobs":[], "sPeriods": [], "sJobsModes": [], "sResources": []}
        self.iteration = {}
        max_jobs = len(sJobs)
        makespan = 0
        
        # TODO: find a more elegant way to do this
        deactivate_constraint(self.iterator.get_constraint("c10_precedence"))
        
        # Create a first solution with all jobs and the "cheapest" modes
        while k < max_jobs:
            i += 1
            print("iteration ", i)
            max_j = min(k + step, max_jobs)
            max_period = int(3 + makespan + sum(self.input_data["max_duration"][sJobs[j]] for j in range(k, max_j)))
            fixed_indices["sJobs"] += free_indices["sJobs"]
            fixed_indices["sJobsModes"] += free_indices["sJobsModes"]
            fixed_indices["sPeriods"] = [j for j in range(max_period)]
            free_indices["sJobs"] = [sJobs[j] for j in range(k, max_j)]
            free_indices["sJobsModes"] = [(j, m) for (j, m) in first_modes if j in free_indices["sJobs"]]
            expected_resources = {r: sum(self.input_data["pResourcesUsed"][j, r, m] for j,m in free_indices["sJobsModes"])
                                  for r in self.input_data["sNResources"][None]}
            print("free indices ", free_indices)
            print("fixed indices ", fixed_indices)
            print("Expected resources used", expected_resources)
            
            free_jobs = [(i,j) for (i,j) in product(free_indices["sJobs"], free_indices["sJobs"]) if i != j]
            activate_constraint(self.iterator.get_constraint("c10_precedence"), free_jobs)
            
            self.iteration[i] = self.iterator.iterate(free_indices, fixed_indices,
                                                      excluded_constraints=["c10_precedence"])
            makespan = pyo.value(self.iterator.get_variable("vMakespan"))
            k = max_j
            
            print("Objective: " + str(makespan))
            v01Mode = var_to_dict(self.iterator.get_variable("v01Mode"))
            resources_used = {r: sum(v01Mode[j, m] * self.input_data["pResourcesUsed"][j, r, m]
                   for (j, m) in self.input_data["sJobsModes"][None]) for r in self.input_data["sNResources"][None]}
            modes_order = self.get_modes_order(resources_used)
            first_modes = [(j, modes_order[j][0]) for j in sJobs]
            print("Resources_used: ", resources_used)
            
            if not is_feasible(self.iteration[i][0]):
                print("Error encountered")
                break
                
        print("Current objective value: " + str(self.iteration[i][0]))
        
        self.iterator.instance.sPeriods.values = [i for i in range(int(makespan + 1))]
        self.input_data["sJobs"][None] = [i for i in range(int(makespan + 1))]

        if is_feasible(self.iteration[i][0]):
            # Add the other modes little by little
            k = 0
            i = 0
            
            while k < max_jobs:
                i += 1
                print("iteration ", i)
                max_j = min(k + modes_steps, max_jobs)
                free_jobs = range(k, max_j)
                self.solve_with_free_jobs_modes(free_jobs)
                k = max_j
        
        self.model_solution = self.iterator.instance
        self.print_instance()
        
        chrono.stop()
    
    def solve_with_free_jobs_modes(self, free_jobs):
        
        sJobs = self.input_data["sJobs"][None]
        sPeriods = self.input_data["sPeriods"][None]
        sJobsModes = self.input_data["sJobsModes"][None]
        
        free_jobs_modes = [(j, m) for j,m in sJobsModes if j in free_jobs]
        fixed_jobs_modes = [k for k in sJobsModes if k not in free_jobs_modes]
        
        free_indices = {"sJobs":sJobs, "sPeriods":sPeriods, "sJobsModes":free_jobs_modes,
                        "sResources": self.input_data["sResources"][None]}
        fixed_indices = {"sJobs":[], "sPeriods": [], "sJobsModes": fixed_jobs_modes, "sResources": []}
        
        self.iterator.iterate(free_indices, fixed_indices)
    
    def print_instance(self):
        print("printing instance")
        with open("instance_display.txt", "w") as f:
            self.model_solution.display(ostream=f)
        
        with open("instance_pprint.txt", "w") as f:
            self.model_solution.pprint(ostream=f)

    def format_solution(self):
    
        instance = self.model_solution
        dict_start = var_to_dict(instance.vStart)
        dict_mode = var_to_dict(instance.v01Mode)
        set_jobs = [i for i in instance.sJobs]
    
        mode_no_denso = dict()
        for a, b in dict_mode.keys():
            if dict_mode[a, b] == 1:
                mode_no_denso.update({a: b})
    
        if len(mode_no_denso) == 0:
            return {}

        # final = dict()
        final = pt.SuperDict()
        for j in set_jobs:
            final[j] = dict()
            final[j].update({'period': int(dict_start[j]), 'mode': int(mode_no_denso[j])})
        return final
        