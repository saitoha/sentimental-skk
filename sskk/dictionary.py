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
import inspect
import re
import settings
import logging
import time
import thread

homedir = os.path.expanduser('~')
rcdir = os.path.join(homedir, '.sskk')

# 標準辞書ディレクトリ
dictdir = os.path.join(rcdir, 'dict')
if not os.path.exists(dictdir):
    os.makedirs(dictdir)

# ユーザー辞書ディレクトリ
userdictdir = os.path.join(rcdir, 'userdict')
if not os.path.exists(userdictdir):
    os.makedirs(userdictdir)

bash_history_path = os.path.join(homedir, '.bash_history')
zsh_history_path = os.path.join(homedir, '.zsh_history')

_user_tangodb = {}
_tangodb = {}
_okuridb = {}

user_dict_file = None


class SkkLineLoader():

    _encoding = 0
    _encoding_list = [u'euc-jp', u'utf-8']
    _pattern = re.compile('^(?:([0-9a-z\.\^]+?)|(.+?)([a-z])?) /(.+)/')

    def _decode_line(self, line):
        try:
            return unicode(line, self._encoding_list[self._encoding])
        except UnicodeDecodeError:
            self._encoding = 1 - self._encoding  # flip
        return unicode(line, self._encoding_list[self._encoding])

    def parse(self, line):
        if len(line) < 4 or line[1] == ';':
            return
        try:
            line = self._decode_line(line)
        except UnicodeDecodeError:
            return
        match = self._pattern.match(line)
        if not match:
            template = '_load_dict: can\'t load the entry: %s'
            logging.warning(template % line)
        alphakey, key, okuri, value = match.groups()
        if key:
            if okuri:
                key += okuri
            else:
                completer.register(key, value)
            if key in _tangodb:
                values = _tangodb[key]
                new_values = value.split('/')
                for new_value in new_values:
                    if not new_value in values:
                        values.append(new_value)
            else:
                _tangodb[key] = value.split('/')
        else:
            completer.register(alphakey, value)
            if alphakey in _tangodb:
                values = _tangodb[alphakey]
                new_values = value.split('/')
                for new_value in new_values:
                    if not new_value in values:
                        values.append(new_value)
            else:
                _tangodb[alphakey] = value.split('/')


class Expander():

    limit = 10

    def _expand_all(self, key, current, candidate):
        limit = self.limit
        for c, value in current:
            if len(candidate) >= limit:
                break
            if value == {}:
                candidate.append(key + c)
            else:
                self._expand_all(key + c, (x for x in value.items()), candidate)

    def _expand_sparse(self, key, current, candidate, generators):
        limit = self.limit
        for c, value in current:
            if len(candidate) >= limit:
                break
            if value == {}:
                candidate.append(key + c)
                return True
            generator = (x for x in value.items())
            if self._expand_sparse(key + c, generator, candidate, generators):
                generators.append((key, current))
                return True
        return False

    def expand(self, key, current, candidate):
        limit = settings.get('suggest.max')
        self.limit = limit
        generators = []
        for c in current:
            generator = (x for x in current[c].items())
            self._expand_sparse(key + c, generator, candidate, generators)
            if len(candidate) >= limit:
                break
        else:
            if len(candidate) < limit:
                for k, v in generators:
                    self._expand_all(k, v, candidate)
                    if len(candidate) >= limit:
                        break
                if len(candidate) < limit:
                    for c in current:
                        if not current[c]:
                            candidate.append(c)
                            if len(candidate) >= limit:
                                break
                elif not current:
                    candidate.append(key)


class Completer():

    def __init__(self):
        self._compdb = {}
        self._comp_value_db = {}
        self._expander = Expander()

    def register(self, key, value):
        current = self._compdb
        self._comp_value_db[key] = value
        for c in key:
            if c in current:
                current = current[c]
            else:
                new_current = {}
                current[c] = new_current
                current = new_current

    def suggest(self, key, finals):
        _current = self._compdb
        for _c in key:
            if _c in _current:
                _current = _current[_c]
            else:
                return None

        expander = self._expander

        candidate = list()
        if not finals:
            expander.expand(u'', _current, candidate)
        else:
            for _key in finals:
                key_len = len(_key)
                if key_len == 1:
                    if _key in _current:
                        expander.expand(_key, _current[_key], candidate)
                        if len(candidate) >= expander.limit:
                            break
                elif key_len == 2:
                    first, second = _key[0], _key[1]
                    if first in _current:
                        if second in _current[first]:
                            expander.expand(_key, _current[first][second], candidate)
                            if len(candidate) >= expander.limit:
                                break
        return candidate


completer = Completer()

_control_chars = re.compile('[\x00-\x1f\x7f\x80-\x9f\xff]')


