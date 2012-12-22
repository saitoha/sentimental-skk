# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from sskk import __version__, __license__, __author__

import inspect, os

filename = inspect.getfile(inspect.currentframe())
dirpath = os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))

try:
    import sskk.tff
    import sskk.termprop
    import sskk.canossa
except:
    print "Please do:\n git submodule update --init"
    import sys
    sys.exit(1)

import sskk.mode as mode
import sskk.popup as popup
import sskk.input as input
import sskk.output as output
import sskk.romanrule as romanrule
import sskk.kanadb as kanadb
import sskk.eisuudb as eisuudb
import sskk.dictionary as dictionary

import doctest
dirty = False
for m in [mode,
          popup,
          input,
          output,
          romanrule,
          kanadb,
          eisuudb,
          dictionary]:
    failure_count, test_count = doctest.testmod(m)
    if failure_count > 0:
        dirty = True
if dirty:
    raise Exception("test failed.")

setup(name                  = 'sentimental-skk',
      version               = __version__,
      description           = '三 ┏( ^o^)┛ ＜ Japanese Input Method SKK (Simple Kana to Kanji conversion) on your terminal',
      long_description      = open(dirpath + "/README.rst").read(),
      py_modules            = ['sskk'],
      eager_resources       = ['sskk/SKK-JISYO.L'],
      classifiers           = ['Development Status :: 4 - Beta',
                               'Topic :: Terminals',
                               'Environment :: Console',
                               'Intended Audience :: End Users/Desktop',
                               'License :: OSI Approved :: GNU General Public License (GPL)',
                               'Programming Language :: Python'
                               ],
      keywords              = 'skk japanese terminal',
      author                = __author__,
      author_email          = 'user@zuse.jp',
      url                   = 'https://github.com/saitoha/sentimental-skk',
      license               = __license__,
      packages              = find_packages(exclude=[]),
      zip_safe              = False,
      include_package_data  = True,
      install_requires      = [],
      entry_points          = """
                              [console_scripts]
                              sskk = sskk.sskk:main
                              """
      )

