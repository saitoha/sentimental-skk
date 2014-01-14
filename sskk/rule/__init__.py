#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ***** BEGIN LICENSE BLOCK *****
# Copyright (C) 2012  Hayaki Saito <user@zuse.jp>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# ***** END LICENSE BLOCK *****

import os

homedir = os.path.expanduser('~')
rcdir = os.path.join(homedir, '.sskk')

# ユーザ定義かなルールディレクトリ
ruledir = os.path.join(rcdir, 'rule')
if not os.path.exists(ruledir):
    os.makedirs(ruledir)


def list():
    """
    >>> result = list()
    >>> 'builtin_act' in result
    True
    >>> 'builtin_azik' in result
    True
    >>> 'builtin_normal' in result
    True
    """
    import os, sys, inspect

    files = []
    try:
        files += os.listdir(ruledir)
    except OSError:
        pass

    filename = inspect.getfile(inspect.currentframe())
    dirpath = os.path.abspath(os.path.dirname(filename))

    try:
        files += os.listdir(dirpath)
    except OSError:
        pass

    files = filter(lambda file: not file.startswith('__') and file.endswith('.py'), files)
    methods = map(lambda file: file[:-3], files)

    return methods


def get(s):
    """
    >>> import sys
    >>> sys_path_backup = sys.path
    >>> get('')
    Traceback (most recent call last):
    ValueError: Empty module name
    >>> sys.path == sys_path_backup
    True
    """
    import os
    import sys
    import inspect

    filename = inspect.getfile(inspect.currentframe())
    dirpath = os.path.abspath(os.path.dirname(filename))
    sys_path_backup = sys.path
    sys.path = [ruledir, dirpath]
    try:
        module = __import__(s)
    finally:
        sys.path = sys_path_backup
    return module.get()
        

def test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()
