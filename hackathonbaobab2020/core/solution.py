import pytups as pt
import json
from .tools import dict_to_list
from ..schemas import check_solution
from typing import List, Dict

_solutionHint = Dict[str, List[Dict[str, id]]]


class Solution(object):
    def __init__(self, data: Dict[int, Dict[str, int]]):
        """ """
        # data is a dictionary that has, for each job, a time and a mode.
        # {job: period=(int), mode=(int)}
        # pt.SuperDict is equivalent to `dict` but with additional methods
        self.data = pt.SuperDict.from_dict(data)
        return

    @classmethod
    def from_dict(cls, data_json: _solutionHint) -> "Solution":
        check_solution(data_json)
        data = pt.SuperDict(
            {
                v["job"]: pt.SuperDict(period=v["period"], mode=v["mode"])
                for v in data_json["assignment"]
            }
        )
        return cls(data)

    @classmethod
    def from_json(cls, path: str) -> "Solution":
        """ """
        with open(path, "r") as f:
            data_json = json.load(f)
        return cls.from_dict(data_json)

    def to_dict(self) -> _solutionHint:
        return dict(assignment=dict_to_list(self.data, "job"))

    def to_json(self, path: str) -> None:
        data_json = self.to_dict()
        with open(path, "w") as f:
            json.dump(data_json, f, indent=4, sort_keys=True)
        return
