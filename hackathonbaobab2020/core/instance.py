import pytups as pt
import re
from ..schemas import check_instance, instance
from typing import List
from cornflow_client import InstanceCore
from pytups import SuperDict


class Instance(InstanceCore):
    schema = instance

    @property
    def data(self) -> SuperDict:
        return self._data

    @data.setter
    def data(self, value: SuperDict):
        self._data = value

    @classmethod
    def from_mm(cls, path: str, content: List[str] = None) -> "Instance":
        if content is None:
            with open(path, "r") as f:
                content = f.readlines()

        content = pt.TupList(content)
        index_prec = content.index("PRECEDENCE RELATIONS:\n")

        index_requests = content.index("REQUESTS/DURATIONS:\n")

        index_avail = content.index("RESOURCEAVAILABILITIES:\n")

        # precedence.
        precedence = content[index_prec + 2 : index_requests - 1]
        successors = pt.SuperDict()
        for line in precedence:
            _, job, modes, num_succ, *jobs, _ = re.split("\s+", line)
            successors[int(job)] = pt.TupList(jobs).vapply(int)
        successors = successors.kvapply(lambda k, v: dict(successors=v, id=k))

        # requests/ durations
        requests = content[index_requests + 3 : index_avail - 1]
        resources = re.findall(r"[RN] \d", content[index_requests + 1])
        needs = pt.SuperDict()
        durations = pt.SuperDict()
        last_job = ""
        for line in requests:
            if line[2] == " ":
                job = last_job
                _, mode, duration, *consumption, _ = re.split("\s+", line)
            else:
                _, job, mode, duration, *consumption, _ = re.split("\s+", line)
                last_job = job
            key = int(job), int(mode)
            needs[key] = {v: int(consumption[k]) for k, v in enumerate(resources)}
            needs[key] = pt.SuperDict(needs[key])
            durations[key] = int(duration)

        # resources / availabilities
        line = content[index_avail + 2]
        _, *avail, _ = re.split("\s+", line)
        availability = {k: int(avail[i]) for i, k in enumerate(resources)}
        availability = pt.SuperDict(availability).kvapply(
            lambda k, v: dict(available=v, id=k)
        )
        data = dict(
            resources=availability,
            jobs=successors,
            durations=durations.to_dictdict(),
            needs=needs.to_dictdict(),
        )
        return cls(data)

    def to_dict(self) -> dict:

        res = self.data["resources"].values_l()
        job = self.data["jobs"].values_l()
        duration = (
            self.data["durations"]
            .to_dictup()
            .to_tuplist()
            .vapply(lambda v: pt.SuperDict(job=v[0], mode=v[1], duration=v[2]))
        )
        needs = (
            self.data["needs"]
            .to_dictup()
            .to_tuplist()
            .vapply(
                lambda v: pt.SuperDict(job=v[0], mode=v[1], resource=v[2], need=v[3])
            )
        )

        data = pt.SuperDict(jobs=job, resources=res, needs=needs, durations=duration)

        return data

    @classmethod
    def from_dict(cls, data_json: dict) -> "Instance":
        check_instance(data_json)

        jobs = pt.SuperDict({v["id"]: v for v in data_json["jobs"]})
        res = pt.SuperDict({v["id"]: v for v in data_json["resources"]})
        needs = pt.SuperDict(
            {
                (v["job"], v["mode"], v["resource"]): round(v["need"])
                for v in data_json["needs"]
            }
        )
        durations = pt.SuperDict(
            {
                (v["job"], v["mode"]): round(v["duration"])
                for v in data_json["durations"]
            }
        )
        data = pt.SuperDict(
            jobs=jobs,
            resources=res,
            needs=needs.to_dictdict(),
            durations=durations.to_dictdict(),
        )
        return cls(data)

    @staticmethod
    def is_resource_renewable(resource: dict) -> bool:
        if "type" in resource:
            return resource["type"] == "R"
        return resource["id"][0] == "R"

    def get_renewable_resources(self) -> List[str]:
        return self.data["resources"].vfilter(self.is_resource_renewable).keys_l()
