import pytups as pt
import os
from .instance import Instance
from .solution import Solution


class Experiment(object):

    def __init__(self, instance, solution):
        self.instance = instance
        self.solution = solution
        return

    @classmethod
    def from_json(cls, path, inst_file='input.json', sol_file='output.json'):
        instance = Instance.from_json(os.path.join(path, inst_file))
        solution = Solution.from_json(os.path.join(path, sol_file))
        return Experiment(instance, solution)

    def solve(self, options):
        raise NotImplementedError("complete this!")

    def check_solution(self, list_tests=None, **params):
        func_list = dict(
            successors = self.check_successors,
            resources = self.check_resources,
            all_jobs_once = self.all_jobs_once,
        )
        if list_tests is None:
            list_tests = func_list.keys()
        result = {k: func_list[k](**params) for k in list_tests}
        return pt.SuperDict({k: v for k, v in result.items() if v})

    def check_successors(self, **params):
        succ = self.instance.data['jobs'].get_property('successors')
        durations = self.instance.data['durations']
        solution = self.solution.data.to_dictup().to_tuplist().\
            to_dict(result_col=2, indices=[1, 0], is_list=False).\
            to_dictdict()
        sol_start = solution['period']
        sol_mode = solution['mode']
        sol_finished = sol_start.kvapply(lambda k, v: v + durations[k][sol_mode[k]])
        errors = pt.SuperDict()
        for job, post_jobs in succ.items():
            for job2 in post_jobs:
                if sol_finished[job] > sol_start[job2]:
                    errors[job, job2] = sol_finished[job] - sol_start[job2]
        return errors

    def check_resources_nonrenewable(self, **params):
        sol_mode = self.get_modes()
        usage = self.instance.data['needs']
        resource_usage = sol_mode.kvapply(lambda k, v: usage[k][v])
        avail = self.instance.data['resources'].get_property('available')
        renewable_res = avail.kfilter(lambda k: k[0]=='R').keys()
        resource_usage_N = resource_usage.to_dictup().to_tuplist().to_dict(result_col=2, indices=[1]).vapply(sum)
        # TODO types should be in input data
        error_N = \
            resource_usage_N.kfilter(lambda k: k not in renewable_res).\
            kvapply(lambda k, v: avail[k] - v).\
            vfilter(lambda v: v < 0)
        return error_N

    def check_resources_renewable(self, **params):
        sol_mode = self.get_modes()
        usage = self.instance.data['needs']
        resource_usage = sol_mode.kvapply(lambda k, v: usage[k][v])
        avail = self.instance.data['resources'].get_property('available')
        renewable_res = avail.kfilter(lambda k: k[0]=='R').keys()
        sol_start = self.get_start_times()
        sol_finished = self.get_finished_times()
        job_periods = sol_start.sapply(func=range, other=sol_finished)
        # TODO types should be in input data
        makespan = self.get_objective()
        consumption_rt = \
            pt.SuperDict({(r, t): 0 for r in renewable_res for t in range(makespan+1)})
        for job, periods in job_periods.items():
            for period in periods:
                # print(period)
                # print(job)
                for resource, value in resource_usage[job].items():
                    if resource in renewable_res:
                        consumption_rt[resource, period] += value
        errors_R = consumption_rt.kvapply(lambda k, v: avail[k[0]] - v).vfilter(lambda v: v < 0)
        return errors_R

    def get_objective(self, **params):
        return max(self.get_finished_times().values())

    def all_jobs_once(self, **params):
        missing = self.instance.data['jobs'].keys() - self.solution.data.keys()
        return pt.SuperDict({k: 1 for k in missing})

    def get_start_times(self):
        return self.solution.data.get_property('period')

    def get_modes(self):
        return self.solution.data.get_property('mode')

    def get_finished_times(self):
        sol_start = self.get_start_times()
        sol_mode = self.solution.data.get_property('mode')
        durations = self.instance.data['durations']
        return sol_start.kvapply(lambda k, v: v + durations[k][sol_mode[k]])
