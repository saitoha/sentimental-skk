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

import tff

import title
import os

################################################################################
#
# OutputHandler
#
class OutputHandler(tff.DefaultHandler):

    def __init__(self, use_title=False, mode_handler=None):
        self.__super = super(OutputHandler, self)
        self.__use_title = use_title
        self._mode_handler = mode_handler

    def handle_start(self, context):
        self.__super.handle_start(context)

    def handle_end(self, context):
        if self.__use_title:
            context.writestring(u'\x1b]0;／^o^＼\x07')
        self.__super.handle_end(context)

    def handle_esc(self, context, intermediate, final):
        if not self._mode_handler is None:
            return self._mode_handler.handle_esc(context, intermediate, final)
        return False

    def handle_csi(self, context, parameter, intermediate, final):
        if not self._mode_handler is None:
            return self._mode_handler.handle_csi(context, parameter, intermediate, final)
        return False

    def handle_control_string(self, context, prefix, value):
        if self.__use_title:
            if prefix == 0x5d: # ']'
                try:
                    pos = value.index(0x3b)
                except ValueError:
                    return 
                if pos == -1:
                    return
                elif pos == 0:
                    num = [0]
                else:
                    try:
                        num = value[:pos]
                    except:
                        num = None 
                if not num is None:
                    if num == [0x30] or num == [0x32]:
                        arg = value[pos + 1:]
                        title.setoriginal(u''.join([unichr(x) for x in arg]))
                        s = title.get()
                        if s:
                            value = num + [0x3b] + [ord(x) for x in s]
                            new_title = u"".join([unichr(c) for c in value])
                            context.writestring(u"\x1b]%s\x1b\\" % new_title)
        return False


