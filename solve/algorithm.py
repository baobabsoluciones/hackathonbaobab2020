
from core.model import get_model
from pyomo.environ import SolverFactory, value
from core import Experiment, Solution


class Algorithm(Experiment):

    def __init__(self, instance, solution=None):
        if solution is None:
            solution = {}
        super().__init__(instance, solution)
        return

    def solve(self, options):
        model = get_model()
        data = self.instance.get_input_data()
        print(data)
        model_instance = model.create_instance(data, report_timing=True)
        opt = SolverFactory('cbc')
        result = opt.solve(model_instance, tee=True)
        
        self.status = str(result.solver.termination_condition)
        self.model_solution = model_instance
        print(self.status)
        #self.model_solution.display()
        if self.status == "optimal":
            self.print_instance()
            
        data = self.format_solution()
        
        self.solution = Solution(data)
        
        return self.solution
    
    def print_instance(self):
        print("printing instance")
        with open("instance_display.txt", "w") as f:
            self.model_solution.display(ostream=f)
    pass
    
    def format_solution(self):
        
        instance = self.model_solution
        dict_start = var_to_dict(instance.vStart)
        dict_mode = var_to_dict(instance.v01Mode)
        set_jobs = [i for i in instance.sJobs]
        
        print(dict_start)
        print(dict_mode)
        print(set_jobs)
        
        mode_no_denso = dict()
        for a, b in dict_mode.keys():
            if dict_mode[a, b] == 1:
                mode_no_denso.update({a: b})
        
        if len(mode_no_denso)==0:
            return {}
        
        final = dict()
        for j in set_jobs:
            final[j] = dict()
            final[j].update({'period': dict_start[j], 'mode': mode_no_denso[j]})
        return final
        
        
def var_to_dict(variable):
    """
    Transform a pyomo variable into a python dict
    :param variable: a pyomo variable
    :return: a dict containing the indices and values of the variable.
    """
    return {key: value(variable[key]) for key in variable.keys()}