"""
​
Optimization model to assign employees to bus stops
​
"""

import pyomo
import pyomo.opt
from pyomo.environ import *

def get_bus_stops_model():
    """
    This function creates the pyomo bus stops location abstract model.
​
    :return: a pyomo abstract model
    """
    
    # Create model
    model = AbstractModel()
    
    # Model sets
    model.sJobs = Set()
    model.sResources = Set()
    model.sModes = Set()
    model.sPeriods = Set()
    model.sPairsPrecedence = Set()
    model.sJobsPrecedence = Set(dimen=2)
    model.sJobsModes = Set(dimen=2)

    
    # Model parameters
    
    # General parameters
    model.pResourcesUsed = Param(model.sJobs, model.sResources, model.sModes, mutable=True)
    model.pDuration = Param(model.sJobsModes, model.sModes, mutable=True)
    model.pMaxResources = Param(model.sResources, mutable=True)
    
    
    # Objective function parameters
    model.pWeightResources = Param(mutable=True)
    model.pWeightMakespan = Param(mutable=True)
    
    # Model variables
    model.v01Start = Var(model.sJobs, model.sPeriods, domain=Binary)
    model.vStart = Var(model.sJobs, domain=NonNegativeIntegers)
    model.v01End = Var(model.sJobs, model.sPeriods, domain=Binary)
    model.vEnd = Var(model.sJobs, domain=NonNegativeIntegers)
    model.vResources = Var(model.sResources, model.sJobs, model.sPeriods, domain=NonNegativeIntegers)
    model.v01Mode = Var(model.sJobsModes, domain=Binary)
    model.vMakespan = Var(domain=Reals)
    
    
    # Constraints
    # c1:
    def c1_start_consistency(model, iJob, iPeriod):
        return model.vStart[iJob] == model.v01Start[iJob, iPeriod] * int(iPeriod)
    
    # c2:
    def c2_start_work_relation(model, iJob, iPeriod):
        return model.v01Start[iJob, iPeriod] <= model.v01Work[iJob, iPeriod]
    
    # c3:
    def c3_amount_starts(model, iJob):
        return sum(model.v01Start[iJob, iPeriod] for iPeriod in model.sPeriods) == 1
    
    # c4:
    def c4_amount_ends(model, iJob):
        return sum(model.v01End[iJob, iPeriod] for iPeriod in model.sPeriods) == 1
    
    # c5:
    def c5_durations(model, iJob):
        return model.vEnd[iJob] >= model.vStart[iJob] + sum(
            model.pDuration[iJob, iMode] * model.v01Mode[iJob, iMode] for iMode in model.sModes)
    
    # c6: giving value to makespan
    def c6_makespan_value(model, iJob):
        return model.vMakespan >= model.vEnd[iJob]
    
    # c7: resources
    def c7_resource_allocation(model, iJob, iPeriod, iMode, iResource):
        return model.vResources[iResource, iJob, iPeriod] >= model.v01Work[iJob, iPeriod] * model.pResourcesUsed[
            iJob, iResource, iMode] - 1000000 * (1 - model.v01Mode[iJob, iMode])
    
    # c8: maximum amount renewable resources
    def c8_max_r_resources(model, iResource, iPeriod):
        return sum(model.vResources[iResource, iJob, iPeriod] for iJob in model.sJobs) <= model.pMaxResources[iResource]
    
    # c9: maximum amount non-renewable resources
    def c9_max_r_resources(model, iResource):
        return sum(model.vResources[iResource, iJob, iPeriod] for iJob in model.sJobs for iPeriod in model.sPeriods) <= \
               model.pMaxResources[iResource]
    
    # c10: precedence
    def c10_precedence(model, iJob1, iJob2):
        return model.vEnd[iJob1] < model.vStart[iJob2]
    
    # Objective function
    def obj_expression(model):
        """
        -  the number of bus stops will be minimized. Stops belonging to an express route will not be considered
        -  the sum of distances between employees and bus stops will be minimized
        """
        return model.pWeightMakespan * model.vMakespan
    
    
    # Activate constraints
    model.c1_start_consistency = Constraint(model.sJobs, model.sPeriods, rule=c1_start_consistency)
    model.c2_start_work_relation = Constraint(model.sJobs, model.sPeriods, rule=c2_start_work_relation)
    model.c3_amount_starts = Constraint(model.sJobs, rule=c3_amount_starts)
    model.c4_amount_ends = Constraint(model.sJobs, rule=c4_amount_ends)
    model.c5_durations = Constraint(model.sJobs, rule=c5_durations)
    model.c6_makespan_value = Constraint(model.sJobs, rule=c6_makespan_value)
    model.c7_resource_allocation = Constraint(model.sJobs, model.sPeriods, model.sModes, model.sResources,
                                              rule=c7_resource_allocation)
    model.c8_max_r_resources = Constraint(model.sResources, model.sPeriods, rule=c8_max_r_resources)
    model.c9_max_r_resources = Constraint(model.sResources, rule=c9_max_r_resources)
    model.c10_precedence = Constraint(model.sPairsPrecedence, rule=c10_precedence)
    
    # Add objective function
    model.f_obj = Objective(rule=obj_expression, sense=minimize)
    
    return model
