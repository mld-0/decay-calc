#   VIM SETTINGS: {{{3
#   vim: set tabstop=4 modeline modelines=10 foldmethod=marker:
#   vim: set foldlevel=2 foldcolumn=3: 
#   }}}1

import re
from distutils.core import setup
from setuptools import setup

version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('decaycalc/__main__.py').read(),
    re.M
    ).group(1)

with open("README.md", "rb") as f:
    long_descr = f.read().decode("utf-8")

test_depend = [ 
    'pytest'
    'pandas'
    'tzlocal'
    'pytz'
    'dateparser'
    'matplotlib'
]

setup(
    name="decaycalc",
    version=version,
    author="Matthew L Davis",
    author_email="mld.0@protonmail.com",
    description="Calculate amount of given item remaining at a given time from a list of qtys and datetimes",
    long_description=long_descr,
    packages = ['decaycalc', 'tests'],
    tests_require=test_depend,
    entry_points={
        'console_scripts': [ 
        'decaycalc=decaycalc.__main__:clicalc',
        ],
    }
)


