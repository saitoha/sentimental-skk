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

import os, thread, inspect, re

_tangodb = {}
_okuridb = {}

def _load_dictionary():
    filename = inspect.getfile(inspect.currentframe())
    dirpath = os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))
    p = re.compile('^(.+?)([a-z])? /(.+)/')
    
    for line in open(dirpath + '/SKK-JISYO.L'):
        if line[1] == ';':
            continue
        line = unicode(line, u'eucjp')
        g = p.match(line)
        key = g.group(1)
        okuri = g.group(2)
        value = g.group(3)
        if okuri:
            _okuridb[key + okuri] = value
        else:
            _tangodb[key] = value 

def gettango(key):
    if _tangodb.has_key(key):
        return _tangodb[key]
    return None

def getokuri(key):
    if _okuridb.has_key(key):
        return _okuridb[key]
    return None

thread.start_new_thread(_load_dictionary, ())

