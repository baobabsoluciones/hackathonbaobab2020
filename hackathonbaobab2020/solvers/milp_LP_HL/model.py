"""

Optimization model

"""

import pyomo
import pyomo.opt
from pyomo.environ import *

def get_model():
    """
    This function creates the pyomo  model.
    
    :return: a pyomo abstract model
    """
    
    # Create model
    model = AbstractModel()
    
    # Model sets
    model.sJobs = Set()
    model.sResources = Set()
    model.sRResources = Set()
    model.sNResources = Set()
    model.sModes = Set()
    model.sPeriods = Set()
    model.sJobsPrecedence = Set(dimen=2)
    model.sJobsModes = Set(dimen=2)
    
    # General parameters
    model.pResourcesUsed = Param(model.sJobs, model.sResources, model.sModes, mutable=True)
    model.pDuration = Param(model.sJobs, model.sModes, mutable=True)
    model.pMaxResources = Param(model.sResources, mutable=True)
    
    # Objective function parameters
    model.pWeightResources = Param(mutable=True)
    model.pWeightMakespan = Param(mutable=True)
    
    # Model variables
    model.v01Start = Var(model.sJobs, model.sPeriods, domain=Binary)
    model.v01End = Var(model.sJobs, model.sPeriods, domain=Binary)
    model.v01Work = Var(model.sJobs, model.sPeriods, domain=Binary)
    model.v01Mode = Var(model.sJobsModes, domain=Binary)
    model.vStart = Var(model.sJobs, domain=NonNegativeReals)
    model.vEnd = Var(model.sJobs, domain=NonNegativeReals)
    model.vResources = Var(model.sRResources, model.sJobs, model.sPeriods, domain=NonNegativeReals)
    model.vMakespan = Var(domain=NonNegativeReals)
    model.vSlack = Var(model.sJobs, domain=NonNegativeReals)
    
    
    # Constraints
    # c1:
    def c1a_start_consistency(model, iJob):
        return model.vStart[iJob] == sum(model.v01Start[iJob, iPeriod] * int(iPeriod) for iPeriod in model.sPeriods)
    
    def c1b_end_consistency(model, iJob):
        return model.vEnd[iJob] == sum(model.v01End[iJob, iPeriod] * int(iPeriod) for iPeriod in model.sPeriods)
    
    # c2:
    def c2_start_work_relation(model, iJob, iPeriod):
        return model.v01Start[iJob, iPeriod] <= model.v01Work[iJob, iPeriod]
    
    # c3:
    def c3_amount_starts(model, iJob):
        return sum(model.v01Start[iJob, iPeriod] for iPeriod in model.sPeriods) == 1 #- model.vSlack[iJob]
    
    # c4:
    def c4_amount_ends(model, iJob):
        return sum(model.v01End[iJob, iPeriod] for iPeriod in model.sPeriods) == 1
    
    # c5:
    def c5_durations(model, iJob):
        return model.vEnd[iJob] + 1 >= model.vStart[iJob] +\
        sum(model.pDuration[iJob, iMode] * model.v01Mode[iJob, iMode] for iMode in model.sModes
            if (iJob, iMode) in model.sJobsModes)
    
    # c6: giving value to makespan
    def c6_makespan_value(model, iJob):
        return model.vMakespan >= model.vEnd[iJob]
    
    # c7: resources
    def c7_resource_allocation(model, iJob, iMode, iPeriod, iResource):
        # return model.vResources[iResource, iJob, iPeriod] >= model.v01Work[iJob, iPeriod] * model.pResourcesUsed[
        #     iJob, iResource, iMode] - M * (1 - model.v01Mode[iJob, iMode])
        return model.vResources[iResource, iJob, iPeriod] >=\
               (model.v01Work[iJob, iPeriod] + model.v01Mode[iJob, iMode] - 1) *\
               model.pResourcesUsed[iJob, iResource, iMode]
    
    # c8: maximum amount renewable resources
    def c8_max_r_resources(model, iResource, iPeriod):
        return sum(model.vResources[iResource, iJob, iPeriod] for iJob in model.sJobs) <= model.pMaxResources[iResource]
    
    # c9: maximum amount non-renewable resources
    def c9_max_n_resources(model, iResource):
        return sum(model.v01Mode[iJob, iMode] * model.pResourcesUsed[iJob, iResource, iMode]
                   for (iJob, iMode) in model.sJobsModes) <= model.pMaxResources[iResource]
    
    # c10: precedence
    def c10_precedence(model, iJob1, iJob2):
        return model.vEnd[iJob1]  + 1 <= model.vStart[iJob2]

    def c11_continue_work(model, iJob, iPeriod):
        if iPeriod < max(model.sPeriods):
            return model.v01Work[iJob, iPeriod + 1] >= model.v01Work[iJob, iPeriod] - model.v01End[iJob, iPeriod]
        else:
            return Constraint.Skip
    
    def c12_amount_modes(model, iJob):
        return sum(model.v01Mode[iJob, iMode] for iMode in model.sModes if (iJob, iMode) in model.sJobsModes) == 1
    
    # Objective function
    def obj_expression(model):
        return model.pWeightMakespan * model.vMakespan
        #        +\
        # model.pWeightResources * sum(model.vResources[iResource, iJob, iPeriod]
        #                     for iJob in model.sJobs for iPeriod in model.sPeriods for iResource in model.sNResources)
    
    
    # Activate constraints
    model.c1a_start_consistency = Constraint(model.sJobs, rule=c1a_start_consistency)
    model.c1b_end_consistency = Constraint(model.sJobs, rule=c1b_end_consistency)
    model.c2_start_work_relation = Constraint(model.sJobs, model.sPeriods, rule=c2_start_work_relation)
    model.c3_amount_starts = Constraint(model.sJobs, rule=c3_amount_starts)
    model.c4_amount_ends = Constraint(model.sJobs, rule=c4_amount_ends)
    model.c5_durations = Constraint(model.sJobs, rule=c5_durations)
    model.c6_makespan_value = Constraint(model.sJobs, rule=c6_makespan_value)
    model.c7_resource_allocation = Constraint(model.sJobsModes, model.sPeriods, model.sRResources,
                                              rule=c7_resource_allocation)
    model.c8_max_r_resources = Constraint(model.sRResources, model.sPeriods, rule=c8_max_r_resources)
    model.c9_max_n_resources = Constraint(model.sNResources, rule=c9_max_n_resources)
    model.c10_precedence = Constraint(model.sJobsPrecedence, rule=c10_precedence)
    model.c11_continue_work = Constraint(model.sJobs, model.sPeriods, rule=c11_continue_work)
    model.c12_amount_modes = Constraint(model.sJobs, rule=c12_amount_modes)
    
    # Add objective function
    model.f_obj = Objective(rule=obj_expression, sense=minimize)
    
    return model
