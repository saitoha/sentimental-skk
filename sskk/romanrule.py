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

import kanadb
import rule
import logging

SKK_ROMAN_VALUE = 65540
SKK_ROMAN_NEXT = 65541
SKK_ROMAN_PREV = 65542
SKK_ROMAN_BUFFER = 65543


def _maketree(rule, onbin, txu, nn):
    """ makes try-tree """
    tree = {}

    for key, value in rule.items():
        buf = u''
        context = tree
        for c in key:
            code = ord(c)
            if not code in context:
                context[code] = {SKK_ROMAN_PREV: context}
            context = context[code]
            buf += chr(code)
            context[SKK_ROMAN_BUFFER] = buf
        context[SKK_ROMAN_VALUE] = value
        first = key[0]
        if first in onbin:
            key = first + key
            value = txu + value
            buf = u''
            context = tree
            for c in key:
                code = ord(c)
                if not code in context:
                    context[code] = {SKK_ROMAN_PREV: context}
                context = context[code]
                if buf == chr(code):
                    buf = txu
                buf += chr(code)
                context[SKK_ROMAN_BUFFER] = buf

            context[SKK_ROMAN_VALUE] = value

    for key, value in tree.items():
        context = tree
        if key == 0x6e:  # 'n'
            for c in onbin:
                code = ord(c)
                value[code] = {SKK_ROMAN_VALUE: nn,
                               SKK_ROMAN_NEXT: tree[code]}
    tree[SKK_ROMAN_BUFFER] = u''
    tree[SKK_ROMAN_PREV] = tree
    return tree


def _make_rules(rule):
    hira_rule = rule
    kata_rule = {}
    for key, value in hira_rule.items():
        kata_rule[key] = kanadb.to_kata(value)
    return (hira_rule, kata_rule)


def compile(method="builtin_normal"):
    ''' make hiragana/katakana input state trie-tree
    >>> hira_tree, kata_tree = compile('builtin_normal')
    >>> hira_tree[ord('k')][ord('y')][ord('a')][SKK_ROMAN_VALUE]
    u'\u304d\u3083'
    >>> hira_tree[ord('t')][ord('t')][ord('a')][SKK_ROMAN_VALUE]
    u'\u3063\u305f'
    >>> kata_tree[ord('k')][ord('y')][ord('a')][SKK_ROMAN_VALUE]
    u'\u30ad\u30e3'
    >>> hira_tree, kata_tree = compile('builtin_azik')
    >>> hira_tree[ord('k')][ord('y')][ord('a')][SKK_ROMAN_VALUE]
    u'\u304d\u3083'
    >>> kata_tree[ord('k')][ord('y')][ord('a')][SKK_ROMAN_VALUE]
    u'\u30ad\u30e3'
    >>> hira_tree, kata_tree = compile('builtin_act')
    >>> hira_tree[ord('c')][ord('g')][ord('a')][SKK_ROMAN_VALUE]
    u'\u304d\u3083'
    >>> kata_tree[ord('c')][ord('g')][ord('a')][SKK_ROMAN_VALUE]
    u'\u30ad\u30e3'
    '''

    logging.info("compile roman rule: %s" % method)

    _base_name, base_ruledict = rule.get('builtin_base')
    name, ruledict = rule.get(method)

    ruledict.update(base_ruledict)

    hira_rule, kata_rule = _make_rules(ruledict)
    if method == 'builtin_normal':
        onbin = 'bcdfghjkmprstvwxz'
    else:
        onbin = 'w'

    _hira_tree = _maketree(hira_rule, onbin, u'っ', u'ん')
    _kata_tree = _maketree(kata_rule, onbin, u'ッ', u'ン')

    return (_hira_tree, _kata_tree)


def test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()
