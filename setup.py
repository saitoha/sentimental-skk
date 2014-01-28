# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from sskk import __version__, __license__, __author__

import inspect
import os

filename = inspect.getfile(inspect.currentframe())
dirpath = os.path.abspath(os.path.dirname(filename))
long_description = open(os.path.join(dirpath, "README.rst")).read()

try:
    import sskk.canossa
except ImportError, e:
    print e
    print "Please do:\n git submodule update --init"
    import sys
    sys.exit(1)

setup(name                  = 'sentimental-skk',
      version               = __version__,
      description           = '三 三 ( ´_ゝ`）＜ Japanese Input Method SKK '
                              '(Simple Kana to Kanji conversion) on your terminal',
      long_description      = long_description,
      py_modules            = ['sskk'],
      eager_resources       = ['sskk/SKK-JISYO.L',
                               'sskk/SKK-JISYO.assoc',
                               'sskk/SKK-JISYO.JIS2',
                               'sskk/SKK-JISYO.edict',
                               'sskk/SKK-JISYO.geo',
                               'sskk/SKK-JISYO.jinmei',
                              ],
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
      install_requires      = ['tff'],
      entry_points          = """
                              [console_scripts]
                              sskk = sskk.sskk:main
                              sskk-test-terminal = sskk.sskk:test_terminal
                              """
      )

