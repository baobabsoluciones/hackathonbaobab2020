from ortools.sat.python import cp_model
from hackathonbaobab2020.core import Experiment, Solution
import pytups as pt


class CPModel1(Experiment):

    def __init__(self, instance, solution=None):
        super().__init__(instance, solution)
        return

    def solve(self, options):
        model = cp_model.CpModel()
        input_data = pt.SuperDict.from_dict(self.instance.data)
        max_dur_job = input_data['durations'].vapply(lambda v: max(v.values()))
        horizon = sum(max_dur_job) + 1
        jobs_data = input_data['jobs']
        durations_data = pt.SuperDict.from_dict(input_data['durations'])
        needs_data = pt.SuperDict.from_dict(input_data['needs'])
        mode_dictionary_to_values = lambda v: v.to_tuplist().sorted(key=lambda x: x[0]).take(1)

        # variable declaration:
        starts = pt.SuperDict({job: model.NewIntVar(0, horizon, 'start_{}'.format(job)) for job in jobs_data})
        ends = pt.SuperDict({job: model.NewIntVar(0, horizon, 'end_{}'.format(job)) for job in jobs_data})
        job_mode = pt.SuperDict({job: model.NewIntVar(0, len(modes) - 1, 'mode_{}'.format(job))
                                 for job, modes in durations_data.items()})
        job_duration = pt.SuperDict({job: model.NewIntVar(min(modes.values()), max(modes.values()), 'duration_{}'.format(job))
                                     for job, modes in durations_data.items()})
        interval = pt.SuperDict({job: model.NewIntervalVar(starts[job], job_duration[job], ends[job], 'interval_{}'.format(job))
                                 for job in jobs_data})
        mode_duration_perjob = durations_data.vapply(mode_dictionary_to_values)
        # definition of job duration
        [model.AddElement(job_mode[job], mode_duration_perjob[job], job_duration[job]) for job in jobs_data]

        # for each job and resource:
        # an array of consumptions (one per mode in order)
        needs_data_perjob = \
            needs_data. \
                to_dictup(). \
                to_tuplist(). \
                take([0, 2, 1, 3]). \
                to_dict([2, 3]). \
                vapply(sorted). \
                vapply(pt.TupList).vapply(lambda v: v.take(1))

        # for each job and resource:
        # a variable with the consumption
        job_consumption = needs_data_perjob.kvapply(
            lambda k, v: model.NewIntVar(min(v), max(v), 'consumption_{}_{}'.format(*k))
        )
        # definition of job consumption
        for (job, res), needs in needs_data_perjob.items():
            model.AddElement(job_mode[job], needs, job_consumption[job, res])

        # succession needs to be guaranteed
        for job, job_data in input_data['jobs'].items():
            for successor in job_data['successors']:
                model.Add(starts[successor] >= ends[job])

        # resource usage
        job_consumption_per_res = job_consumption.to_tuplist().take([1, 0, 2]).to_dict(2, is_list=False).to_dictdict()
        for resource, res_data in input_data['resources'].items():
            # we get jobs that consume that resource and how much
            jobs, consumptions = zip(*job_consumption_per_res[resource].items_tl())
            relevant_intervals = [interval[j] for j in jobs]
            if resource in self.instance.get_renewable_resources():
                # renewable resources we use intervals to check them
                model.AddCumulative(intervals=relevant_intervals, demands=consumptions, capacity=res_data['available'])
            else: # non renewable resources we sum all
                model.Add(sum(consumptions) <= res_data['available'])

        # we set the objective as the makespan
        obj_var = model.NewIntVar(0, horizon, 'makespan')
        model.AddMaxEquality(obj_var, ends.values())
        model.Minimize(obj_var)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = options.get('timeLimit', 10)
        status = solver.Solve(model)
        if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            return status
        start_sol = starts.vapply(solver.Value)
        mode_sol = job_mode.vapply(lambda v: solver.Value(v) + 1)
        _func = lambda x, y: dict(period=x, mode=y)
        solution = start_sol.sapply(func=_func, other=mode_sol)
        self.solution = Solution(solution)
        return status





