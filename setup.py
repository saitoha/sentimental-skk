# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from sskk import __version__, __license__, __author__

import inspect, os

filename = inspect.getfile(inspect.currentframe())
dirpath = os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))

try:
    import sskk.canossa
except:
    print "Please do:\n git submodule update --init"
    import sys
    sys.exit(1)

import sskk.mode as mode
import sskk.input as input
import sskk.romanrule as romanrule
import sskk.kanadb as kanadb
import sskk.eisuudb as eisuudb
import sskk.dictionary as dictionary
import sskk.charbuf as charbuf
import sskk.word as word

import doctest
dirty = False
for m in [mode,
          input,
          romanrule,
          kanadb,
          eisuudb,
          dictionary,
          charbuf,
          word,
          ]:
    failure_count, test_count = doctest.testmod(m)
    if failure_count > 0:
        dirty = True
if dirty:
    raise Exception("test failed.")

print "succeeded."

setup(name                  = 'sentimental-skk',
      version               = __version__,
      description           = '三 ⊂二二二( ^o^)二二⊃ ＜ Japanese Input Method SKK (Simple Kana to Kanji conversion) on your terminal',
      long_description      = open(os.path.join(dirpath, "README.rst")).read(),
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
      install_requires      = [],
      entry_points          = """
                              [console_scripts]
                              sskk = sskk.sskk:main
                              """
      )

