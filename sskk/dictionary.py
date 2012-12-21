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

rcdir = os.path.join(os.getenv("HOME"), ".sskk")
dictdir = os.path.join(rcdir, "dict")
if not os.path.exists(dictdir):
    os.makedirs(dictdir)

_tangodb = {}
_okuridb = {}
_compdb = {}
_encoding = 0

def _register(key):
    current = _compdb
    for c in key:
        if current.has_key(c):
            current = current[c]
        else:
            new_current = {}
            current[c] = new_current 
            current = new_current

def _decode_line(line):
    global _encoding
    try:
        return unicode(line, [u'eucjp', u'utf-8]'][_encoding])
    except:
        _encoding = 1 - _encoding
        return unicode(line, [u'eucjp', u'utf-8]'][_encoding])

def _load_dict(filename):
    p = re.compile('^(.+?)([a-z])? /(.+)/')
    
    for line in open(filename):
        if line[1] == ';':
            continue
        line = _decode_line(line)
        g = p.match(line)
        key = g.group(1)
        okuri = g.group(2)
        value = g.group(3)
        _register(key)
        if okuri:
            _okuridb[key + okuri] = value.split("/")
        else:
            _tangodb[key] = value.split("/")

def _get_fallback_dict_path():
    filename = inspect.getfile(inspect.currentframe())
    dirpath = os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe())))
    return os.path.join(dirpath, 'SKK-JISYO.L')

def _load():
    dict_list = os.listdir(dictdir)
    if len(dict_list) == 0:
        _load_dict(_get_fallback_dict_path())
    else:
        for f in dict_list:
            _load_dict(os.path.join(dictdir, f))


def gettango(key):
    if _tangodb.has_key(key):
        return _tangodb[key]
    return None

def getokuri(key):
    if _okuridb.has_key(key):
        return _okuridb[key]
    return None

def getcomp(key):
    current = _compdb
    for c in key:
        if current.has_key(c):
            current = current[c]
        else:
            return None
    candidate = []
    def expand(key, current):
        if current == {}:
            candidate.append(key)
        else:
            for c in current:
                expand(key + c, current[c]) 
    expand("", current)
    return candidate 

thread.start_new_thread(_load, ())

def test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()

