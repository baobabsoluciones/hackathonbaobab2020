from .run_batch import *
import warnings

try:
    from .benchmark import *
except ImportError:
    warnings.warn("To use the benchmark functions, to install benchmark dependencies: \n`pip install hackathonbaobab2020[benchmark]`")
