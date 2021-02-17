import os
import json
from jsonschema import Draft7Validator

basedir = os.path.dirname(__file__)
print()

with open(os.path.join(basedir, 'instance.json'), 'r') as f:
    instance = json.load(f)

with open(os.path.join(basedir, 'solution.json'), 'r') as f:
    solution = json.load(f)


def check_schema(schema, data):
    checker = Draft7Validator(schema)
    if not checker.is_valid(data):
        error_list = [e for e in checker.iter_errors(data)]
        raise ValueError("Data is not compatible with schema: \n{}".
                         format(error_list))
    return True


def check_instance(data):
    return check_schema(instance, data)


def check_solution(data):
    return check_schema(solution, data)

