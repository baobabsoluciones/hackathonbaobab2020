from hackathonbaobab2020.core import Experiment, Solution

from pyomo.environ import *
from pyomo.environ import SolverFactory
import pytups as pt
import logging as log
import time

start_time = time.time()

SOLVER_STATUS = {4: "optimal", 2: "maxTimeLimit", 3: "infeasible", 0: "unknown"}

SOLVER_PARAMETERS = {
    # maximum resolution time of each iteration.
    "sec": 300,
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
    return str(status) == str(TerminationCondition.optimal) or str(status) == str(
        TerminationCondition.maxTimeLimit
    )


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


def write_cbc_warmstart_file(filename, instance, opt):
    """
    This function writes a file to be passed to cbc solver as a warmstart file.
    This function is necessary because of a bug of cbc that does not allow reading warmstart files on windows
    with an absolute path.
    :param filename: path to the file
    :param instance: model instance (created with create_instance)
    :param opt: solver instance (created with solver factory)
    :return:
    """
    opt._presolve(instance)
    opt._write_soln_file(instance, filename)


def get_assign_tasks_model():
    # Model definition
    model = AbstractModel()

    # Model sets definition
    model.sJobs = Set()
    model.sModes = Set()
    model.sResources = Set()
    model.sSlots = Set()

    # Model parameters definition
    model.pNumberSlots = Param(mutable=True)
    model.pDuration = Param(model.sJobs, model.sModes, mutable=True)
    model.pNeeds = Param(model.sJobs, model.sModes, model.sResources, mutable=True)
    model.pAvailability = Param(model.sResources, mutable=True)
    model.pResourceType = Param(
        model.sResources, mutable=True
    )  # 1 is renewable 2 not renewable
    model.p01Successor = Param(model.sJobs, model.sJobs, mutable=True, domain=Binary)
    model.pSlot = Param(model.sSlots, mutable=True)

    # Model variables definition
    model.v01Start = Var(model.sJobs, model.sSlots, domain=Binary)
    model.v01End = Var(model.sJobs, model.sSlots, domain=Binary)
    model.v01JobDone = Var(model.sJobs, model.sSlots, model.sModes, domain=Binary)
    model.v01JobMode = Var(model.sJobs, model.sModes, domain=Binary)
    model.vMaxSlot = Var(domain=NonNegativeReals)

    # Model constraint definition
    # c1: the start time of a task should be earlier than the end time
    def c1_start_before_end(model, iJob):
        return sum(
            model.v01End[iJob, iSlot] * model.pSlot[iSlot] for iSlot in model.sSlots
        ) >= sum(
            model.v01Start[iJob, iSlot] * model.pSlot[iSlot] for iSlot in model.sSlots
        )

    # c2: the renewable resources used during each period should be inferior to the resource availability
    def c2_renewable_resources(model, iSlot, iResource):
        if model.pResourceType[iResource] == 1:
            return (
                sum(
                    model.v01JobDone[iJob, iSlot, iMode]
                    * model.pNeeds[iJob, iMode, iResource]
                    for iJob in model.sJobs
                    for iMode in model.sModes
                    if (iJob, iMode, iResource) in model.pNeeds
                )
                <= model.pAvailability[iResource]
            )
        return Constraint.Skip

    # c3: the total non renewable resources used should be inferior to the resource availability
    def c3_non_renewable_resources(model, iResource):
        if model.pResourceType[iResource] == 2:
            # return sum(model.v01JobDone[iJob, iSlot, iMode] * model.pNeeds[iJob, iMode, iResource]
            return (
                sum(
                    model.v01JobMode[iJob, iMode] * model.pNeeds[iJob, iMode, iResource]
                    for iJob in model.sJobs
                    for iMode in model.sModes
                    if (iJob, iMode, iResource) in model.pNeeds
                )
                <= model.pAvailability[iResource]
            )
        return Constraint.Skip

    # c4: precedence between tasks should be respected
    def c4_precedence(model, iJob, iJob2):
        if iJob != iJob2 and model.p01Successor[iJob, iJob2] == 1:
            return sum(
                model.v01Start[iJob2, iSlot] * model.pSlot[iSlot]
                for iSlot in model.sSlots
            ) >= (
                sum(
                    model.v01End[iJob, iSlot] * model.pSlot[iSlot]
                    for iSlot in model.sSlots
                )
                + 1
            )
        return Constraint.Skip

    # c5: the number of slots in which the job is done should be equal to the job duration
    # def c5_duration(model, iJob, iMode):
    #    if (iJob, iMode) in model.pDuration:
    #        return sum(model.v01JobDone[iJob, iSlot, iMode] for iSlot in model.sSlots) == model.pDuration[iJob, iMode] \
    #               * model.v01JobMode[iJob, iMode]
    #    return Constraint.Skip

    # c6: the difference between the start and the end of a job is equal to its duration
    def c6_duration2(model, iJob):
        return (
            sum(
                model.v01End[iJob, iSlot] * model.pSlot[iSlot] for iSlot in model.sSlots
            )
            - sum(
                model.v01Start[iJob, iSlot] * model.pSlot[iSlot]
                for iSlot in model.sSlots
            )
            == sum(
                model.v01JobMode[iJob, iMode] * model.pDuration[iJob, iMode]
                for iMode in model.sModes
                if (iJob, iMode) in model.pDuration
            )
            - 1
        )

    # c7: if a job ends in slot S, then the job is done in slot S but it is not done in slot S+1
    def c7_end_continuity(model, iJob, iSlot, iMode):
        if model.pSlot[iSlot] != model.pNumberSlots:
            return (
                model.v01JobDone[iJob, iSlot, iMode]
                <= model.v01JobDone[iJob, iSlot + 1, iMode] + model.v01End[iJob, iSlot]
            )
        return Constraint.Skip

    # c8: if a job starts in slot S+1, then the job is done in slot S+1 but it is not done in slot S
    def c8_start_continuity(model, iJob, iSlot, iMode):
        if model.pSlot[iSlot] != model.pNumberSlots:
            return (
                model.v01JobDone[iJob, iSlot + 1, iMode]
                <= model.v01JobDone[iJob, iSlot, iMode]
                + model.v01Start[iJob, iSlot + 1]
            )
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
    model.c2_renewable_resources = Constraint(
        model.sSlots, model.sResources, rule=c2_renewable_resources
    )
    model.c3_non_renewable_resources = Constraint(
        model.sResources, rule=c3_non_renewable_resources
    )
    model.c4_precedence = Constraint(model.sJobs, model.sJobs, rule=c4_precedence)
    # model.c5_duration = Constraint(model.sJobs, model.sModes, rule=c5_duration)
    model.c6_duration2 = Constraint(model.sJobs, rule=c6_duration2)
    model.c7_end_continuity = Constraint(
        model.sJobs, model.sSlots, model.sModes, rule=c7_end_continuity
    )
    model.c8_start_continuity = Constraint(
        model.sJobs, model.sSlots, model.sModes, rule=c8_start_continuity
    )
    model.c9_one_start = Constraint(model.sJobs, rule=c9_one_start)
    model.c10_one_end = Constraint(model.sJobs, rule=c10_one_end)
    model.c11_one_mode = Constraint(model.sJobs, rule=c11_one_mode)
    model.c12_job_mode = Constraint(
        model.sJobs, model.sSlots, model.sModes, rule=c12_job_mode
    )
    model.c13_total_duration = Constraint(
        model.sJobs, model.sSlots, rule=c13_total_duration
    )

    # Objective function definition
    def obj_expression(model):
        return model.vMaxSlot

        # Activate objective function

    model.f_obj = Objective(rule=obj_expression, sense=minimize)

    return model


def get_feasible_modes():
    # Model definition
    model = AbstractModel()

    # Model sets definition
    model.sJobs = Set()
    model.sModes = Set()
    model.sResources = Set()

    # Model parameters definition
    model.pDuration = Param(model.sJobs, model.sModes, mutable=True)
    model.pNeeds = Param(model.sJobs, model.sModes, model.sResources, mutable=True)
    model.pAvailability = Param(model.sResources, mutable=True)
    model.pResourceType = Param(
        model.sResources, mutable=True
    )  # 1 is renewable 2 not renewable

    # Model variables definition
    model.v01JobMode = Var(model.sJobs, model.sModes, domain=Binary)
    model.vMaxSlot = Var(domain=NonNegativeReals)

    # c2: the renewable resources used during each period should be inferior to the resource availability
    def c2_renewable_resources(model, iJob, iResource):
        if model.pResourceType[iResource] == 1:
            return (
                sum(
                    model.v01JobMode[iJob, iMode] * model.pNeeds[iJob, iMode, iResource]
                    for iMode in model.sModes
                    if (iJob, iMode, iResource) in model.pNeeds
                )
                <= model.pAvailability[iResource]
            )
        return Constraint.Skip

    # Model constraint definition
    # c3: the total non renewable resources used should be inferior to the resource availability
    def c3_non_renewable_resources(model, iResource):
        if model.pResourceType[iResource] == 2:
            return (
                sum(
                    model.v01JobMode[iJob, iMode] * model.pNeeds[iJob, iMode, iResource]
                    for iJob in model.sJobs
                    for iMode in model.sModes
                    if (iJob, iMode, iResource) in model.pNeeds
                )
                <= model.pAvailability[iResource]
            )
        return Constraint.Skip

    # c11: only one mode can be used for each job
    def c11_one_mode(model, iJob):
        return (
            sum(
                model.v01JobMode[iJob, iMode]
                for iMode in model.sModes
                if (iJob, iMode) in model.pDuration
            )
            == 1
        )

    # c13: the variable to be minimized is the latest ending time
    def c13_total_duration(model):
        return (
            sum(
                model.pDuration[iJob, iMode] * model.v01JobMode[iJob, iMode]
                for iJob in model.sJobs
                for iMode in model.sModes
                if (iJob, iMode) in model.pDuration
            )
            <= model.vMaxSlot
        )

    # Activate constraints
    model.c3_non_renewable_resources = Constraint(
        model.sResources, rule=c3_non_renewable_resources
    )
    model.c11_one_mode = Constraint(model.sJobs, rule=c11_one_mode)
    model.c13_total_duration = Constraint(rule=c13_total_duration)

    # Objective function definition
    def obj_expression(model):
        return model.vMaxSlot

        # Activate objective function

    model.f_obj = Objective(rule=obj_expression, sense=minimize)

    return model


def get_tasks_fix_modes():
    # Model definition
    model = AbstractModel()

    # Model sets definition
    model.sJobs = Set()
    model.sResources = Set()
    model.sSlots = Set()

    # Model parameters definition
    model.pNumberSlots = Param(mutable=True)
    model.pDuration = Param(model.sJobs, mutable=True)
    model.pNeeds = Param(model.sJobs, model.sResources, mutable=True)
    model.pAvailability = Param(model.sResources, mutable=True)
    model.pResourceType = Param(
        model.sResources, mutable=True
    )  # 1 is renewable 2 not renewable
    model.p01Successor = Param(model.sJobs, model.sJobs, mutable=True, domain=Binary)
    model.pSlot = Param(model.sSlots, mutable=True)

    # Model variables definition
    model.v01Start = Var(model.sJobs, model.sSlots, domain=Binary)
    model.v01End = Var(model.sJobs, model.sSlots, domain=Binary)
    model.v01JobDone = Var(model.sJobs, model.sSlots, domain=Binary)
    model.vMaxSlot = Var(domain=NonNegativeReals)

    # Model constraint definition
    # c1: the start time of a task should be earlier than the end time
    def c1_start_before_end(model, iJob):
        return sum(
            model.v01End[iJob, iSlot] * model.pSlot[iSlot] for iSlot in model.sSlots
        ) >= sum(
            model.v01Start[iJob, iSlot] * model.pSlot[iSlot] for iSlot in model.sSlots
        )

    # c2: the renewable resources used during each period should be inferior to the resource availability
    def c2_renewable_resources(model, iSlot, iResource):
        if model.pResourceType[iResource] == 1:
            return (
                sum(
                    model.v01JobDone[iJob, iSlot] * model.pNeeds[iJob, iResource]
                    for iJob in model.sJobs
                )
                <= model.pAvailability[iResource]
            )
        return Constraint.Skip

    # c4: precedence between tasks should be respected
    def c4_precedence(model, iJob, iJob2):
        if iJob != iJob2 and model.p01Successor[iJob, iJob2] == 1:
            return sum(
                model.v01Start[iJob2, iSlot] * model.pSlot[iSlot]
                for iSlot in model.sSlots
            ) >= (
                sum(
                    model.v01End[iJob, iSlot] * model.pSlot[iSlot]
                    for iSlot in model.sSlots
                )
                + 1
            )
        return Constraint.Skip

    # c5: the number of slots in which the job is done should be equal to the job duration
    def c5_duration(model, iJob):
        return (
            sum(model.v01JobDone[iJob, iSlot] for iSlot in model.sSlots)
            == model.pDuration[iJob]
        )

    # c6: the difference between the start and the end of a job is equal to its duration
    def c6_duration2(model, iJob):
        return (
            sum(
                model.v01End[iJob, iSlot] * model.pSlot[iSlot] for iSlot in model.sSlots
            )
            - sum(
                model.v01Start[iJob, iSlot] * model.pSlot[iSlot]
                for iSlot in model.sSlots
            )
            == model.pDuration[iJob] - 1
        )

    # c7: if a job ends in slot S, then the job is done in slot S but it is not done in slot S+1
    def c7_end_continuity(model, iJob, iSlot):
        if model.pSlot[iSlot] != model.pNumberSlots:
            return (
                model.v01JobDone[iJob, iSlot]
                <= model.v01JobDone[iJob, iSlot + 1] + model.v01End[iJob, iSlot]
            )
        return Constraint.Skip

    # c8: if a job starts in slot S+1, then the job is done in slot S+1 but it is not done in slot S
    def c8_start_continuity(model, iJob, iSlot):
        if model.pSlot[iSlot] != model.pNumberSlots:
            return (
                model.v01JobDone[iJob, iSlot + 1]
                <= model.v01JobDone[iJob, iSlot] + model.v01Start[iJob, iSlot + 1]
            )
        return Constraint.Skip

    # c9: the job can only start once
    def c9_one_start(model, iJob):
        return sum(model.v01Start[iJob, iSlot] for iSlot in model.sSlots) == 1

    # c10: the job can only end once
    def c10_one_end(model, iJob):
        return sum(model.v01End[iJob, iSlot] for iSlot in model.sSlots) == 1

    # c13: the variable to be minimized is the latest ending time
    def c13_total_duration(model, iJob, iSlot):
        return model.v01End[iJob, iSlot] * model.pSlot[iSlot] <= model.vMaxSlot

    # Activate constraints
    model.c1_start_before_end = Constraint(model.sJobs, rule=c1_start_before_end)
    model.c2_renewable_resources = Constraint(
        model.sSlots, model.sResources, rule=c2_renewable_resources
    )
    model.c4_precedence = Constraint(model.sJobs, model.sJobs, rule=c4_precedence)
    model.c5_duration = Constraint(model.sJobs, rule=c5_duration)
    model.c6_duration2 = Constraint(model.sJobs, rule=c6_duration2)
    model.c7_end_continuity = Constraint(
        model.sJobs, model.sSlots, rule=c7_end_continuity
    )
    model.c8_start_continuity = Constraint(
        model.sJobs, model.sSlots, rule=c8_start_continuity
    )
    model.c9_one_start = Constraint(model.sJobs, rule=c9_one_start)
    model.c10_one_end = Constraint(model.sJobs, rule=c10_one_end)
    model.c13_total_duration = Constraint(
        model.sJobs, model.sSlots, rule=c13_total_duration
    )

    # Objective function definition
    def obj_expression(model):
        return model.vMaxSlot

        # Activate objective function

    model.f_obj = Objective(rule=obj_expression, sense=minimize)

    return model


class Fix_loop_solver(Experiment):
    """
    Model created with Pyomo.
    """

    def __init__(self, instance, solution=None):
        super().__init__(instance, solution)
        return

    def get_input_data(self, jobsToSolve=-1, previusSlots=1):
        """
        Prepair the data for the model.
        """

        data = self.instance.to_dict()
        self.input_data = {}

        list_total_jobs = list(set([j["id"] for j in data["jobs"]]))

        if jobsToSolve == -1:
            jobsToSolve = len(list_total_jobs)

        jobs = list(set([j["id"] for j in data["jobs"] if j["id"] <= jobsToSolve]))
        modes = list(set([d["mode"] for d in data["durations"]]))
        resources = [r["id"] for r in data["resources"]]
        jobs_durations = {
            (d["job"], d["mode"]): d["duration"]
            for d in data["durations"]
            if d["job"] <= jobsToSolve
        }
        resources_needs = {
            (n["job"], n["mode"], n["resource"]): n["need"]
            for n in data["needs"]
            if n["job"] <= jobsToSolve
        }

        for j in jobs:
            for m in modes:
                # Change duration of 0 to 1, for coherence with formulation
                if (j, m) in jobs_durations and jobs_durations[(j, m)] == 0:
                    jobs_durations[(j, m)] = 1

        max_duration_new_job = 0
        mode_max_duration = 1
        for m in modes:
            if (jobs[-1], m) in jobs_durations.keys():
                if jobs_durations[jobs[-1], m] >= max_duration_new_job:
                    max_duration_new_job = jobs_durations[jobs[-1], m]
                    mode_max_duration = m

        periods = [p for p in range(1, 1 + int(previusSlots + max_duration_new_job))]
        total_resources = {r["id"]: r["available"] for r in data["resources"]}
        jobs_precedence_1 = [
            (j["id"], j["successors"]) for j in data["jobs"] if j["id"] <= jobsToSolve
        ]
        jobs_precedence = sum([[(a, c) for c in b] for (a, b) in jobs_precedence_1], [])

        self.input_data["sJobs"] = {None: jobs}
        self.input_data["sModes"] = {None: modes}
        self.input_data["sResources"] = {None: resources}
        self.input_data["pDuration"] = jobs_durations
        self.input_data["sSlots"] = {None: periods}
        self.input_data["pNeeds"] = resources_needs
        self.input_data["pAvailability"] = total_resources
        self.input_data["pNumberSlots"] = {None: len(periods)}

        resource_type = dict()  # 1 is renewable 2 not renewable
        for r in resources:
            if "R" in r:
                resource_type[r] = 1
            else:
                resource_type[r] = 2

        self.input_data["pResourceType"] = resource_type

        successor01 = dict()
        for j1 in jobs:
            for j2 in jobs:
                successor01[(j1, j2)] = 0

        for e in jobs_precedence:
            if e[1] <= jobsToSolve:
                successor01[(e[0], e[1])] = 1

        self.input_data["p01Successor"] = successor01
        self.input_data["pSlot"] = {s: s for s in periods}

        return {None: self.input_data}, max_duration_new_job, mode_max_duration

    def get_input_data_fix_mode(self, jobsToSolve=-1, previusSlots=1):
        """
        Prepair the data for the model.
        """

        data = self.instance.to_dict()
        self.input_data = {}
        fixed_jobs_modes = self.fixed_jobs_modes

        list_total_jobs = list(set([j["id"] for j in data["jobs"]]))

        if jobsToSolve == -1:
            jobsToSolve = len(list_total_jobs)

        jobs = list(set([j["id"] for j in data["jobs"] if j["id"] <= jobsToSolve]))
        modes = list(set([d["mode"] for d in data["durations"]]))
        resources = [r["id"] for r in data["resources"]]
        jobs_durations_aux = {
            (d["job"], d["mode"]): d["duration"]
            for d in data["durations"]
            if d["job"] <= jobsToSolve
        }
        resources_needs_aux = {
            (n["job"], n["mode"], n["resource"]): n["need"]
            for n in data["needs"]
            if n["job"] <= jobsToSolve
        }
        resources_needs = dict()
        jobs_durations = dict()

        for j in jobs:
            for m in modes:
                if (j, m) in fixed_jobs_modes:
                    # assign duration based on input
                    if fixed_jobs_modes[j, m] == 1:
                        jobs_durations[j] = jobs_durations_aux[j, m]

                        # Change duration of 0 to 1, for coherence with formulation
                        if jobs_durations[j] == 0:
                            jobs_durations[j] = 1

                        # assign needs based on input
                        for r in resources:
                            resources_needs[(j, r)] = resources_needs_aux[j, m, r]

        max_duration_new_job = jobs_durations[jobsToSolve]
        periods = [p for p in range(1, 1 + int(previusSlots + max_duration_new_job))]
        total_resources = {r["id"]: r["available"] for r in data["resources"]}
        jobs_precedence_1 = [
            (j["id"], j["successors"]) for j in data["jobs"] if j["id"] <= jobsToSolve
        ]
        jobs_precedence = sum([[(a, c) for c in b] for (a, b) in jobs_precedence_1], [])

        self.input_data["sJobs"] = {None: jobs}
        self.input_data["sResources"] = {None: resources}
        self.input_data["pDuration"] = jobs_durations
        self.input_data["sSlots"] = {None: periods}
        self.input_data["pNeeds"] = resources_needs
        self.input_data["pAvailability"] = total_resources
        self.input_data["pNumberSlots"] = {None: len(periods)}

        resource_type = dict()  # 1 is renewable 2 not renewable
        for r in resources:
            if "R" in r:
                resource_type[r] = 1
            else:
                resource_type[r] = 2

        self.input_data["pResourceType"] = resource_type

        successor01 = dict()
        for j1 in jobs:
            for j2 in jobs:
                successor01[(j1, j2)] = 0

        for e in jobs_precedence:
            if e[1] <= jobsToSolve:
                successor01[(e[0], e[1])] = 1

        self.input_data["p01Successor"] = successor01
        self.input_data["pSlot"] = {s: s for s in periods}

        return {None: self.input_data}, max_duration_new_job

    def solve(self, options, print_file=False):
        """
        Solve the problem.
        """
        print_file = options.get("print_file", False)
        debug = log.root.level == log.DEBUG
        # parameters of the resolution.
        if "SOLVER_PARAMETERS" not in options:
            options["SOLVER_PARAMETERS"] = {}
        if "timeLimit" in options:
            if "SOLVER_PARAMETERS" in options:
                options["SOLVER_PARAMETERS"]["sec"] = options["timeLimit"]
            else:
                options["SOLVER_PARAMETERS"] = {"sec": options["timeLimit"]}
        else:
            options["timeLimit"] = SOLVER_PARAMETERS["sec"]
        log.debug("Max time(s): ", options["timeLimit"])

        dataDict = self.instance.to_dict()
        listJobs = list(set([j["id"] for j in dataDict["jobs"]]))

        # First we calculate feasible modes for jobs
        model_modes = get_feasible_modes()
        data, max_duration_new_job, mode_max_duration = self.get_input_data(
            jobsToSolve=len(listJobs)
        )
        model_modes_instance = model_modes.create_instance(data)
        opt = SolverFactory("cbc")
        opt.options.update(options["SOLVER_PARAMETERS"])
        result = opt.solve(model_modes_instance, tee=debug)

        self.status = get_status(result)
        self.model_solution = model_modes_instance

        if not is_feasible(self.status):
            self.solution = Solution({})
            return get_status_value(self.status)

        for iResource in model_modes_instance.sResources:
            log.debug(
                "used",
                iResource,
                sum(
                    value(model_modes_instance.v01JobMode[iJob, iMode])
                    * value(model_modes_instance.pNeeds[iJob, iMode, iResource])
                    for iJob in model_modes_instance.sJobs
                    for iMode in model_modes_instance.sModes
                    if (iJob, iMode, iResource) in model_modes_instance.pNeeds
                ),
                "total:",
                value(model_modes_instance.pAvailability[iResource]),
            )
        for iJob in model_modes_instance.sJobs:
            for iMode in model_modes_instance.sModes:
                if (iJob, iMode) in model_modes_instance.pDuration:
                    if value(model_modes_instance.v01JobMode[iJob, iMode]) == 1:
                        log.debug(iJob, iMode)

        log.debug("time fix model (s):", result.solver.system_time)

        self.fixed_jobs_modes = {
            (iJob, iMode): value(model_modes_instance.v01JobMode[iJob, iMode])
            for iJob in model_modes_instance.sJobs
            for iMode in model_modes_instance.sModes
            if (iJob, iMode) in model_modes_instance.pDuration
        }
        # End feasible modes

        model = get_tasks_fix_modes()

        log.debug("Starting loop")
        # Loop for solving the problem
        for loop_jobs in listJobs:
            if loop_jobs == 2:
                # First we solve without warmstart
                # Get the data
                data, max_duration_new_job = self.get_input_data_fix_mode(
                    jobsToSolve=loop_jobs
                )
                model_instance = model.create_instance(data)
                opt = SolverFactory("cbc")
                options["SOLVER_PARAMETERS"] = {"ratio": 0.2}
                opt.options.update(options["SOLVER_PARAMETERS"])
                result = opt.solve(model_instance)
                end_solve = time.time()

                self.status = get_status(result)
                self.model_solution = model_instance

                if not is_feasible(self.status):
                    self.solution = Solution({})
                    return get_status_value(self.status)

                log.debug(
                    "Jobs solved: ",
                    loop_jobs,
                    ", nº Slots:",
                    int(value(model_instance.vMaxSlot)),
                    ", time (s):",
                    result.solver.system_time,
                )
                previous_instance = model_instance
                aux_periods = 0

            elif loop_jobs > 2:
                # We solve starting with previous solution and add new job
                # Get the data
                data, max_duration_new_job = self.get_input_data_fix_mode(
                    jobsToSolve=loop_jobs,
                    previusSlots=aux_periods + value(previous_instance.vMaxSlot),
                )
                if loop_jobs == listJobs[-1]:
                    model_instance = model.create_instance(data)
                    options["SOLVER_PARAMETERS"] = {"ratio": 0.01}
                    opt.options.update(options["SOLVER_PARAMETERS"])
                else:
                    model_instance = model.create_instance(data)

                # Initialize previous solution
                for j in previous_instance.sJobs:
                    for s in previous_instance.sSlots:
                        if s <= model_instance.sSlots[-1]:
                            model_instance.v01Start[j, s].value = value(
                                previous_instance.v01Start[j, s]
                            )
                            model_instance.v01End[j, s].value = value(
                                previous_instance.v01End[j, s]
                            )
                            model_instance.v01JobDone[j, s].value = value(
                                previous_instance.v01JobDone[j, s]
                            )
                            # model_instance.vMaxSlot.value = value(previous_instance.vMaxSlot) +

                # Initialize new job, first to 0
                for n in range(
                    int(value(previous_instance.vMaxSlot) + 1),
                    int(value(previous_instance.vMaxSlot) + max_duration_new_job + 1),
                ):
                    model_instance.v01Start[loop_jobs, n].value = 0
                    model_instance.v01End[loop_jobs, n].value = 0

                # Then to 1 only when true
                model_instance.v01Start[
                    loop_jobs, int(value(previous_instance.vMaxSlot) + 1)
                ].value = 1
                model_instance.v01End[
                    loop_jobs,
                    int(value(previous_instance.vMaxSlot) + max_duration_new_job),
                ].value = 1
                for n in range(
                    int(value(previous_instance.vMaxSlot) + 1),
                    int(value(previous_instance.vMaxSlot) + max_duration_new_job + 1),
                ):
                    model_instance.v01JobDone[loop_jobs, n].value = 1

                # WarmStart
                write_cbc_warmstart_file("./cbc_warmstart.soln", model_instance, opt)

                result = opt.solve(
                    model_instance,
                    tee=debug,
                    warmstart=True,
                    warmstart_file="./cbc_warmstart.soln",
                )

                self.status = get_status(result)
                self.model_solution = model_instance

                if not is_feasible(self.status):
                    self.solution = Solution({})
                    return get_status_value(self.status)

                log.debug(
                    "Jobs solved: ",
                    loop_jobs,
                    ", nº Slots:",
                    int(value(model_instance.vMaxSlot)),
                    ", time (s):",
                    result.solver.system_time,
                )

                previous_instance = model_instance

                end_solve = time.time()

        # Solve complete problem with warmstart
        time_left = options["timeLimit"] - (time.time() - start_time)
        options["timeLimit"] = time_left
        log.debug("Time left (s)", time_left)
        log.debug("Solve complete problem with warmstart")
        model = get_assign_tasks_model()
        data, max_duration_new_job, mode_max_duration = self.get_input_data(
            jobsToSolve=len(listJobs), previusSlots=value(previous_instance.vMaxSlot)
        )

        model_instance = model.create_instance(data)
        # Check input
        v01Start = dict()
        v01End = dict()
        v01JobDone = dict()
        v01JobMode = dict()

        # Initialize previous solution
        for j in previous_instance.sJobs:
            for s in previous_instance.sSlots:
                if s <= model_instance.sSlots[-1]:
                    model_instance.v01Start[j, s].value = int(
                        value(previous_instance.v01Start[j, s])
                    )
                    model_instance.v01End[j, s].value = int(
                        value(previous_instance.v01End[j, s])
                    )

                    v01Start[j, s] = int(value(previous_instance.v01Start[j, s]))
                    v01End[j, s] = int(value(previous_instance.v01End[j, s]))

                    for m in model_instance.sModes:
                        if (j, m) in self.fixed_jobs_modes:
                            if self.fixed_jobs_modes[j, m] == 1:
                                model_instance.v01JobDone[j, s, m].value = int(
                                    value(previous_instance.v01JobDone[j, s])
                                )
                                model_instance.v01JobMode[j, m].value = 1

                                v01JobDone[j, s, m] = int(
                                    value(previous_instance.v01JobDone[j, s])
                                )
                                v01JobMode[j, m] = 1

        # WarmStart
        opt.options.update(options["SOLVER_PARAMETERS"])
        write_cbc_warmstart_file("./cbc_warmstart.soln", model_instance, opt)
        result = opt.solve(
            model_instance,
            tee=debug,
            warmstart=True,
            warmstart_file="./cbc_warmstart.soln",
        )

        log.debug(
            "Jobs solved: ",
            loop_jobs,
            ", nº Slots:",
            int(value(model_instance.vMaxSlot)),
            ", time (s):",
            result.solver.system_time,
        )
        log.debug("Finish")

        self.status = get_status(result)
        self.model_solution = model_instance

        log.debug(
            "End of solver. Total time:  %.2f seconds" % (time.time() - start_time)
        )
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
                if value(instance.v01Start[j, s]) == 1:
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
            final[j].update(
                {"period": int(dict_start[j]), "mode": int(mode_no_denso[j])}
            )
        return final
