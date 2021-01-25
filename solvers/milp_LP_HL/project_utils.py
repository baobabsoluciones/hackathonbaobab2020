
SOLVER_STATUS = {4: "optimal", 2: "maxTimeLimit", 3: "infeasible", 0: "unknown"}


def reverse_dict(d):
    return {j:i for i, j in d.items()}

def get_status_value(status):
    val = reverse_dict(SOLVER_STATUS)

    if status in val:
        return val[status]
    else:
        print("Unknown status: " + status)
        return val["Unknown"]

