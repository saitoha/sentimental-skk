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

#import thread

_eisuudb = ((u'0', u'０'), (u'1', u'１'), (u'2', u'２'),
            (u'3', u'３'), (u'4', u'４'), (u'5', u'５'),
            (u'6', u'６'), (u'7', u'７'), (u'8', u'８'),
            (u'9', u'９'), (u'^', u'＾'), (u'@', u'＠'),
            (u'[', u'［'), (u']', u'］'), (u':', u'：'),
            (u';', u'；'), (u',', u'，'), (u'.', u'．'),
            (u'/', u'／'), (u'_', u'＿'), (u'*', u'＊'),
            (u'!', u'！'), (u'#', u'＃'), (u'$', u'＄'),
            (u'%', u'％'), (u'&', u'＆'), (u'(', u'（'),
            (u')', u'）'), (u'=', u'＝'), (u'~', u'〜'),
            (u'|', u'｜'), (u'{', u'｛'), (u'}', u'｝'),
            (u'+', u'＋'), (u'*', u'＊'), (u'<', u'＜'),
            (u'>', u'＞'), (u'?', u'？'), (u'A', u'Ａ'),
            (u'B', u'Ｂ'), (u'C', u'Ｃ'), (u'D', u'Ｄ'),
            (u'E', u'Ｅ'), (u'F', u'Ｆ'), (u'G', u'Ｇ'),
            (u'H', u'Ｈ'), (u'I', u'Ｉ'), (u'J', u'Ｊ'),
            (u'K', u'Ｋ'), (u'L', u'Ｌ'), (u'M', u'Ｍ'),
            (u'N', u'Ｎ'), (u'O', u'Ｏ'), (u'P', u'Ｐ'),
            (u'Q', u'Ｑ'), (u'R', u'Ｒ'), (u'S', u'Ｓ'),
            (u'T', u'Ｔ'), (u'U', u'Ｕ'), (u'V', u'Ｖ'),
            (u'W', u'Ｗ'), (u'X', u'Ｘ'), (u'Y', u'Ｙ'),
            (u'Z', u'Ｚ'), (u'a', u'ａ'), (u'b', u'ｂ'),
            (u'c', u'ｃ'), (u'd', u'ｄ'), (u'e', u'ｅ'),
            (u'f', u'ｆ'), (u'g', u'ｇ'), (u'h', u'ｈ'),
            (u'i', u'ｉ'), (u'j', u'ｊ'), (u'k', u'ｋ'),
            (u'l', u'ｌ'), (u'm', u'ｍ'), (u'n', u'ｎ'),
            (u'o', u'ｏ'), (u'p', u'ｐ'), (u'q', u'ｑ'),
            (u'r', u'ｒ'), (u's', u'ｓ'), (u't', u'ｔ'),
            (u'u', u'ｕ'), (u'v', u'ｖ'), (u'w', u'ｗ'),
            (u'x', u'ｘ'), (u'y', u'ｙ'), (u'z', u'ｚ'),
            (u' ', u'　'))

_han_to_zen = {}
_han_to_zen_cp = {}


def _loaddb():
    for han, zen in _eisuudb:
        _han_to_zen[han] = zen
        _han_to_zen_cp[ord(han)] = ord(zen)


def to_zenkaku(s):
    """
    convert ascii string to Japanese Zenkaku string

    >>> _loaddb()
    >>> to_zenkaku("0")
    u'\uff10'
    >>> to_zenkaku("a")
    u'\uff41'
    >>> to_zenkaku("ABC")
    u'\uff21\uff22\uff23'
    """
    def conv(c):
        if c in _han_to_zen:
            return _han_to_zen[c]
        return c
    return ''.join([conv(c) for c in s])


def to_zenkaku_cp(code):
    """
    convert some ascii code points to Japanese Zenkaku code points

    >>> _loaddb()
    >>> hex(to_zenkaku_cp(40))
    '0xff08'
    >>> hex(to_zenkaku_cp(84))
    '0xff34'
    """
    if code in _han_to_zen_cp:
        return _han_to_zen_cp[code]
    return code

#thread.start_new_thread(_loaddb, ())
_loaddb()


def test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()
