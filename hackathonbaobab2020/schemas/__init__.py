import os
import json
from jsonschema import Draft7Validator

basedir = os.path.dirname(__file__)


def check_schema(schema, data):
    checker = Draft7Validator(schema)
    if not checker.is_valid(data):
        error_list = [e for e in checker.iter_errors(data)]
        raise ValueError("Data is not compatible with schema: \n{}".format(error_list))
    return True


def load_file(name):
    with open(os.path.join(basedir, name), "r") as f:
        data = json.load(f)
    return data


instance = load_file("instance.json")
solution = load_file("solution.json")
config = load_file("config.json")


def check_instance(data):
    return check_schema(instance, data)


def check_solution(data):
    return check_schema(solution, data)


def check_config(data):
    return check_schema(config, data)
