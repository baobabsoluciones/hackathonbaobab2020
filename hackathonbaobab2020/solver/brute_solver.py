from hackathonbaobab2020.core import Experiment, Solution

from pyomo.environ import *
from pyomo.environ import SolverFactory
import pytups as pt

SOLVER_STATUS = {4: "optimal", 2: "maxTimeLimit", 3: "infeasible", 0: "unknown"}

SOLVER_PARAMETERS = {
    # maximum resolution time of each iteration.
    "sec": 600,
    # accepted absolute gap
    "allow": 1,
    # accepted relative gap (0.01 = 1%)
    "ratio": 0.01,
    # model tolerance
    "primalT": 10 ** -7,
}


def is_feasible(status):
    """
    Return True if the status is optimal or maxTimeLimit

    :param status: a status (string or pyomo object)
    :return: True if the status is optimal or maxTimeLimit
    """
    return str(status) == str(TerminationCondition.optimal) or str(status) == str(TerminationCondition.maxTimeLimit)


def get_status(result):
    """
    Return the status of the solution from the result object

    :param result: a pyomo result object
    :return: the status
    """
    return str(result.solver.termination_condition)


def var_to_dict(variable):
    """
    Transform a pyomo variable into a python dict

    :param variable: a pyomo variable
    :return: a dict containing the indices and values of the variable.
    """
    return {key: value(variable[key]) for key in variable.keys()}


def reverse_dict(d):
    return {j: i for i, j in d.items()}


def get_status_value(status):
    val = reverse_dict(SOLVER_STATUS)

    if status in val:
        return val[status]
    else:
        print("Unknown status: " + status)
        return val["Unknown"]


