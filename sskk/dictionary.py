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

def _register(key, value):
    current = _compdb
    for c in key:
        if current.has_key(c):
            current = current[c]
        else:
            new_current = {}
            current[c] = new_current 
            current = new_current

_control_chars = re.compile("[\x00-\x1f\x7f\x80-\x9f\xff]")
def _escape(s):
    return _control_chars.sub("", s)

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
        if okuri:
            _okuridb[key + okuri] = value.split("/")
        else:
            _register(key, value)
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
    generators = []
    def expand_all(key, current, candidate):
        for c, value in current:
            if value == {}:
                candidate.append(key + c)
            else:
                expand_all(key + c, (x for x in value.items()), candidate) 

    def expand_sparse(key, current, candidate):
        for c, value in current:
            if value == {}:
                candidate.append(key + c)
                return True
            if expand_sparse(key + c, (x for x in value.items()), candidate):
                generators.append((key, current))
                return True
        return False

    for c in current:
        expand_sparse(c, (x for x in current[c].items()), candidate)
        if len(candidate) > 20:
            break
    else:
        if len(candidate) < 10:
            for item in generators:
                key, cur = item
                expand_all(c, cur, candidate)
            if len(candidate) < 10:
                for c in current:
                    if current[c] == {}:
                        candidate.append(c)

    return candidate 


################################################################################
#
# Clause
#
class Clause():

    def __init__(self, key, candidates):
        self._key = _escape(key)
        self._values = []
        self._displays = []
        for candidate in candidates:
            row = candidate.split(";")
            if len(row) == 2:
                value, remarks = row
            else:
                value, remarks = candidate, u""
            self._values.append(_escape(value))
            self._displays.append(_escape(value + " " + remarks))
        self._index = 0

    def getkey(self):
        return self._key

    def getcurrentvalue(self):
        return self._values[self._index]

    def getcandidates(self):
        return self._values

    def select(self, index):
        self._index = index

################################################################################
#
# Clauses
#
class Clauses:

    def __init__(self):
        self._clauses = []
        self._index = 0

    def __iter__(self):
        for clause in self._clauses:
            yield clause

    def add(self, clause):
        self._clauses.append(clause)

    def getkey(self):
        word = u""
        for clause in self._clauses:
            word += clause.getkey()
        return word

    def getvalue(self):
        word = u""
        for clause in self._clauses:
            word += clause.getcurrentvalue()
        return word

    def getcurrentclause(self):
        return self._clauses[self._index]

    def getcurrentvalue(self):
        return self._clauses[self._index].getcurrentvalue()

    def getcandidates(self):
        return self._clauses[self._index].getcandidates()

    def select(self, index):
        self._index = index

    def movenext(self):
        self._index = (self._index + 1) % len(self._clauses)

    def moveprev(self):
        self._index = (self._index - 1) % len(self._clauses)

    def _retry_google(self, words):
        response = call_cgi_api(",".join(words))
        if response:
            self._clauses = []
            for clauseinfo in response:
                key, candidates = clauseinfo
                clause = Clause(key, candidates)
                self.add(clause)
            if self._index >= len(self._clauses):
                self._index = len(self._clauses) - 1

    def shift_left(self):

        words = []
        for clause in self._clauses:
            words.append(clause.getkey())

        index = self._index
        surplus = words[index][-1:] + "".join(words[index + 1:])
        words[index] = words[index][:-1]
        words = words[0:index + 1] + [surplus]

        self._retry_google(words)

    def shift_right(self):

        words = []
        for clause in self._clauses:
            words.append(clause.getkey())

        index = self._index
        if index == len(words) - 1:
            words = words[:index] + [words[index][0], words[index][1:]]
        else:
            words[index] += words[index + 1][0]
            surplus = ("".join(words[index + 1:])[1:])
            words = words[:index + 1] + [surplus]

        self._retry_google(words)

import urllib, urllib2, json
def call_cgi_api(key):
    try:
        params = urllib.urlencode({'langpair' : 'ja-Hira|ja',
                                   'text' : key.encode("UTF-8")})
        url = 'http://www.google.com/transliterate?'
        json_response = urllib2.urlopen(url, params).read()
        response = json.loads(json_response)
         
    except:
        return None 
    return response

def get_from_google_cgi_api(key):
    try:
        params = urllib.urlencode({'langpair' : 'ja-Hira|ja',
                                   'text' : key.encode("UTF-8")})
        url = 'http://www.google.com/transliterate?'
        json_response = urllib2.urlopen(url, params).read()
        response = json.loads(json_response)

        clauses = Clauses() 
        for clauseinfo in response:
            key, candidates = clauseinfo
            clause = Clause(key, candidates)
            clauses.add(clause)
    except:
        return None 
    return clauses

thread.start_new_thread(_load, ())

def test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()

