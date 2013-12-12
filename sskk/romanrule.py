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
import logging

SKK_ROMAN_VALUE = 0
SKK_ROMAN_NEXT = 1
SKK_ROMAN_PREV = 2
SKK_ROMAN_BUFFER = 3

def _maketree(rule, s, txu, nn):
    """ makes try-tree """
    tree = {}

    for key, value in rule.items():
        buf = u''
        context = tree
        for code in [ord(c) for c in key]:
            if not code in context:
                context[code] = {SKK_ROMAN_PREV: context}
            context = context[code]
            buf += chr(code)
            context[SKK_ROMAN_BUFFER] = buf
        context[SKK_ROMAN_VALUE] = value
        first = key[0]
        if first in s:
            key = first + key
            value = txu + value
            buf = u''
            context = tree
            for code in [ord(c) for c in key]:
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
            for code in [ord(c) for c in s]:
                value[code] = {SKK_ROMAN_VALUE: nn,
                               SKK_ROMAN_NEXT: tree[code]}
    tree[SKK_ROMAN_BUFFER] = ''
    tree[SKK_ROMAN_PREV] = tree
    return tree

def _make_rules(rule):
    hira_rule = rule
    kata_rule = {}
    for key, value in hira_rule.items():
        kata_rule[key] = kanadb.to_kata(value)
    return (hira_rule, kata_rule)

def compile_normal():
    ''' make hiragana/katakana input state trie-tree
    >>> hira_tree, kata_tree = compile_normal()
    >>> hira_tree[ord('k')][ord('y')][ord('a')][SKK_ROMAN_VALUE]
    u'\u30ad\u30e3'
    >>> kata_tree[ord('k')][ord('y')][ord('a')][SKK_ROMAN_VALUE]
    u'\u304d\u3083'
    '''

    import rule.normal
    hira_rule, kata_rule = _make_rules(rule.normal.get())

    _hira_tree = _maketree(hira_rule, 'bcdfghjkmprstvwxz', u'っ', u'ん')
    _kata_tree = _maketree(kata_rule, 'bcdfghjkmprstvwxz', u'ッ', u'ン')
    return (_hira_tree, _kata_tree)


def compile_azik():
    ''' make hiragana/katakana input state trie-tree
    >>> hira_rule, kata_rule = _make_rules(rule.azik.get())
    >>> t = _maketree(kata_rule, 'w', u'っ', u'ん')
    >>> t[ord('k')][ord('y')][ord('a')][SKK_ROMAN_VALUE]
    u'\u30ad\u30e3'
    >>> t = _maketree(hira_rule, 'w', u'ッ', u'ン')
    >>> t[ord('k')][ord('y')][ord('a')][SKK_ROMAN_VALUE]
    u'\u304d\u3083'
    '''

    import rule.azik
    hira_rule, kata_rule = _make_rules(rule.azik.get())

    _hira_tree = _maketree(hira_rule, 'w', u'っ', u'ん')
    _kata_tree = _maketree(kata_rule, 'w', u'ッ', u'ン')
    return (_hira_tree, _kata_tree)


def compile_act():
    ''' make hiragana/katakana input state trie-tree
    >>> hira_rule, kata_rule = _make_rules(_rule_act)
    >>> t = _maketree(kata_rule, 'w', u'っ', u'ん')
    >>> t[ord('c')][ord('g')][ord('a')][SKK_ROMAN_VALUE]
    u'\u30ad\u30e3'
    >>> t = _maketree(hira_rule, 'w', u'ッ', u'ン')
    >>> t[ord('c')][ord('g')][ord('a')][SKK_ROMAN_VALUE]
    u'\u304d\u3083'
    '''

    import rule.act
    hira_rule, kata_rule = _make_rules(rule.act.get())

    _hira_tree = _maketree(hira_rule, 'w', u'っ', u'ん')
    _kata_tree = _maketree(kata_rule, 'w', u'ッ', u'ン')
    return (_hira_tree, _kata_tree)


def compile(method="normal"):
    if method == "azik":
        return compile_azik()
    elif method == "act":
        return compile_act()
    elif method == "normal":
        return compile_normal()
    elif method is None:
        return compile_normal()
    else:
        logging.warning("Unknown Roman Rule: " + method)

def test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()