def get_assign_tasks_model():
    # Model definition
    model = AbstractModel()

    # Model sets definition
    model.sJobs = Set()
    model.sModes = Set()
    model.sResources = Set()
    model.sSlots = Set()

    # Model parameters definition
    model.pNumberSlots = Param(mutable=True)  # TODO comprobar si hace falta
    model.pDuration = Param(model.sJobs, model.sModes, mutable=True)
    model.pNeeds = Param(model.sJobs, model.sModes, model.sResources, mutable=True)
    model.pAvailability = Param(model.sResources, mutable=True)
    model.pResourceType = Param(model.sResources, mutable=True)  # 1 is renewable 2 not renewable
    model.p01Successor = Param(model.sJobs, model.sJobs, mutable=True, domain=Binary)
    model.pSlot = Param(model.sSlots, mutable=True)

    # Model variables definition
    model.v01Start = Var(model.sJobs, model.sSlots, domain=Binary)
    model.v01End = Var(model.sJobs, model.sSlots, domain=Binary)
    model.v01JobDone = Var(model.sJobs, model.sSlots, model.sModes, domain=Binary)
    model.v01JobMode = Var(model.sJobs, model.sModes, domain=Binary)
    model.vMaxSlot = Var(domain=NonNegativeIntegers)

    # Model constraint definition
    # c1: the start time of a task should be earlier than the end time
    def c1_start_before_end(model, iJob):
        return sum(model.v01End[iJob, iSlot] * model.pSlot[iSlot] for iSlot in model.sSlots) \
               >= sum(model.v01Start[iJob, iSlot] * model.pSlot[iSlot] for iSlot in model.sSlots)

    # c2: the renewable resources used during each period should be inferior to the resource availability
    def c2_renewable_resources(model, iSlot, iResource, iMode):
        if model.pResourceType[iResource] == 1:
            return sum(model.v01JobDone[iJob, iSlot, iMode] * model.pNeeds[iJob, iMode, iResource]
                       for iJob in model.sJobs if (iJob, iMode, iResource) in model.pNeeds) <= model.pAvailability[iResource]
        return Constraint.Skip

    # c3: the total non renewable resources used should be inferior to the resource availability
    def c3_non_renewable_resources(model, iResource, iMode):
        if model.pResourceType[iResource] == 2:
            # return sum(model.v01JobDone[iJob, iSlot, iMode] * model.pNeeds[iJob, iMode, iResource]
            return sum(model.v01JobMode[iJob, iMode] * model.pNeeds[iJob, iMode, iResource]
                       for iJob in model.sJobs if (iJob, iMode, iResource) in model.pNeeds) <= model.pAvailability[iResource]
        return Constraint.Skip

    # c4: precedence between tasks should be respected
    def c4_precedence(model, iJob, iJob2):
        if iJob != iJob2:
            return sum(model.v01Start[iJob2, iSlot] * model.pSlot[iSlot] for iSlot in model.sSlots) \
                   >= (sum(model.v01End[iJob, iSlot] * model.pSlot[iSlot] for iSlot in model.sSlots) + 1) \
                   * model.p01Successor[iJob, iJob2]
        return Constraint.Skip

    # c5: the number of slots in which the job is done should be equal to the job duration
    def c5_duration(model, iJob, iMode):
        if (iJob, iMode) in model.pDuration:
            return sum(model.v01JobDone[iJob, iSlot, iMode] for iSlot in model.sSlots) == model.pDuration[iJob, iMode] \
                   * model.v01JobMode[iJob, iMode]
        return Constraint.Skip

    # c6: the difference between the start and the end of a job is equal to its duration
    def c6_duration2(model, iJob):
        return sum(model.v01End[iJob, iSlot] * model.pSlot[iSlot] for iSlot in model.sSlots) \
               - sum(model.v01Start[iJob, iSlot] * model.pSlot[iSlot] for iSlot in model.sSlots) \
               == sum(model.v01JobMode[iJob, iMode] * model.pDuration[iJob, iMode] for iMode in model.sModes
                      if (iJob, iMode) in model.pDuration) - 1

    # c7: if a job ends in slot S, then the job is done in slot S but it is not done in slot S+1
    def c7_end_continuity(model, iJob, iSlot, iMode):
        if model.pSlot[iSlot] != model.pNumberSlots:  # TODO ver si funciona con ord(iSlot)
            return model.v01JobDone[iJob, iSlot, iMode] \
                   <= model.v01JobDone[iJob, iSlot + 1, iMode] + model.v01End[iJob, iSlot]
        return Constraint.Skip

    # c8: if a job starts in slot S+1, then the job is done in slot S+1 but it is not done in slot S
    def c8_start_continuity(model, iJob, iSlot, iMode):  # TODO ver si funciona con ord(iSlot), sino pSlot[iSlot]
        if model.pSlot[iSlot] != model.pNumberSlots:
            return model.v01JobDone[iJob, iSlot + 1, iMode] \
                   <= model.v01JobDone[iJob, iSlot, iMode] + model.v01Start[iJob, iSlot + 1]
        return Constraint.Skip

    # c9: the job can only start once
    def c9_one_start(model, iJob):
        return sum(model.v01Start[iJob, iSlot] for iSlot in model.sSlots) == 1

    # c10: the job can only end once
    def c10_one_end(model, iJob):
        return sum(model.v01End[iJob, iSlot] for iSlot in model.sSlots) == 1

    # c11: only one mode can be used for each job
    def c11_one_mode(model, iJob):
        return sum(model.v01JobMode[iJob, iMode] for iMode in model.sModes) == 1

    # c12: is a job J is done in a slot with mode M, then it means mode M is used for job J
    def c12_job_mode(model, iJob, iSlot, iMode):
        return model.v01JobMode[iJob, iMode] >= model.v01JobDone[iJob, iSlot, iMode]

    # c13: the variable to be minimized is the latest ending time
    def c13_total_duration(model, iJob, iSlot):
        return model.v01End[iJob, iSlot] * model.pSlot[iSlot] <= model.vMaxSlot

    # Activate constraints
    model.c1_start_before_end = Constraint(model.sJobs, rule=c1_start_before_end)
    model.c2_renewable_resources = Constraint(model.sSlots, model.sResources, model.sModes, rule=c2_renewable_resources)
    model.c3_non_renewable_resources = Constraint(model.sResources, model.sModes, rule=c3_non_renewable_resources)
    model.c4_precedence = Constraint(model.sJobs, model.sJobs, rule=c4_precedence)
    model.c5_duration = Constraint(model.sJobs, model.sModes, rule=c5_duration)
    model.c6_duration2 = Constraint(model.sJobs, rule=c6_duration2)
    model.c7_end_continuity = Constraint(model.sJobs, model.sSlots, model.sModes, rule=c7_end_continuity)
    model.c8_start_continuity = Constraint(model.sJobs, model.sSlots, model.sModes, rule=c8_start_continuity)
    model.c9_one_start = Constraint(model.sJobs, rule=c9_one_start)
    model.c10_one_end = Constraint(model.sJobs, rule=c10_one_end)
    model.c11_one_mode = Constraint(model.sJobs, rule=c11_one_mode)
    model.c12_job_mode = Constraint(model.sJobs, model.sSlots, model.sModes, rule=c12_job_mode)
    model.c13_total_duration = Constraint(model.sJobs, model.sSlots, rule=c13_total_duration)

    # Objective function definition
    def obj_expression(model):
        return model.vMaxSlot

    # Activate objective function
    model.f_obj = Objective(rule=obj_expression, sense=minimize)

    return model


