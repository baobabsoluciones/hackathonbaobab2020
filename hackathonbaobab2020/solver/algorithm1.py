from hackathonbaobab2020.core import Experiment, Solution
import copy
import pytups as pt


class Algorithm(Experiment):

    def __init__(self, instance, solution=None):
        super().__init__(instance, solution)
        return

    def solve(self, options):
        # takes into account successors
        jobs = copy.deepcopy(self.instance.data['jobs'])
        all_jobs = set(jobs.keys())
        solution = pt.SuperDict()
        succ = jobs.get_property('successors')
        durations = self.instance.data['durations']
        needs = self.instance.data['needs']

        # algorithm
        period = 0
        job = 1
        succ.pop(job)
        mode = 1  # we always chose the first mode
        solution[job] = dict(period=period, mode=mode)
        period = period + durations[job][mode]

        while len(succ):
            reverse = succ.list_reverse()
            possible = all_jobs - reverse.keys() - solution.keys()
            for job in possible:
                succ.pop(job)
                solution[job] = dict(period=period, mode=mode)
                period = period + durations[job][mode]
        self.solution = Solution(solution)
        return self.solution
