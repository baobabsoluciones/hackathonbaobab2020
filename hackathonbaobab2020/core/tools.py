try:
    import ujson as json
except ImportError:
    import json
import os
import pickle
from zipfile import ZipFile
import pytups as pt

from typing import Union


def copy_dict(_dict: dict) -> dict:
    return json.loads(json.dumps(_dict))


def dict_to_list(_dict: pt.SuperDict, name) -> list:
    return _dict.kvapply(lambda k, v: {**v, **{name: k}}).values_l()


def load_data(path: str, file_type: str = None) -> Union[dict, bool]:
    if file_type is None:
        splitext = os.path.splitext(path)
        if len(splitext) == 0:
            raise ImportError("file type not given")
        else:
            file_type = splitext[1][1:]
    if file_type not in ["json", "pickle"]:
        raise ImportError("file type not known: {}".format(file_type))
    if not os.path.exists(path):
        return False
    if file_type == "pickle":
        with open(path, "rb") as f:
            return pickle.load(f)
    if file_type == "json":
        with open(path, "r") as f:
            return json.load(f)


def load_data_zip(
    zipobj: ZipFile, path: str, file_type: str = "json"
) -> Union[dict, bool]:
    if file_type not in ["json"]:
        raise ImportError("file type not known: {}".format(file_type))
    if file_type == "json":
        try:
            data = zipobj.read(path)
        except KeyError:
            return False
        return json.loads(data)


def write_json(data: dict, path: str) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=4, sort_keys=True)


def parent_dirs(pathname: str, subdirs: set = None) -> set:
    """Return a set of all individual directories contained in a pathname

    For example, if 'a/b/c.ext' is the path to the file 'c.ext':
    a/b/c.ext -> set(['a','a/b'])
    """
    if subdirs is None:
        subdirs = set()
    parent = os.path.dirname(pathname)
    if parent:
        subdirs.add(parent)
        parent_dirs(parent, subdirs)
    return subdirs


def dirs_in_zip(zf: ZipFile) -> set:
    """Return a list of directories that would be created by the ZipFile zf"""
    alldirs = set()
    for fn in zf.namelist():
        alldirs.update(parent_dirs(fn))
    return alldirs