class Brute_solver(Experiment):
    """
    Model created with Pyomo.
    """

    def __init__(self, instance, solution=None):
        if solution is None:
            solution = {}
        super().__init__(instance, solution)
        return

    def get_input_data(self):
        """
        Prepair the data for the model.
        """

        data = self.instance.to_dict()
        self.input_data = {}

        jobs = list(set([j["id"] for j in data["jobs"]]))
        modes = list(set([d["mode"] for d in data["durations"]]))
        resources = [r["id"] for r in data["resources"]]
        jobs_durations = {(d["job"], d["mode"]): d["duration"] for d in data["durations"]}
        resources_needs = {(n["job"], n["mode"], n["resource"]): n["need"] for n in data["needs"]}

        for j in jobs:
            for m in modes:
                # Change duration of 0 to 1, for coherence with formulation
                if (j, m) in jobs_durations and jobs_durations[(j, m)] == 0:
                    jobs_durations[(j, m)] = 1

        max_duration = {j: max(jobs_durations[j, m] for m in modes if (j, m) in jobs_durations.keys()) for j in jobs}
        periods = [p for p in range(1, sum(v for v in max_duration.values()))]
        total_resources = {r["id"]: r["available"] for r in data["resources"]}
        jobs_precedence_1 = [(j["id"], j["successors"]) for j in data["jobs"]]
        jobs_precedence = sum([[(a, c) for c in b] for (a, b) in jobs_precedence_1], [])

        self.input_data["sJobs"] = {None: jobs}
        self.input_data["sModes"] = {None: modes}
        self.input_data["sResources"] = {None: resources}
        self.input_data["pDuration"] = jobs_durations
        self.input_data["sSlots"] = {None: periods}
        self.input_data["pNeeds"] = resources_needs
        self.input_data["pAvailability"] = total_resources
        self.input_data['pNumberSlots'] = {None: len(periods)}

        resource_type = dict()  # 1 is renewable 2 not renewable
        for r in resources:
            if "R" in r:
                resource_type[r] = 1
            else:
                resource_type[r] = 2

        self.input_data['pResourceType'] = resource_type

        successor01 = dict()
        for j1 in jobs:
            for j2 in jobs:
                successor01[(j1, j2)] = 0

        for e in jobs_precedence:
            successor01[(e[0], e[1])] = 1

        self.input_data['p01Successor'] = successor01

        self.input_data['pSlot'] = {s: s for s in periods}

        return {None: self.input_data}

    def solve(self, options, print_file=False):
        """
        Solve the problem.
        """
        model = get_assign_tasks_model()

        data = self.get_input_data()

        # parameters of the resolution.

        if "timeLimit" in options:
            if "SOLVER_PARAMETERS" in options:
                options["SOLVER_PARAMETERS"]["sec"] = options["timeLimit"]
            else:
                options["SOLVER_PARAMETERS"] = {"sec": options["timeLimit"]}

        model_instance = model.create_instance(data, report_timing=True)
        opt = SolverFactory('cbc')

        opt.options.update(options["SOLVER_PARAMETERS"])
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

    def print_instance(self):
        print("printing instance")
        with open("instance_display.txt", "w") as f:
            self.model_solution.display(ostream=f)

    def format_solution(self):

        instance = self.model_solution
        dict_start = dict()

        for j in instance.sJobs:
            for s in instance.sSlots:
                if value(instance.v01Start[j,s]) == 1:
                    dict_start[j] = int(s)

        dict_mode = var_to_dict(instance.v01JobMode)
        set_jobs = [i for i in instance.sJobs]

        mode_no_denso = dict()
        for a, b in dict_mode.keys():
            if dict_mode[a, b] == 1:
                mode_no_denso.update({a: b})

        if len(mode_no_denso) == 0:
            return {}

        final = pt.SuperDict()
        for j in set_jobs:
            final[j] = dict()
            final[j].update({'period': int(dict_start[j]), 'mode': int(mode_no_denso[j])})
        return final
