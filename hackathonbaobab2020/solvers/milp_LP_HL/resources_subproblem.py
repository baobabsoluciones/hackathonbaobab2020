
from pyomo.environ import *
from .configuration import SOLVER_PARAMETERS
from hackathonbaobab2020.solvers.milp_LP_HL.pyomo_utils import is_feasible, get_status, var_to_dict

def get_r_submodel():
    """
    This function creates the pyomo  model.

    :return: a pyomo abstract model
    """
    
    # Create model
    model = AbstractModel()
    
    # Model sets
    model.sJobs = Set()
    model.sResources = Set()
    model.sNResources = Set()
    model.sModes = Set()
    model.sJobsModes = Set(dimen=2)
    
    # General parameters
    model.pResourcesUsed = Param(model.sJobs, model.sResources, model.sModes, mutable=True)
    model.pMaxResources = Param(model.sResources, mutable=True)
    
    # Objective function parameters
    model.pWeightResources = Param(mutable=True)
    
    # Model variables
    model.v01Mode = Var(model.sJobsModes, domain=Binary)
    
    # c9: maximum amount non-renewable resources
    def c9_max_n_resources(model, iResource):
        return sum(model.v01Mode[iJob, iMode] * model.pResourcesUsed[iJob, iResource, iMode]
                   for (iJob, iMode) in model.sJobsModes) <= model.pMaxResources[iResource]
    
    def c12_amount_modes(model, iJob):
        return sum(model.v01Mode[iJob, iMode] for iMode in model.sModes if (iJob, iMode) in model.sJobsModes) == 1
    
    # Objective function
    def obj_expression(model):
        return sum(model.v01Mode[iJob, iMode] * model.pResourcesUsed[iJob, iResource, iMode]
                   for (iJob, iMode) in model.sJobsModes for iResource in model.sNResources)

    # Activate constraints
    model.c9_max_n_resources = Constraint(model.sNResources, rule=c9_max_n_resources)
    model.c12_amount_modes = Constraint(model.sJobs, rule=c12_amount_modes)
    
    # Add objective function
    model.f_obj = Objective(rule=obj_expression, sense=minimize)
    
    return model

def solve_resource_subproblem(input_data):
    
    print("Get a feasible combination of jobs and modes")
    
    model = get_r_submodel()
    
    model_instance = model.create_instance(input_data, report_timing=False)
    opt = SolverFactory('cbc')
    opt.options.update(SOLVER_PARAMETERS)
    result = opt.solve(model_instance, tee=False)

    status = get_status(result)
    print("Status of modes allocation: " + status)
    
    if is_feasible(status):
        used_modes = var_to_dict(model_instance.v01Mode)
        solution = {(j, m) for (j,m) in used_modes if used_modes[(j, m)]}
    else:
        raise Exception("Problem infeasible")
    
    return solution