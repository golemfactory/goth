#!/usr/bin/env python

from os import path
import sys

from setuptools import setup, find_packages


def parse_requirements(my_path):
    """
    Parse requirements.txt file
    :return: [requirements, dependencies]
    """
    import re

    requirements = []
    dependency_links = []
    requirement_lines = open(path.join(my_path, "requirements.txt"))
    for line in reversed(list(requirement_lines)):
        line = line.strip()
        if line.startswith("-") or line.startswith("#"):
            continue

        m = re.match(".+#egg=(?P<package>.+?)(?:&.+)?$", line)
        if m:
            requirements.append(m.group("package"))
            dependency_links.append(line)
        else:
            requirements.append(line)
    return requirements, dependency_links


directory = path.abspath(path.dirname(__file__))
requirements, dependencies = parse_requirements(directory)

setup(
    name="yagna-integration",
    version="0.0.1",
    platforms=sys.platform,
    description="Testing framework for yagna",
    long_description="Testing framework for yagna",
    url="https://golem.network",
    author="Golem Team",
    author_email="contact@golem.network",
    license="GPL-3.0",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.7",
    ],
    zip_safe=False,
    keywords="golem",
    package_dir={'': 'ya-int'},
    packages=find_packages(include=["../test"]),
    install_requires=requirements,
    dependency_links=dependencies,
)
