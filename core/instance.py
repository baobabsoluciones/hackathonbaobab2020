import pytups as pt
import re
import json


class Instance(object):

    def __init__(self, data):
        self.data = data

    @classmethod
    def from_mm(cls, path):
        with open(path, 'r') as f:
            content = f.readlines()

        content = pt.TupList(content)
        index_prec = \
            content. \
            index('PRECEDENCE RELATIONS:\n')

        index_requests = \
            content.index('REQUESTS/DURATIONS:\n')

        index_avail = \
            content.\
            index('RESOURCEAVAILABILITIES:\n')

        # precedence.
        precedence = content[index_prec+2:index_requests-1]
        successors = pt.SuperDict()
        for line in precedence:
            _, job, modes, num_succ, *jobs, _ = re.split('\s+', line)
            successors[int(job)] = pt.TupList(jobs).vapply(int)
        successors = successors.kvapply(lambda k, v:  dict(successors=v, id=k))

        # requests/ durations
        requests = content[index_requests+3:index_avail - 1]
        resources = re.findall(r'[RN] \d', content[index_requests+1])
        needs = pt.SuperDict()
        durations = pt.SuperDict()
        last_job = ''
        for line in requests:
            if line[2] == ' ':
                job = last_job
                _, mode, duration, *consumption, _ = re.split('\s+', line)
            else:
                _, job, mode, duration, *consumption, _ = re.split('\s+', line)
                last_job = job
            key = int(job), int(mode)
            needs[key] = \
                {v: int(consumption[k]) for k, v in enumerate(resources)}
            needs[key] = pt.SuperDict(needs[key])
            durations[key] = int(duration)

        # resources / availabilities
        line = content[index_avail + 2]
        _, *avail, _ = re.split('\s+', line)
        availability = {k: int(avail[i]) for i, k in enumerate(resources)}
        availability = pt.SuperDict(availability).kvapply(lambda k, v: dict(available=v, id=k))
        data = dict(resources=availability, jobs=successors, durations=durations.to_dictdict(),
                    needs=needs.to_dictdict())
        return cls(data)
    
    def format_data(self):
        res = self.data['resources'].values_l()
        job = self.data['jobs'].values_l()
        duration =self.data['durations'].to_dictup().to_tuplist().vapply(lambda v: pt.SuperDict(job=v[0], mode=v[1], duration=v[2]))
        needs = \
            self.data['needs'].to_dictup().to_tuplist().\
            vapply(lambda v: pt.SuperDict(job=v[0], mode=v[1],
                                          resource=v[2],
                                          need=v[3]))

        data = pt.SuperDict(jobs=job, resources=res, needs=needs, durations=duration)
        
        return data
    
    def get_input_data(self):
        
        data = self.format_data()
        print(data)
        self.input_data = {}
        
        jobs = set([j["id"] for j in data["jobs"]])
        periods = [p for p in range(140)]
        resources = [r["id"] for r in data["resources"]]
        modes = set([d["mode"] for d in data["durations"]])
        resources_needs = {(n["job"], n["resource"], n["mode"]): n["need"] for n in data["needs"]}
        # TODO: solve this problem here
        jobs_precedence = [sum([(j["id"], i) for i in j["successors"]], []) for j in data["jobs"]]
        jobs_durations = {(d["job"], d["mode"]): d["duration"] for d in data["durations"]}
        total_resources = {r["id"]: r["available"] for r in data["resources"]}
        
        self.input_data["sJobs"] = {None: jobs}
        self.input_data["sPeriods"] = {None: periods}
        self.input_data["sRessources"] = {None: resources}
        self.input_data["sModes"] = {None: modes}
        self.input_data["sJobsPrecedence"] = {None: jobs_precedence}
        self.input_data["sJobsModes"] = {None: jobs_durations.keys()}

        self.input_data["pResourcesUsed"] = resources_needs
        self.input_data["pDuration"] = jobs_durations
        self.input_data["pMaxResources"] = total_resources
        self.input_data["pWeightMakespan"] = {None: 1}
        self.input_data["pWeightResources"] = {None: 0}
        
        return {None: self.input_data}

    @classmethod
    def from_json(cls, path):
        with open(path, 'r') as f:
            data_json = json.load(f)
        jobs = pt.SuperDict({v['id']: v for v in data_json['jobs']})
        res = pt.SuperDict({v['id']: v for v in data_json['resources']})
        needs = pt.SuperDict({(v['job'], v['mode'], v['resource']): v['need'] for v in data_json['needs']})
        durations = pt.SuperDict({(v['job'], v['mode']): v['duration'] for v in data_json['durations']})
        data = pt.SuperDict(jobs=jobs, resources=res, needs=needs.to_dictdict(), durations=durations.to_dictdict())
        print(data)
        return cls(data)

    def to_json(self, path):
        res = self.data['resources'].values_l()
        job = self.data['jobs'].values_l()
        duration =self.data['durations'].to_dictup().to_tuplist().vapply(lambda v: pt.SuperDict(job=v[0], mode=v[1], duration=v[2]))
        needs = \
            self.data['needs'].to_dictup().to_tuplist().\
            vapply(lambda v: pt.SuperDict(job=v[0], mode=v[1],
                                          resource=v[2],
                                          need=v[3]))

        data = pt.SuperDict(jobs=job, resources=res, needs=needs, durations=duration)
        with open(path, 'w') as f:
            json.dump(data, f, indent=4, sort_keys=True)

    def get_renewable_resources(self):
        return self.data['resources'].kfilter(lambda k: k[0]=='R').keys()

    def graph(self):
        pass
