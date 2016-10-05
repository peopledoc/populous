import sys

from setuptools import setup, find_packages

import populous

requirements = [
    "click",
    "cached-property",
    "fake-factory",
    "dateutils"
]

if sys.version_info < (3, 2):
    requirements.append('functools32')

setup(
    name="populous",
    version=populous.__version__,
    url=populous.__url__,
    description=populous.__doc__,
    author=populous.__author__,
    license=populous.__license__,
    long_description="TODO",
    packages=find_packages(),
    install_requires=requirements,
    extra_require={
        'tests': ['tox', 'pytest', 'pytest-mock'],
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
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Topic :: Utilities",
    ],
    keywords='populous populate database',
)