def feedback(key, value):
    global user_dict_file
    if not key:
        return
    if key[0] == '@':
        return
    completer.register(key, value)
    if key in _user_tangodb:
        record = _user_tangodb[key]
        if value in record:
            record.remove(value)
        record.insert(0, value)
    else:
        _user_tangodb[key] = [value]
    if not user_dict_file:
        filename = '%d.tmp' % int(time.time())
        path = os.path.join(userdictdir, filename)
        user_dict_file = open(path, 'a+')
    record = '%s /%s/\n' % (key, value)
    user_dict_file.write(record.encode('utf-8'))
    user_dict_file.flush()
    logging.info("feedback: key=%s, value=%s" % (key, value))


def _escape(s):
    '''
    >>> _escape('abc')
    'abc'
    >>> _escape('lda\\x1baa\x10laa')
    'ldaaalaa'
    '''
    return _control_chars.sub('', s)


def _load_dict(filename):
    try:
        thread.start_new_thread(_load_dict_impl, (filename))
    except Exception:
        _load_dict_impl(filename)


def _load_dict_impl(filename):

    loader = SkkLineLoader()

    logging.info("load_dict: loading %s." % filename)
    try:
        for line in open(filename):
            loader.parse(line)
    except Exception, e:
        logging.exception(e)
        template = '_load_dict: loading process failed. filename: %s'
        logging.exception(template % filename)


def _get_fallback_dict_path(name):
    filename = inspect.getfile(inspect.currentframe())
    dirpath = os.path.abspath(os.path.dirname(filename))
    return os.path.join(dirpath, name)


def _load_history(filename):
    try:
        thread.start_new_thread(_load_history_impl, (filename))
    except Exception:
        _load_history_impl(filename)


def _load_history_impl(filename):
    for line in open(filename):
        value = _escape(line)
        key = _escape(line)
        if len(key) > 70:
            continue
        try:
            key = unicode(key, "utf-8")
        except UnicodeDecodeError:
            continue
        key = u'$' + key
        completer.register(key, value)
        if key in _tangodb:
            values = _tangodb[key]
            values.append(value)
        else:
            _tangodb[key] = [value]


def _load_user_dict():
    """
    >>> _load_user_dict()
    """
    import glob
    try:
        tmpdict_list = glob.glob(userdictdir + '/*.tmp')
    except Exception, e:
        logging.exception(e)

    for f in reversed(sorted(tmpdict_list)):
        try:
            _load_dict(os.path.join(userdictdir, f))
        except ImportError, e:
            logging.exception(e)

    try:
        userdict_list = glob.glob(userdictdir + '/*.dict')
    except Exception, e:
        logging.exception(e)

    for f in reversed(sorted(userdict_list)):
        try:
            _load_dict(os.path.join(userdictdir, f))
        except ImportError, e:
            logging.exception(e)

    if len(tmpdict_list) > 20:
        filename = '%d.dict' % int(time.time())
        f = open(os.path.join(userdictdir, filename), 'w')
        try:
            for key, value in _tangodb.items():
                entry = u'%s /%s/\n' % (key, u'/'.join(value))
                f.write(entry.encode('utf-8'))
        except Exception, e:
            logging.exception(e)
        finally:
            f.close()
        for f in tmpdict_list:
            try:
                os.remove(f)
            except OSError, e:
                logging.exception(e)

    for f in os.listdir(dictdir):
        try:
            _load_dict(os.path.join(dictdir, f))
        except ImportError, e:
            logging.exception(e)


def _load_builtin_dict():
    """
    >>> _load_user_dict()
    """
    try:
        _load_dict(_get_fallback_dict_path('SKK-JISYO.builtin'))
    except Exception, e:
        logging.exception(e)

    import rule
    template = "@ローマ字ルール /%s;builtin:settings:romanrule:'%s'/"
    try:
        loader = SkkLineLoader()
        for rulename in rule.list():
            try:
                ruledisplay, ruledict = rule.get(rulename)
                loader.parse(template % (ruledisplay, rulename))
            except ImportError, e:
                logging.exception(e)
    except Exception, e:
        logging.exception(e)

    try:
        _load_dict(_get_fallback_dict_path('SKK-JISYO.L'))
    except Exception, e:
        logging.exception(e)

    try:
        _load_dict(_get_fallback_dict_path('SKK-JISYO.JIS2'))
    except Exception, e:
        logging.exception(e)

    try:
        _load_dict(_get_fallback_dict_path('SKK-JISYO.assoc'))
    except Exception, e:
        logging.exception(e)

    try:
        _load_dict(_get_fallback_dict_path('SKK-JISYO.geo'))
    except Exception, e:
        logging.exception(e)

    try:
        _load_dict(_get_fallback_dict_path('SKK-JISYO.jinmei'))
    except Exception, e:
        logging.exception(e)

    if os.path.exists(bash_history_path):
        try:
            _load_history(bash_history_path)
        except Exception, e:
            logging.exception(e)

    if os.path.exists(zsh_history_path):
        try:
            _load_history(zsh_history_path)
        except Exception, e:
            logging.exception(e)

    logging.info("Dictionary initialization processes are completed.")


