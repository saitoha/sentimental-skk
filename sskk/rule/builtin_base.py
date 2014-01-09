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
    '1s': u'@task_switch',
    '1n': u'@task_next',
    '1p': u'@task_prev',
    '1d': u'@task_blur',
    '4' : u'@shell_start',
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
