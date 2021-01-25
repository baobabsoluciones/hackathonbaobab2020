#!/usr/bin/env python3

from setuptools import setup

packages = ['hackathonbaobab2020',
            'hackathonbaobab2020.core',
            'hackathonbaobab2020.solvers',
            'hackathonbaobab2020.execution',
            'hackathonbaobab2020.solvers.milp_LP_HL']

with open("README.md", "r") as fh:
    long_description = fh.read()

required = []
with open("requirements.txt", "r") as fh:
    required.append(fh.read().splitlines())


kwargs = {
    "name": "hackathonbaobab2020",
    "version": 0.9,
    "packages": packages,
    "description": "Hackathon 2020 at baobab soluciones",
    "long_description": long_description,
    'long_description_content_type': "text/markdown",
    "author": "Franco Peschiera",
    "maintainer": "Franco Peschiera",
    "author_email": "pchtsp@gmail.com",
    "maintainer_email": "pchtsp@gmail.com",
    "install_requires": required,
    "url": "https://github.com/baobabsoluciones/hackathonbaobab2020",
    "download_url": "https://github.com/baobabsoluciones/hackathonbaobab2020/archive/main.zip",
    "keywords": "math hackathon pulp ortools pyomo",
    "classifiers": [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
}

setup(**kwargs)