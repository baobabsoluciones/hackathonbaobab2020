import pytups as pt
import os
from .instance import Instance
from .solution import Solution
from . import tools as di


class Experiment(object):

    def __init__(self, instance, solution):
        self.instance = instance
        self.solution = solution
        return

    @classmethod
    def from_json(cls, path, inst_file='input.json', sol_file='output.json'):
        instance = Instance.from_json(os.path.join(path, inst_file))
        if os.path.exists(os.path.join(path, sol_file)):
            solution = Solution.from_json(os.path.join(path, sol_file))
        else:
            solution = None
        return cls(instance, solution)

    @classmethod
    def from_zipped_json(cls, zipobj, path, inst_file='input.json', sol_file='output.json'):
        instance = di.load_data_zip(zipobj, os.path.join(path, inst_file))
        instance = Instance.from_dict(instance)
        try:
            solution = di.load_data_zip(zipobj, os.path.join(path, sol_file))
            solution = Solution.from_dict(solution)
        except:
            solution = None
        return cls(instance, solution)
    
    def solve(self, options):
        raise NotImplementedError("complete this!")
    
    def check_solution(self, list_tests=None, **params):
        func_list = dict(
            successors = self.check_successors,
            resources_nr = self.check_resources_nonrenewable,
            resources_r=self.check_resources_renewable,
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
        # non renewables are counted once per job
        sol_mode = self.get_modes()
        usage = self.instance.data['needs']
        resource_usage = sol_mode.kvapply(lambda k, v: usage[k][v])
        avail = self.instance.data['resources'].get_property('available')
        renewable_res = self.instance.get_renewable_resources()
        resource_usage_N = resource_usage.to_dictup().to_tuplist().to_dict(result_col=2, indices=[1]).vapply(sum)
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
        renewable_res = self.instance.get_renewable_resources()
        sol_start = self.get_start_times()
        sol_finished = self.get_finished_times()
        job_periods = sol_start.sapply(func=range, other=sol_finished)
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

    def graph(self):
        try:
            import plotly as pt
            import plotly.figure_factory as ff
        except ImportError:
            print("You need plotly to be able to plot!")

        import plotly.express as px
        input_data = self.instance.data
        all_durations = input_data['durations']
        jobs_data = input_data['jobs'].keys_tl()

        output_data = self.solution.data
        start = output_data.get_property('period')
        mode = output_data.get_property('mode')
        duration = jobs_data.to_dict(None).kapply(lambda k: all_durations[k][mode[k]])

        color_per_mode = ['#4cb33d', '#00c8c3', '#31c9ff', '#878787', '#EFCC00']
        colors = mode.vapply(lambda v: color_per_mode[v-1])
        transf = lambda k, v: dict(Task=k, Start=start[k],
                                   Finish=start[k]+v, Label=str(k), Mode=mode[k])
        gantt_data = duration.kvapply(transf).values_tl()


        filename = 'temp.html'
        options = dict(show_colorbar=True, showgrid_x=True, title="Jobs!",
                       bar_width=0.5, width=2000, height=1000)
        # fig = px.timeline(gantt_data, x_start="Start", x_end="Finish", y="Task", color='Mode')
        # fig.update_xaxes()
        fig = ff.create_gantt(gantt_data, colors=colors, index_col='Task', **options)
        fig['layout'].update(autosize=True, margin=dict(l=150), xaxis=dict(type='linear'))
        fig.update_yaxes(autorange="reversed")  # otherwise tasks are listed from the bottom up
        # for i in range(len(gantt_data)):
        #     # task = gantt_data[i]['Resource']
        #     mode = gantt_data[i]['Mode']
        #     task = gantt_data[i]['Task']
        #     text = 'job:{}<br>mode: {}'.format(task, mode)
        #     fig["data"][i].update(text=text, hoverinfo="text")
        fig.show()

        # for i in gantt_data:
        #     x_pos = (i['Finish'] - i['Start']) / 2 + i['Start']
        #     [j['name'] for j in fig['data']] #if (j['name'] == i['Task'])]
        #     for j in :
        #         :
        #             y_pos = (j['y'][0] + j['y'][1] + j['y'][2] + j['y'][3]) / 4
        #         fig['layout']['annotations'] += tuple([dict(x=x_pos, y=y_pos, text=i['Label'], font={'color':'black'})])

        # pt.offline.plot(fig, filename=filename, show_link=False, config=dict(responsive=True))