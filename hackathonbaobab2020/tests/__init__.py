import os
import zipfile
from ..core import Instance


def get_test_instance(zip, filename):
    directory = os.path.join(os.path.dirname(__file__), "../data/")
    zip_path = os.path.join(directory, zip)
    zip_obj = zipfile.ZipFile(zip_path)
    data = zip_obj.read(filename)
    return Instance.from_mm(path=None, content=data.decode().splitlines(True))
