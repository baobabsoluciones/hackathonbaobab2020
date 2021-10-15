import pytups as pt
from .tools import dict_to_list
from ..schemas import check_solution, solution
from typing import List, Dict
from cornflow_client import SolutionCore
from pytups import SuperDict

_solutionHint = Dict[str, List[Dict[str, int]]]


class Solution(SolutionCore):
    schema = solution

    def __init__(self, data: _solutionHint):
        """ """
        # data is a dictionary that has, for each job, a time and a mode.
        # {job: period=(int), mode=(int)}
        super().__init__(data)
        return

    @property
    def data(self) -> SuperDict:
        return self._data

    @data.setter
    def data(self, value: SuperDict):
        self._data = value

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

    def to_dict(self) -> _solutionHint:
        return dict(assignment=dict_to_list(self.data, "job"))
