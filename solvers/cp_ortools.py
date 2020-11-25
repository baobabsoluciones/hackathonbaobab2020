from ortools.sat.python import cp_model
from core.experiment import Experiment
import pytups as pt


class CPModel1(Experiment):

    def __init__(self, instance, solution=None):
        if solution is None:
            solution = {}
        super().__init__(instance, solution)
        return

    def solve(self, options):
        model = cp_model.CpModel()
        horizon = 1000
        input_data = self.instance.data

        starts = pt.SuperDict()
        ends = pt.SuperDict()
        job_duration = pt.SuperDict()
        job_mode = pt.SuperDict()
        interval = pt.SuperDict()
        job_consumption = pt.SuperDict()
        for job in input_data['jobs']:
            id = job
            modes_durations = input_data['durations'][job]
            needs = input_data['needs'][job]
            starts[id] = model.NewIntVar(0, horizon, 'start_{}'.format(id))
            ends[id] = model.NewIntVar(0, horizon, 'end_{}'.format(id))
            job_mode[id] = model.NewIntVar(0, len(modes_durations)-1, 'mode_{}'.format(id))
            job_duration[id] = model.NewIntVar(min(modes_durations.values()), max(modes_durations.values()), 'duration_{}'.format(id))
            # mode_duration = []
            # for mode, dur in modes.items():
            #     mode_duration.append(
            #         model.NewIntVar(dur, dur, 'mode_dur_{}_{}'.format(id, mode))
            #     )
            mode_duration = pt.SuperDict(modes_durations).to_tuplist().sorted(key=lambda x: x[0]).take(1)
            model.AddElement(job_mode[id], mode_duration, job_duration[id])
            interval[id] = model.NewIntervalVar(starts[id], job_duration[id], ends[id], 'interval_{}'.format(id))
            modes_needs = \
                pt.SuperDict(needs).to_dictup().to_tuplist().take([1, 0, 2]).to_dict(2, is_list=False).to_dictdict().\
                    vapply(lambda v: v.to_tuplist().sorted(key=lambda x: x[0]).take(1))
            for res, needs in modes_needs.items():
                # if it does not demand the resource: no point modeling it
                if not max(needs):
                    continue
                job_consumption[id, res] = \
                    model.NewIntVar(min(needs), max(needs), 'consumption_{}_{}'.format(id, res))
                model.AddElement(job_mode[id], needs, job_consumption[id, res])

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
                # renewable resources we only by intervals
                model.AddCumulative(intervals=relevant_intervals, demands=consumptions, capacity=res_data['available'])
            else: # non renewable resources we sum all
                model.Add(sum(consumptions) <= res_data['available'])

        # objective
        obj_var = model.NewIntVar(0, horizon, 'makespan')
        model.AddMaxEquality(obj_var, ends.values())
        model.Minimize(obj_var)

        solver = cp_model.CpSolver()
        status = solver.Solve(model)
        solver.Value(obj_var)




