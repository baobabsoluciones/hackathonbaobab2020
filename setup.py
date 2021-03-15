#!/usr/bin/env python3

from setuptools import setup

packages = ['hackathonbaobab2020',
            'hackathonbaobab2020.core',
            'hackathonbaobab2020.solver',
            'hackathonbaobab2020.execution',
            'hackathonbaobab2020.solver.milp_LP_HL',
            'hackathonbaobab2020.schemas',
            'hackathonbaobab2020.tests',
            ]

with open("README.md", "r") as fh:
    long_description = fh.read()

install_requires = ['pytups', 'click', 'pandas', 'orloge', 'jsonschema']

extras_require = {
    'benchmark': ['tabulate', 'pygount', 'plotly', 'seaborn'],
    'solvers': ['pyomo' ,'ortools']
    }

kwargs = {
    "name": "hackathonbaobab2020",
    "version": "0.98.0",
    "packages": packages,
    "description": "Hackathon 2020 at baobab soluciones",
    "long_description": long_description,
    'long_description_content_type': "text/markdown",
    "author": "Franco Peschiera",
    "maintainer": "Franco Peschiera",
    "author_email": "pchtsp@gmail.com",
    "maintainer_email": "pchtsp@gmail.com",
    "install_requires": install_requires,
    "extras_require": extras_require,
    "url": "https://github.com/baobabsoluciones/hackathonbaobab2020",
    "download_url": "https://github.com/baobabsoluciones/hackathonbaobab2020/archive/main.zip",
    "keywords": "math hackathon pulp ortools pyomo",
    "include_package_data": True,
    "classifiers": [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
}

setup(**kwargs)