def gettango(key):
    if key in _user_tangodb:
        result = _user_tangodb[key]
        if key in _tangodb:
            values = _tangodb[key]
            for value in values:
                if not value in result:
                    result.append(value)
        return result
    if key in _tangodb:
        return _tangodb[key]
    return []


def getokuri(key):
    result = list()
    if key in _tangodb:
        result += _tangodb[key]
    return result


def suggest(key, finals):
    return completer.suggest(key, finals)


def _call_cgi_api_async(key, timeout, result):
    result['value'] = _call_cgi_api(key, timeout)


def _call_cgi_api(key, timeout):
    import json
    import socket
    import urllib
    import urllib2
    params = urllib.urlencode({'langpair': 'ja-Hira|ja',
                               'text': key.encode('UTF-8')})
    escaped_params = str(params)
    url = 'http://www.google.com/transliterate?' + escaped_params
    try:
        response = urllib2.urlopen(url, None, timeout)
        json_response = response.read()
        if not json_response:
            logging.exception('_call_cgi_api failed. %s' % key)
            return None
        response = json.loads(json_response)
    except urllib2.URLError, e:
        logging.exception(e)
        return None
    except socket.error, e:
        logging.exception(e)
        return None
    return response


def get_from_cgi_api(clauses, key):

    timeout = settings.get('cgi-api.timeout')

    if not timeout:
        timeout = 1.0

    try:
        import threading
        result = {}
        args = (key, timeout, result)
        t = threading.Thread(target=_call_cgi_api_async, args=args)
        t.setDaemon(True)
        t.start()
        if not t.isAlive():
            return None
        t.join(timeout)
        try:
            response = result['value']
        except KeyError:
            return None
    except ImportError, e:
        response = _call_cgi_api(key, timeout)

    if not response:
        return None

    try:
        for clauseinfo in response:
            key, cgi_candidates = clauseinfo
            candidates = gettango(key)
            for candidate in cgi_candidates:
                if not candidate in candidates:
                    candidates.append(candidate)
            clause = Clause(key, candidates)
            clauses.add(clause)
    except Exception, e:
        logging.exception(e)
        logging.exception('get_from_cgi_api failed. key: %s' % key)
        return None
    return clauses


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
            row = candidate.split(';')
            if len(row) == 2:
                value, remark = row
            else:
                value, remark = candidate, u''
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

    def __len__(self):
        return len(self._clauses)

    def add(self, clause):
        self._clauses.append(clause)

    def getkey(self):
        word = u''
        for clause in self._clauses:
            word += clause.getkey()
        return word

    def length(self):
        return len(self._clauses)

    def getvalue(self):
        word = u''
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

    def shift_left(self):

        words = []
        for clause in self._clauses:
            words.append(clause.getkey())

        index = self._index
        surplus = words[index][-1:] + u''.join(words[index + 1:])
        words[index] = words[index][:-1]
        words = words[0:index + 1] + [surplus]

        self._retry_cgi_api(words)

    def shift_right(self):

        words = []
        for clause in self._clauses:
            words.append(clause.getkey())

        index = self._index
        if index == len(words) - 1:
            words = words[:index] + [words[index][0], words[index][1:]]
        else:
            words[index] += words[index + 1][0]
            surplus = (''.join(words[index + 1:])[1:])
            words = words[:index + 1] + [surplus]

        self._retry_cgi_api(words)

    def _retry_cgi_api(self, words):
        timeout = settings.get('cgi-api.timeout')

        if not timeout:
            timeout = 1.0

        response = _call_cgi_api(','.join(words), timeout)
        if response:
            self._clauses = []
            for clauseinfo in response:
                key, candidates = clauseinfo
                clause = Clause(key, candidates)
                self.add(clause)
            if self._index >= len(self._clauses):
                self._index = len(self._clauses) - 1


def _create_dns_cache():
    import socket
    """
    create DNS cache for www.google.com
    """
    try:
        socket.gethostbyname('www.google.com')
        logging.info("DNS cache for www.google.com is created.")
    except socket.gaierror, e:
        logging.warning(e)


def initialize():
    # load dictionaries asynchronously if possible
    try:
        thread.start_new_thread(_create_dns_cache, ())
        thread.start_new_thread(_load_user_dict, ())
        thread.start_new_thread(_load_builtin_dict, ())
    except Exception, e:
        logging.warning(e)
        logging.warning("Fallback to synchronous initialization for dictionaries.")
        _load_user_dict()
        _load_builtin_dict()


def test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    test()
