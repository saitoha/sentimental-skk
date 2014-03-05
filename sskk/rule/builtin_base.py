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


_rule = {
    '\x00': u'@skk-cancel-pass',             # C-@ C-SP
    '\x01': u'@skk-cancel-pass',             # C-a
    '\x02': u'@skk-move-prev-clause',        # C-b
    '\x03': u'@skk-cancel-pass',             # C-c
    '\x04': u'@skk-cancel-pass',             # C-d
    '\x05': u'@skk-cancel-pass',             # C-e
    '\x06': u'@skk-move-next-clause',        # C-f
    '\x07': u'@skk-cancel',                  # C-g
    '\x08': u'@skk-back',                    # C-h BS
    '\x09': u'@skkmenu-next',                # C-i TAB
    '\x0a': u'@skk-kakutei-key',             # C-j
    '\x0b': u'@skk-cancel-pass',             # C-k
    '\x0c': u'@skk-cancel-pass',             # C-l
    '\x0d': u'@skk-kakutei-key',             # C-m Enter
    '\x0e': u'@skkmenu-next',                # C-n
    '\x0f': u'@skk-cancel-pass',             # C-o
    '\x10': u'@skkmenu-prev',                # C-p
    '\x11': u'@skk-set-henkan-point-subr',   # C-q
    '\x12': u'@skk-cancel-pass',             # C-r
    '\x13': u'@skk-cancel-pass',             # C-s
    '\x14': u'@skk-cancel-pass',             # C-t
    '\x15': u'@skk-cancel-pass',             # C-u
    '\x16': u'@skk-cancel-pass',             # C-v
    '\x17': u'@skkapp-wikipedia',            # C-w
    '\x18': u'@skk-delete-candidate',        # C-x
    '\x19': u'@skk-cancel-pass',             # C-y
    '\x1a': u'@skk-cancel-pass',             # C-z
    '\x1b': u'@skk-j-mode-off',              # C-[ ESC
    '\x1c': u'@skk-cancel-pass',             # C-\
    '\x1d': u'@skk-cancel-pass',             # C-]
    '\x1e': u'@skk-cancel-pass',             # C-^
    '\x1f': u'@skk-cancel-pass',             # C-_
    '\x20': u'@skk-henkan',                  # SP
    '\x7f': u'@skk-back',                    # DEL
    '/'   : u'@skk-abbrev-mode',
    'l'   : u'@skk-j-mode-off',
    'q'   : u'@skk-toggle-kana',
    'L'   : u'@skk-start-eisuu',
    'wws' : u'@skkwm-switch',
    'wwn' : u'@skkwm-next',
    'wwp' : u'@skkwm-prev',
    'wwd' : u'@skkwm-blur',
    'wwh' : u'@skkwm-left',
    'wwj' : u'@skkwm-down',
    'wwk' : u'@skkwm-up',
    'wwl' : u'@skkwm-right',
    'w4'  : u'@skksh-start',
    '$'   : u'@skksh-start',
    '@'   : u'@skkconf-start',
}


def get():
    """
    >>> name, rule = get()
    """
    return 'base', _rule


def test():
    import doctest
    doctest.testmod()


if __name__ == "__main__":
    test()
