
"""

Optimization model to assign employees to bus stops

"""

import pyomo
import pyomo.opt
from pyomo.environ import *

def get_bus_stops_model():
    """
    This function creates the pyomo bus stops location abstract model.

    :return: a pyomo abstract model
    """
    
    # Create model
    model = AbstractModel()
    
    # Model sets
    model.sJobs = Set()
    model.sResources = Set()
    model.sModes = Set()
    model.sPeriods = Set()
    
    model.sJob_periods = Set(dimen = 2)

    # Model parameters
    
    # General parameters
    model.pResourcesUsed = Param(model.sJobs, model.sResources, model.sModes, mutable=True)
    
    # Objective function parameters
    model.pWeightResources = Param(mutable=True)
    model.pWeightMakespan = Param(mutable=True)
    
    # Model variables
    model.v01Start = Var(model.sJobs, model.sPeriods, domain=Binary)
    model.vStart = Var(model.sJobs, domain=NonNegativeIntegers)
    model.vMakespan = Var(domain=Reals)
    
    # Constraints
    # c1: all employees should be assigned to a single bus stop
    def c1_start_consistency(model, iJob, iPeriod):
        return model.vStart[iJob] == model.v01Start[iJob, iPeriod] * int(iPeriod)
    
    # Objective function
    def obj_expression(model):
        """
        -  the number of bus stops will be minimized. Stops belonging to an express route will not be considered
        -  the sum of distances between employees and bus stops will be minimized
        """
        return model.pWeightMakespan * model.vMakespan
    
    # Activate constraints
    model.c1_start_consistency = Constraint(model.sJobs, model.sPeriods, rule=c1_start_consistency)
    
    # Add objective function
    model.f_obj = Objective(rule=obj_expression, sense=minimize)
    
    return model


