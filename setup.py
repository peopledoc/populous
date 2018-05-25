import sys

from setuptools import setup, find_packages

import populous


def readme():
    with open('README.rst') as f:
        return f.read()


requirements = [
    "click",
    "click-log>=0.2.0",
    "cached-property",
    "dateutils",
    "Faker",
    "future",
    "Jinja2",
    "PyYAML",
    "peloton_bloomfilters_py3"
]

if sys.version_info < (3, 2):
    requirements.append('functools32')

setup(
    name="populous",
    version=populous.__version__,
    url=populous.__url__,
    description="Populate your database with god-like powers",
    author=populous.__author__,
    author_email=populous.__author_email__,
    license=populous.__license__,
    long_description=readme(),
    packages=find_packages(exclude=['demo']),
    install_requires=requirements,
    extras_require={
        'tests': ['tox', 'pytest', 'pytest-mock', 'flake8'],
    },
    entry_points={
        'console_scripts': [
            'populous = populous.__main__:cli'
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Utilities",
    ],
    keywords='populous populate database',
    zip_safe=False,
)
