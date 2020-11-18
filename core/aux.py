import json


def copy_dict(_dict):
    return json.loads(json.dumps(_dict))


def dict_to_list(_dict, name):
    return _dict.kvapply(lambda k, v: {**v, **{name: k}}).values_l()
