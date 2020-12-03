from pyomo.environ import *
import pyomo.environ as pyo
from core import Experiment, Solution
from core.tools import write_cbc_warmstart_file
import copy
import pytups as pt


class Model(Experiment):

    def __init__(self, instance, algorithm=None, solution=None):
        super().__init__(instance, solution)
        self.formatted_data = {}
        self.algorithm = algorithm
        self.initial_solution = None

    def solve(self, options):
        model = self.get_model()
        self.prepare_data()
        self.initial_solution = self.algorithm.solve({})
        print(self.initial_solution.data)
        #
        self.milp_instance = model.create_instance(self.formatted_data, report_timing=True)
        self.initialize_solution()
        opt = pyo.SolverFactory('gurobi')
        # write_cbc_warmstart_file("./cbc_warmstart.soln", self.milp_instance, opt)

        config = dict()
        config["parameters_model"] = {"sec": 300, "allow": 0, "ratio": 0.01, "primalT": 10 ** -7}
        opt.options.update(config["parameters_model"])
        # self.result = opt.solve(self.milp_instance, tee=True, warmstart=True, warmstart_file="./cbc_warmstart.soln")
        self.result = opt.solve(self.milp_instance, tee=True, warmstart=True)
        print(self.result)
        self.solution = Solution(self.format_solution())
        print(self.solution.data)
        return self.result

    def prepare_data(self):
        self.formatted_data['sTasks'] = {None: [i for i in self.instance.data['jobs']]}

        self.formatted_data['sModes'] = {None: [i for i in range(1, 4)]}
        self.formatted_data['sRenewableResources'] = {None: [i for i in self.instance.data['resources'] if 'R' in i]}
        self.formatted_data['sNotRenewableResources'] = {None: [i for i in self.instance.data['resources'] if 'N' in i]}

        aux_list = list()
        for t1 in self.instance.data['jobs']:
            if len(self.instance.data['jobs'][t1]['successors']) > 0:
                for t2 in self.instance.data['jobs'][t1]['successors']:
                    aux_list.append((t1, t2))

        self.formatted_data['sTasks_Tasks'] = {None: aux_list}

        aux_dict = dict()
        p_max_duration = 0
        for t in self.instance.data['durations']:
            p_max_duration += self.instance.data['durations'][t][1]
            for k in self.instance.data['durations'][t]:
                aux_dict[(t, k)] = self.instance.data['durations'][t][k]

        self.formatted_data['sTime'] = {None: [i for i in range(p_max_duration + 1)]}
        self.formatted_data['sTime_Time_One'] = {None: [(i, i + 1) for i in range(p_max_duration)]}
        self.formatted_data['pTime'] = {i: i for i in range(p_max_duration + 1)}

        aux_dict[(min([i for i in self.instance.data['jobs']]), 2)] = 0
        aux_dict[(min([i for i in self.instance.data['jobs']]), 3)] = 0
        aux_dict[(max([i for i in self.instance.data['jobs']]), 2)] = 0
        aux_dict[(max([i for i in self.instance.data['jobs']]), 3)] = 0

        self.formatted_data['pDuration'] = aux_dict

        self.formatted_data['pCapacityRenewableResource'] = {r: self.instance.data['resources'][r]['available']
                                                             for r in self.instance.data['resources'] if 'R' in r}

        self.formatted_data['pNeedsRenewableResources'] = \
            {(t, m, r): self.instance.data['needs'][t][m][r] for t in self.instance.data['needs']
             for m in self.instance.data['needs'][t] for r in self.instance.data['needs'][t][m] if 'R' in r}

        self.formatted_data['pCapacityNotRenewableResource'] = {r: self.instance.data['resources'][r]['available']
                                                                for r in self.instance.data['resources'] if 'N' in r}

        self.formatted_data['pNeedsNotRenewableResources'] = \
            {(t, m, r): self.instance.data['needs'][t][m][r] for t in self.instance.data['needs']
             for m in self.instance.data['needs'][t] for r in self.instance.data['needs'][t][m] if 'N' in r}

        self.formatted_data = {None: self.formatted_data}

    def format_solution(self):
        temp_solution = dict()
        start_time = 0
        mode = 0
        for i in self.milp_instance.sTasks:
            for j in self.milp_instance.sTime:
                if pyo.value(self.milp_instance.v01Start[i, j]) > 0:
                    start_time = j

            for j in self.milp_instance.sModes:
                if pyo.value(self.milp_instance.v01Mode[i, j]) > 0:
                    mode = j

            temp_solution[i] = dict(period=start_time, mode=mode)

        return temp_solution

    def get_model(self, initial=True):
        model = AbstractModel()

        model.sTasks = Set()
        model.sModes = Set()
        model.sRenewableResources = Set()
        model.sNotRenewableResources = Set()
        model.sTime = Set()

        model.sTasks_Tasks = Set(dimen=2)  # tasks pairs with precedence
        model.sTime_Time_One = Set(dimen=2)  # time pairs with one diference

        model.v01Start = Var(model.sTasks, model.sTime, domain=Binary)
        model.v01End = Var(model.sTasks, model.sTime, domain=Binary)
        model.v01Active = Var(model.sTasks, model.sTime, model.sModes, domain=Binary)
        model.v01Mode = Var(model.sTasks, model.sModes, domain=Binary)
        model.vFinishTime = Var(domain=NonNegativeReals)

        model.pTime = Param(model.sTime, mutable=True)
        model.pDuration = Param(model.sTasks, model.sModes, mutable=True)
        model.pCapacityRenewableResource = Param(model.sRenewableResources, mutable=True)
        model.pNeedsRenewableResources = Param(model.sTasks, model.sModes, model.sRenewableResources, mutable=True)
        model.pCapacityNotRenewableResource = Param(model.sNotRenewableResources, mutable=True)
        model.pNeedsNotRenewableResources = Param(model.sTasks, model.sModes, model.sNotRenewableResources,
                                                  mutable=True)

        def c1_start_before_end(model, iTask):
            return sum(model.v01Start[iTask, iTime] * model.pTime[iTime] for iTime in model.sTime) <= \
                   sum(model.v01End[iTask, iTime] * model.pTime[iTime] for iTime in model.sTime)

        def c2_always_start(model, iTask):
            return sum(model.v01Start[iTask, iTime] for iTime in model.sTime) == 1

        def c3_always_end(model, iTask):
            return sum(model.v01End[iTask, iTime] for iTime in model.sTime) == 1

        def c4_active_duration(model, iTask):
            return sum(model.v01Active[iTask, iTime, iModes] for iTime in model.sTime for iModes in model.sModes) == \
                   sum(model.pDuration[iTask, iMode] * model.v01Mode[iTask, iMode] for iMode in model.sModes)

        def c5_start(model, iTask, iTime1, iTime2):
            return sum(model.v01Active[iTask, iTime2, iMode] for iMode in model.sModes) <= \
                   sum(model.v01Active[iTask, iTime1, iMode] for iMode in model.sModes) + model.v01Start[iTask, iTime2]

        def c6_end(model, iTask, iTime1, iTime2):
            return sum(model.v01Active[iTask, iTime1, iMode] for iMode in model.sModes) <= \
                   sum(model.v01Active[iTask, iTime2, iMode] for iMode in model.sModes) + model.v01End[iTask, iTime1]

        def c7_preference(model, iTask1, iTask2):
            # if iTask1 == min(model.sTasks) or iTask2 == max(model.sTasks):
            #     return sum(model.v01End[iTask1, iTime] * model.pTime[iTime] for iTime in model.sTime) <= \
            #            sum(model.v01Start[iTask2, iTime] * model.pTime[iTime] for iTime in model.sTime)
            # else:
            return sum(model.v01Start[iTask1, iTime] * model.pTime[iTime] for iTime in model.sTime) + \
                   sum(model.pDuration[iTask1, iMode] * model.v01Mode[iTask1, iMode] for iMode in model.sModes) <= \
                   sum(model.v01Start[iTask2, iTime] * model.pTime[iTime] for iTime in model.sTime)

        def c8_finish_time(model, iTask, iTime):
            return model.vFinishTime >= model.v01End[iTask, iTime] * model.pTime[iTime]

        def c9_select_mode(model, iTask):
            return sum(model.v01Mode[iTask, iMode] for iMode in model.sModes) == 1

        def c10_one_mode(model, iTask, iMode):
            return model.v01Mode[iTask, iMode] * model.pDuration[iTask, iMode] == sum(
                model.v01Active[iTask, iTime, iMode] for iTime in model.sTime)

        def c11_renewable_resource_capacity(model, iTime, iResource):
            return sum(model.v01Active[iTask, iTime, iMode] * model.pNeedsRenewableResources[iTask, iMode, iResource]
                       for iTask in model.sTasks if iTask != min(model.sTasks) and iTask != max(model.sTasks) for iMode
                       in model.sModes) <= \
                   model.pCapacityRenewableResource[iResource]

        def c13_not_renewable_resource_capacity(model, iResource):
            return sum(model.v01Mode[iTask, iMode] * model.pNeedsNotRenewableResources[iTask, iMode, iResource]
                       for iTask in model.sTasks if iTask != min(model.sTasks) and iTask != max(model.sTasks) for iMode
                       in model.sModes) <= \
                   model.pCapacityNotRenewableResource[iResource]

        def obj_expression(model):
            return model.vFinishTime

        model.c1_start_before_end = Constraint(model.sTasks, rule=c1_start_before_end)
        model.c2_always_start = Constraint(model.sTasks, rule=c2_always_start)
        model.c3_always_end = Constraint(model.sTasks, rule=c3_always_end)
        model.c4_active_duration = Constraint(model.sTasks, rule=c4_active_duration)
        model.c5_start = Constraint(model.sTasks, model.sTime_Time_One, rule=c5_start)
        model.c6_end = Constraint(model.sTasks, model.sTime_Time_One, rule=c6_end)
        model.c7_preference = Constraint(model.sTasks_Tasks, rule=c7_preference)
        model.c8_finish_time = Constraint(model.sTasks, model.sTime, rule=c8_finish_time)
        model.c9_select_mode = Constraint(model.sTasks, rule=c9_select_mode)
        model.c10_one_mode = Constraint(model.sTasks, model.sModes, rule=c10_one_mode)
        model.c11_renewable_resource_capacity = Constraint(model.sTime, model.sRenewableResources,
                                                           rule=c11_renewable_resource_capacity)
        model.f_obj = Objective(rule=obj_expression, sense=minimize)
        model.c13_not_renewable_resource_capacity = Constraint(model.sNotRenewableResources,
                                                               rule=c13_not_renewable_resource_capacity)

        return model

    def initialize_solution(self):

        # model.v01Start[Job, time]
        # model.v01End[Job, time]
        # model.v01Active[Job, time, mode]
        # model.v01Mode[Job, mode]
        # model.vFinishTime
        final_end = 0
        for i in self.initial_solution.data:
            mode = self.initial_solution.data[i]['mode']
            start = self.initial_solution.data[i]['period']
            end = start + self.milp_instance.pDuration[i, mode].value - 1
            if end < 0:
                end = 0
            elif end < start:
                end = start
            if end > final_end:
                final_end = end
            self.milp_instance.v01Start[i, start].value = 1
            self.milp_instance.v01End[i, end].value = 1

            for x in range(start, end + 1):
                self.milp_instance.v01Active[i, x, mode].value = 1

            self.milp_instance.v01Mode[i, mode].value = 1
        self.milp_instance.vFinishTime.value = final_end
