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

def _param_generator(params, minimum, offset, maxarg):
    for p in ''.join([chr(p) for p in params]).split(';')[:maxarg]:
        if p == '':
            yield minimum 
        else:
            yield max(minimum, int(p) + offset)
 
def _parse_params(params, minimum=0, offset=0, minarg=1, maxarg=255):
   if len(params) < minarg:
        return [minimum] * minarg
   return [param for param in _param_generator(params, minimum, offset, maxarg)]


################################################################################
#
# OutputHandler
#
class OutputHandler(tff.DefaultHandler):

    def __init__(self,
                 use_title=False,
                 use_mouse=False,
                 mouse_mode=None):
        self.__super = super(OutputHandler, self)
        self.__use_title = use_title
        self.__use_mouse = use_mouse
        self.__mouse_mode = mouse_mode

    def handle_start(self, context):
        self.__super.handle_start(context)

    def handle_end(self, context):
        if self.__use_title:
            context.writestring(u'\x1b]0;／^o^＼\x07')
        self.__super.handle_end(context)

    def handle_esc(self, context, intermediate, final):
        if self.__use_mouse:
            if final == 0x63 and len(intermediate) == 0:
                self.__mouse_mode.protocol = 0
                self.__mouse_mode.encoding = 0
            # TODO DECTSR support
        return False

    def handle_csi(self, context, parameter, intermediate, final):
        if self.__use_mouse:
            if len(parameter) > 0:
                if parameter[0] == 0x3f and len(intermediate) == 0:
                    params = _parse_params(parameter[1:])
                    if final == 0x68: # 'h'
                        modes = []
                        for param in params:
                            if param == 1000:
                                self.__mouse_mode.protocol = 1000 
                            elif param == 1001:
                                self.__mouse_mode.protocol = 1001 
                            elif param == 1002:
                                self.__mouse_mode.protocol = 1002 
                            elif param == 1003:
                                self.__mouse_mode.protocol = 1003 
                            elif param == 1005:
                                self.__mouse_mode.encoding = 1005 
                            elif param == 1015:
                                self.__mouse_mode.encoding = 1015 
                            elif param == 1006:
                                self.__mouse_mode.encoding = 1006 
                            else:
                                modes.append(str(param))
                        if len(modes) > 0:
                            context.writestring("\x1b[?%sh" % ";".join(modes))
                        return True
                    elif final == 0x6c: # 'l'
                        modes = []
                        for param in params:
                            if param == 1000:
                                self.__mouse_mode.protocol = 0
                            elif param == 1001:
                                self.__mouse_mode.protocol = 0
                            elif param == 1002:
                                self.__mouse_mode.protocol = 0
                            elif param == 1003:
                                self.__mouse_mode.protocol = 0
                            elif param == 1005:
                                self.__mouse_mode.encoding = 0
                            elif param == 1015:
                                self.__mouse_mode.encoding = 0
                            elif param == 1006:
                                self.__mouse_mode.encoding = 0
                            else:
                                modes.append(str(param))
                        if len(modes) > 0:
                            context.writestring("\x1b[?%sl" % ";".join(modes))
                        return True
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


