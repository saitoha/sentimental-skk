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
import sys

_CONFDB = {
}

_DEFAULT_CONF = """
#
#
_CONFDB_OVERLAY = %s

def get():
    return _CONFDB_OVERLAY

"""


# get resource directory path (~/.sskk)
homedir = os.path.expanduser("~")
rcdir = os.path.join(homedir, ".sskk")

if not os.path.exists(rcdir):
    # create resouce directory
    os.makedirs(rcdir)

# get configure file path (~/.sskk/conf.py)
confpath = os.path.join(rcdir, "conf.py")

if not os.path.exists(confpath):
    # create default configured setting file
    f = open(confpath, "w")
    try:
        f.write(_DEFAULT_CONF % '{}')
    finally:
        f.close()

# add resource directory to default import directory
sys.path.insert(0, rcdir)
try:
    import conf
    for key, value in conf.get().items():
        _CONFDB[key] = value
except:
    print str(sys.exc_info())
finally:
    sys.path.remove(rcdir)

def get(key):
    if key in _CONFDB:
        return _CONFDB[key]
    return None

def set(key, value):
    _CONFDB[key] = value

def save():
    f = open(confpath, "w")
    try:
        f.write(_DEFAULT_CONF % repr(_CONFDB))
    finally:
        f.close()
