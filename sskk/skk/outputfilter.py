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


################################################################################
#
# OutputHandler
#
class OutputHandler(tff.DefaultHandler):

    def __init__(self):
        self.__super = super(OutputHandler, self)

    def handle_start(self, context):
        self.__super.handle_start(context)

    def handle_end(self, context):
        context.write(u'\x1b]0;／^o^＼\x07')
        self.__super.handle_end(context)

    def handle_control_string(self, context, prefix, value):
        if prefix == 0x5d: # ']'
            try:
                pos = value.index(0x3b)
            except ValueError:
                pass 
            if pos == -1:
                pass
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
                    value = num + [0x3b] + [ord(x) for x in title.get()]



