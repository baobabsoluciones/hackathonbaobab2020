from pyomo.core.expr.current import identify_variables
from hackathonbaobab2020.solvers.milp_LP_HL.pyomo_utils import *
from copy import deepcopy
from hackathonbaobab2020.solvers.milp_LP_HL.function_utils import no_duplicates


class BaseIterator:
    
    def __init__(self, instance, opt, warmstart_file="warmstart.soln", variable_map=None, verbose=False):
        """
        This class is used to solve a pyomo model by successive itarations
        
        :param instance: a pyomo instance
        :param opt: a pyomo solver
        :param variable_map: the variable map to use (see set_variable_map for details)
        :param warmstart_file: specify where to write and read the warmstart file
        :param verbose: if true, all the messages of the sovler will be printed (pyomo tee=True option)

        """
        self.instance = instance
        self.opt = opt
        self.verbose = verbose
        if variable_map is None:
            self.variable_map = {}
        else:
            self.variable_map = variable_map
        self.warmstart_file = warmstart_file
        self.iteration = {}
        
    def set_variable_map(self, new_map):
        """
        Set a new variable map.
        A variable map is a dict of the name of the variables that should be fixed and their indices.
        The indices are a list of set names in the same order as in the variable.
        It is important to always give the same names to the indices which will be iterated over. The other set names
        do not matter.
        
        map_example = {
        "vVar1":["sSet1", "sSet2", "sOtherSet"]
        "vVar2":["sSet1"]
        }
        
        At each iteration, the variables containing one of the free index will be free and the one containing
         fixed index will be fixed.
        
        :param new_map: the new variable_map
        """
        self.variable_map = new_map
    
    def get_free_keys(self, var_name, free_indices, fixed_indices):
        """
        Get all the keys (combinations of indices) of a variable that should be free.
        
        :param var_name: name of the variable
        :param free_indices: dict of free indices
        :param fixed_indices:  dict of fixed indices
        :return: a lis of keys that should be free
        """
        var_indices = self.variable_map[var_name]
        variable = self.get_variable(var_name)
        var_dim = len(var_indices)
        all_indices = [[] for i in range(var_dim)]
        indices_to_free = [[] for i in range(var_dim)]
        free_keys = []
        for i in range(var_dim):
            if var_indices[i] in free_indices.keys():
                indices_to_free[i] = free_indices[var_indices[i]]
                all_indices[i] = free_indices[var_indices[i]] + fixed_indices[var_indices[i]]
            else:
                indices_to_free[i] = []
                all_indices[i] = no_duplicates([k[i] for k in variable.keys()])
        
        for i in range(var_dim):
            combinations = deepcopy(all_indices)
            combinations[i] = indices_to_free[i]
            free_keys += existing_indices(variable, *combinations)
            
        return free_keys
    
    def set_variables_states(self, free_indices, fixed_indices):
        """
        Set the variables as fixed or free depending on their indices and the dicts of free and fixed indices.
        If a variable depends on multiple sets of free/fixed indices, the following rule apply:
        - free * free = free
        - free * fixed = free
        - fixed * fixed = fixed
        - free * ignored = fixed
        - fixed * ignored = fixed
        - ignored * ignored = fixed
        
        :param free_indices: indices that will be free in that iterations.
        :param fixed_indices: indices that have already been fixed in previous iterations.
        :return:
        """
        
        fix_variable_list([self.get_variable(v) for v in self.variable_map])
        free_keys = {}
        
        for var_name in self.variable_map:
            free_keys[var_name] = self.get_free_keys(var_name, free_indices, fixed_indices)
            free_variable(self.get_variable(var_name), free_keys[var_name])
        
        return free_keys

    def get_variable(self, var_name):
        """
        Transform a variable name into the corresponding pyomo variable object.

        :param var_name: the variable name
        :return: the pyomo variable object
        """
        return self.instance.__dict__[var_name]
    
    def get_constraint(self, con_name):
        """
        Transform a constraint name into the corresponding pyomo constraint object
        
        :param con_name: the constraint name
        :return: the pyomo constraint object
        """
        return self.instance.__dict__[con_name]
    
    def get_instance_constraint_list(self):
        """
        :return: The list of constraints from the instance.
        """
        return [self.get_constraint(con) for con in self.instance.component_map(Constraint)]
    
    def get_instance_var_list(self):
        """
        :return: The list of variables from the instance.
        """
        return [self.get_variable(v) for v in self.instance.component_map(Var)]
    
    def deactivate_unused_constraints(self, exclude=None):
        """
        Detect fixed constraints indices (all their variable are fixed) and deactivate them.
        
        :param exclude a list of constraint names not to activate.
        
        :return: nothing (modify the instance)
        """
        if exclude is not None:
            dont_activate = [self.get_constraint(e) for e in exclude]
        else:
            dont_activate = []
        
        constraint_list = self.get_instance_constraint_list()
        for const in constraint_list:
            if const not in dont_activate:
                activate_constraint(const)
                for k in const.keys():
                    if len(list(identify_variables(const[k].body, include_fixed=False))) == 0:
                        const[k].deactivate()
    
    def set_var_initial_values(self, var_values=None):
        """
        Set all the variables to 0 or to an optional value.
        var_values is optional and must have the following format:
        var_values = {
            "vVar1": {(0, 0): 1, (0, 1): 1},
            "vVar2": {(0, 0): 1, (0, 3): 1}
        }
        Variables and indices not in var_values will be set to 0.
        
        :param var_values: a dict with variables names, indices and values (optional)
        :return: nothing (update the instance values)
        """
        var_list = self.get_instance_var_list()
        for v in var_list:
            for k in v.keys():
                v[k] = 0
                
        if var_values is not None:
            for v_name in var_values.keys():
                v = self.get_variable(v_name)
                for k, val in var_values[v_name].items():
                    v[k] = val
    
    def free_everything(self):
        """
        Free all the variables and activate all the constraints
        """
        all_var = self.get_instance_var_list()
        all_con = self.get_instance_constraint_list()
        free_variable_list(all_var)
        activate_constraint_list(all_con)
    
    def show_solution(self, free_keys):
        """
        Show the solution for the variables and keys that were free in this iteration.
        Only show non zero values.
        
        :param free_keys: a dict in the format: free_keys = {"var_name":[list of free keys], var_name2"...}
        :return:
        """
        print("Values for free variables are:")
        for var_name in free_keys.keys():
            print(var_name)
            v = self.get_variable(var_name)
            for k in free_keys[var_name]:
                if value(v[k]) != 0:
                    print(k, value(v[k]))

    def solve(self):
        """
        Solve the problem with a warmstart.
        
        :return: resolution status and objective function.
        """
    
        write_cbc_warmstart_file(self.warmstart_file, self.instance, self.opt)
        result = self.opt.solve(self.instance, tee=self.verbose, warmstart=True,
                                warmstart_file=self.warmstart_file)
        status = get_status(result)
        obj = self.instance.f_obj()
    
        return status, obj
    
    def iterate(self, free_indices, fixed_indices, excluded_constraints=None):
        """
        Iterate one time with the given free and fixed indices.
        Free and fixed indices may include several sets and must include exactly the same sets.
        
        free_indices_example = {
            "sSet1": [4,5,6],
            "sSet2": [10,11,12]
        }
        
        The indices which are not in free or fixed indices are ignored for the given sets (they always stay fixed)
        
        If a variable depends on multiple sets of free/fixed indices, the following rule apply:
        - free * free = free
        - free * fixed = free
        - fixed * fixed = fixed
        - free * ignored = fixed
        - fixed * ignored = fixed
        - ignored * ignored = fixed
        
        :param free_indices: indices that will be free in that iterations.
        :param fixed_indices: indices that have already been fixed in previous iterations.
        :return: (tuple) status and obj of the resolution.
        """
        free_keys = self.set_variables_states(free_indices, fixed_indices)
        self.deactivate_unused_constraints(exclude=excluded_constraints)

        status, obj = self.solve()
        #self.show_solution(free_keys)
        
        return status, obj
    
    
    # Work in progress:
    """
    def get_iterative_solution(self, complete_sets, iter_rule_dict=None):
        
        chrono = Chrono("construction of a first solution", silent = False)
        
        free_indices = {s:[] for s in complete_sets.keys()}
        fixed_indices = {s:[] for s in complete_sets.keys()}
        free_indices, fixed_indices = self.update_indices(free_indices, fixed_indices, iter_rule_dict, complete_sets)
        i = 0
        self.iteration = {}
        
        while any(len(s)>0 for s in free_indices.values()):
            print("iteration ", i)
            print("free indices ", free_indices)
            self.iteration[i] = self.iterate(free_indices, fixed_indices)
            free_indices, fixed_indices = self.update_indices(free_indices, fixed_indices, iter_rule_dict, complete_sets)
            chrono.time()
            i += 1
        
        chrono.stop()
        
    def update_indices(self, free_indices, fixed_indices, iter_rule_dict, complete_sets):
        for s in iter_rule_dict.keys():
            rule=iter_rule_dict[s]
            free_indices[s], fixed_indices[s] = rule(free_indices[s], fixed_indices[s], complete_sets[s])
        return free_indices, fixed_indices
    
    def additive_iteration(self, free_indices, fixed_indices, complete_set, k=10):
        fixed_indices += free_indices
        candidates = [i for i in complete_set if i not in fixed_indices]
        free_indices = candidates[0:min(k, len(candidates))]
        return free_indices, fixed_indices
    
    def random_iterate(self, var_name):
        print("not implemented yet")
        pass
    
    def iterate_during(self, t):
        chrono = Chrono("improving solution during %s sec" % t)
        print("not implemented yet")
        pass
    """
        
        