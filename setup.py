# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from sskk import __version__, __license__, __author__

setup(name                  = 'sentimental-skk',
      version               = __version__,
      description           = '三 ┏( ^o^)┛ ＜ Japanese Input Method SKK (Simple Kana to Kanji conversion) on your terminal',
      long_description      = open("README.rst").read(),
      py_modules            = ['sskk'],
      eager_resources       = ['sskk/skk/SKK-JISYO.L'],
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
      install_requires      = ['tff ==0.0.13, <0.1.0', 'canossa ==0.0.12'],
      entry_points          = """
                              [console_scripts]
                              sskk = sskk:main
                              """
      )

