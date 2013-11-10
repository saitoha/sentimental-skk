#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ***** BEGIN LICENSE BLOCK *****
# Copyright (C) 2012-2013  Hayaki Saito <user@zuse.jp>
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
import thread
import inspect
import re
import logging

_TIMEOUT = 1.0

homedir = os.path.expanduser("~")
rcdir = os.path.join(homedir, ".sskk")
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
        if c in current:
            current = current[c]
        else:
            new_current = {}
            current[c] = new_current
            current = new_current

_control_chars = re.compile("[\x00-\x1f\x7f\x80-\x9f\xff]")


def _escape(s):
    """
    >>> _escape("abc")
    'abc'
    >>> _escape("lda\\x1baa\x10laa")
    'ldaaalaa'
    """
    return _control_chars.sub("", s)


def _decode_line(line):
    global _encoding
    try:
        return unicode(line, [u'eucjp', u'utf-8]'][_encoding])
    except:
        _encoding = 1 - _encoding
        return unicode(line, [u'eucjp', u'utf-8]'][_encoding])


def _load_dict(filename):
    p = re.compile('^(?:([0-9a-z.]+?)|(.+?)([a-z])?) /(.+)/')

    try:
        for line in open(filename):
            if len(line) < 4 or line[1] == ';':
                continue
            line = _decode_line(line)
            g = p.match(line)
            alphakey = g.group(1)
            key = g.group(2)
            okuri = g.group(3)
            value = g.group(4)
            if key:
                if okuri:
                    key += okuri
                else:
                    _register(key, value)
                if key in _tangodb:
                    _tangodb[key] += value.split("/")
                else:
                    _tangodb[key] = value.split("/")
            else:
                _register(alphakey, value)
                if alphakey in _tangodb:
                    _tangodb[alphakey] += value.split("/")
                else:
                    _tangodb[alphakey] = value.split("/")
    except:
        logging.exception("loading process failed. filename: %s" % filename)


def _get_fallback_dict_path(name):
    filename = inspect.getfile(inspect.currentframe())
    dirpath = os.path.abspath(os.path.dirname(filename))
    return os.path.join(dirpath, name)


def _load():
    dict_list = os.listdir(dictdir)
    _load_dict(_get_fallback_dict_path('SKK-JISYO.builtin'))
    _load_dict(_get_fallback_dict_path('SKK-JISYO.L'))
    _load_dict(_get_fallback_dict_path('SKK-JISYO.JIS2'))
    _load_dict(_get_fallback_dict_path('SKK-JISYO.assoc'))
    _load_dict(_get_fallback_dict_path('SKK-JISYO.geo'))
    _load_dict(_get_fallback_dict_path('SKK-JISYO.jinmei'))
    if dict_list:
        for f in dict_list:
            _load_dict(os.path.join(dictdir, f))


def gettango(key):
    if key in _tangodb:
        return _tangodb[key]
    return None


def getokuri(key):
    if key in _tangodb:
        return _tangodb[key]
    return None


def getcomp(key, comp):

    _current = _compdb
    for _c in key:
        if _c in _current:
            _current = _current[_c]
        else:
            return None

    def expand_all(key, current, candidate):
        for c, value in current:
            if value == {}:
                candidate.append(key + c)
            else:
                expand_all(key + c, (x for x in value.items()), candidate)

    def expand_sparse(key, current, candidate, generators):
        for c, value in current:
            if value == {}:
                candidate.append(key + c)
                return True
            generator = (x for x in value.items())
            if expand_sparse(key + c, generator, candidate, generators):
                generators.append((key + c, current))
                return True
        return False

    def impl(key, current, candidate):
        generators = []
        for c in current:
            generator = (x for x in current[c].items())
            expand_sparse(key + c, generator, candidate, generators)
            if len(candidate) > 10:
                break
        else:
            if len(candidate) < 10:
                for item in generators:
                    k, v = item
                    expand_all(k, v, candidate)
                if len(candidate) < 10:
                    for c in current:
                        if current[c] == {}:
                            candidate.append(c)
                if current == {}:
                    candidate.append(key)

    candidate = []
    if not comp:
        impl(u"", _current, candidate)
    else:
        for _key in comp:
            if len(_key) == 1:
                if _key in _current:
                    impl(_key, _current[_key], candidate)
            elif len(_key) == 2:
                if _key[0] in _current:
                    if _key[1] in _current[_key[0]]:
                        impl(_key, _current[_key[0]][_key[1]], candidate)
    return candidate


###############################################################################
#
# Clause
#
class Clause():

    def __init__(self, key, candidates):
        self._key = _escape(key)
        self._values = []
        self._remarks = []
        for candidate in candidates:
            row = candidate.split(";")
            if len(row) == 2:
                value, remark = row
            else:
                value, remark = candidate, u""
            self._values.append(_escape(value))
            self._remarks.append(_escape(remark))
        self._index = 0

    def getkey(self):
        return self._key

    def getcurrentvalue(self):
        return self._values[self._index]

    def getcurrentremark(self):
        return self._remarks[self._index]

    def getcandidates(self):
        return self._values

    def select(self, index):
        self._index = index


###############################################################################
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

    def length(self):
        return len(self._clauses)

    def getvalue(self):
        word = u""
        for clause in self._clauses:
            word += clause.getcurrentvalue()
        return word

    def getcurrentclause(self):
        return self._clauses[self._index]

    def getcurrentvalue(self):
        return self._clauses[self._index].getcurrentvalue()

    def getcurrentremark(self):
        return self._clauses[self._index].getcurrentremark()

    def getcandidates(self):
        return self._clauses[self._index].getcandidates()

    def select(self, index):
        self._index = index

    def movenext(self):
        self._index = (self._index + 1) % self.length()

    def moveprev(self):
        self._index = (self._index - 1) % self.length()

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

import urllib
import urllib2
import json


def call_cgi_api(key):
    try:
        params = urllib.urlencode({'langpair': 'ja-Hira|ja',
                                   'text': key.encode("UTF-8")})
        url = 'http://www.google.com/transliterate?'
        response = urllib2.urlopen(url + str(params))
        json_response = response.read()
        if not json_response:
            logging.exception("call_cgi_api failed. %s" % (url + str(params)))
            return None
        response = json.loads(json_response)

    except:
        logging.exception("call_cgi_api failed. key: %s" % key)
        return None
    return response


def get_from_google_cgi_api(clauses, key):
    response = call_cgi_api(key)
    if not response:
        return None
    try:
        for clauseinfo in response:
            key, candidates = clauseinfo
            clause = Clause(key, candidates)
            clauses.add(clause)
    except:
        logging.exception("get_from_google_cgi_api failed. key: %s" % key)
        return None
    return clauses

thread.start_new_thread(_load, ())
#_load()


def test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()
