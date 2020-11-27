import json


def copy_dict(_dict):
    return json.loads(json.dumps(_dict))


def dict_to_list(_dict, name):
    return _dict.kvapply(lambda k, v: {**v, **{name: k}}).values_l()

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