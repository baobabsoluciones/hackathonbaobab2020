"""
Functions to help programming with pyomo
"""

from pyomo.environ import *
from itertools import product


def write_cbc_warmstart_file(filename, instance, opt):
    """
    This function write a file to be passed to cbc solver as a warmstart file.
    This function is necessary because of a bug of cbc that does not allow reading warmstart files on windows
    with absolute path.

    :param filename: path to the file
    :param instance: model instance (created with create_instance)
    :param opt: solver instance (created with solver factory)
    :return:
    """
    opt._presolve(instance)
    opt._write_soln_file(instance, filename)


def activate_constraint(deact_constraint, indices=None):
    """
    Activate a constraint for all the given indices.
    Non existing indices are ignored.
    If no indices are given, activate the constraint for all the indices.

    :param deact_constraint: a pyomo constraint
    :param indices: a list of indices corresponding to the constraint indices.
    :return: nothing (modify the constraint)
    """
    if indices is None:
        keys_to_activate = [key for key in deact_constraint.keys()]
    else:
        keys_to_activate = set(deact_constraint.keys()).intersection(set(indices))
    for key in keys_to_activate:
        deact_constraint[key].activate()


def activate_constraint_list(constraint_list, indices=None):
    """
    Activate a list of constraints for all the given indices.
    Non existing indices are ignored.
    If no indices are given, activate the constraints for all the indices.

    :param constraint_list: a list of pyomo constraints
    :param indices: a list of indices corresponding to the constraints indices.
    :return: nothing (modify the constraint)
    """
    for individual_constraint in constraint_list:
        activate_constraint(individual_constraint, indices)


def deactivate_constraint(act_constraint, indices=None):
    """
    Deactivate a constraint for all the given indices.
    Non existing indices are ignored.
    If no indices are given, activate the constraint for all the indices.

    :param act_constraint: a pyomo constraint
    :param indices: a list of indices corresponding to the constraint indices.
    :return: nothing (modify the constraint)
    """
    if indices is None:
        keys_to_activate = [key for key in act_constraint.keys()]
    else:
        keys_to_activate = set(act_constraint.keys()).intersection(set(indices))
    
    for key in keys_to_activate:
        act_constraint[key].deactivate()


def deactivate_constraint_list(constraint_list, indices=None):
    """
    Deactivate a list of constraints for all the given indices.
    Non existing indices are ignored.
    If no indices are given, activate the constraints for all the indices.

    :param constraint_list: a list of pyomo constraints
    :param indices: a list of indices corresponding to the constraints indices.
    :return: nothing (modify the constraint)
    """
    for individual_constraint in constraint_list:
        deactivate_constraint(individual_constraint, indices)


def free_variable(variable, indices=None):
    """
    Free a variable for all the given indices.
    Non existing indices are ignored.
    If no indices are given, free the variable for all the indices.

    :param variable: a pyomo variables
    :param indices: a list of indices corresponding to the variable indices.
    :return: nothing (modify the variable)
    """
    if indices is None:
        keys_to_free = [key for key in variable.keys()]
    else:
        keys_to_free = set(variable.keys()).intersection(set(indices))
    
    for key in keys_to_free:
        variable[key].fixed = False


def free_variable_list(variable_list, indices=None):
    """
    Free a list of variables for all the given indices.
    Non existing indices are ignored.
    If no indices are given, free the variables for all the indices.

    :param variable_list: a list of pyomo variables
    :param indices: a list of indices corresponding to the variable indices.
    :return: nothing (modify the variable)
    """
    for variable in variable_list:
        free_variable(variable, indices)


def fix_variable(variable, indices=None):
    """
    fix (freeze) a variable for all the given indices.
    Non existing indices are ignored.
    If no indices are given, free the variable for all the indices.

    :param variable: a pyomo variable
    :param indices: a list of indices corresponding to the variable indices.
    :return: nothing (modify the variable)
    """
    if indices is None:
        keys_to_free = [key for key in variable.keys()]
    else:
        keys_to_free = set(variable.keys()).intersection(set(indices))
    
    for key in keys_to_free:
        variable[key].fixed = True


def fix_variable_list(variable_list, indices=None):
    """
    Fix (freeze) a list of variables for all the given indices.
    Non existing indices are ignored.
    If no indices are given, free the variables for all the indices.

    :param variable_list: a list of pyomo variables
    :param indices: a list of indices corresponding to the variable indices.
    :return: nothing (modify the variable)
    """
    for variable in variable_list:
        fix_variable(variable, indices)


def get_status(result):
    """
    Return the status of the solution from the result object

    :param result: a pyomo result object
    :return: the status
    """
    return str(result.solver.termination_condition)


def is_feasible(status):
    """
    Return True if the status is optimal or maxTimeLimit

    :param status: a status (string or pyomo object)
    :return: True if the status is optimal or maxTimeLimit
    """
    return str(status) == str(TerminationCondition.optimal) or str(status) == str(TerminationCondition.maxTimeLimit)


def exist(variable, indices=None):
    """
    Take a list of indices and return only the existing indices for the given variable.
    If no indices are given, return all the existing inidices of the variable.

    :param variable: a pyomo variable.
    :param indices: a list of indices or combination of indices.
    :return: all indices combinations
    """
    if indices is None:
        return [key for key in variable.keys()]
    else:
        return set(variable.keys()).intersection(set(indices))


def combine(*indices_lists):
    """
    Return all the combinations from lists of indices

    :param indices_lists: each argument is a list of indices (it must be a list)
    :return: The combined list of indices
    """
    if len([*indices_lists]) > 1:
        return [i for i in product(*indices_lists)]
    else:
        return set(*indices_lists)


def existing_indices(variable, *indices_lists):
    """
    Return all the existing combinations for the given variables and the indices lists.

    :param variable: a pyomo variable.
    :param indices_lists: each argument is a list of indices (it must be a list)
    :return: all existing indices combinations
    """
    return exist(variable, combine(*indices_lists))


def var_to_dict(variable):
    """
    Transform a pyomo variable into a python dict

    :param variable: a pyomo variable
    :return: a dict containing the indices and values of the variable.
    """
    return {key: value(variable[key]) for key in variable.keys()}




