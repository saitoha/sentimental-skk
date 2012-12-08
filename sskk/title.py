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

_enabled = True
_mode = u'@'
_message = u''
_original = u''

def get():
    if _enabled:
        if _mode:
            return u'%s   [%s] %s' % (_original, _mode, _message)
        return u'%s   %s' % (_original, _message)

def setenabled(value):
    global _enabled
    _enabled = value

def setmode(value):
    global _mode
    _mode = value

def setmessage(value):
    global _message
    _message = value

def setoriginal(value):
    global _original
    _original = value



