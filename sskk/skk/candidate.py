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

import sys
import wcwidth
try:
    from CStringIO import StringIO
except:
    from StringIO import StringIO

_POPUP_NORMALDIR = True
_POPUP_REVERSEDIR = False

################################################################################
#
# CandidateManager
#
class CandidateManager():

    __list = None
    __movedir = _POPUP_NORMALDIR
    __scrollpos = 0

    width = 10
    height = 5

    def __init__(self, screen):
        self.__screen = screen
        self.reset()

    def assign(self, key, value=[], okuri=u''):
        self.__index = 0
        self.__key = key
        self.__list = value
        self.__okuri = okuri

    def reset(self):
        self.__index = 0
        self.__list = None
        self.__okuri = None
        self.__key = None
        self.__movedir = _POPUP_NORMALDIR
        self.width = 8
        self.height = 0
        self.__scrollpos = 0
        return u''

    def isempty(self):
        return self.__list == None

    def getyomi(self):
        return self.__key

    def getcurrent(self, kakutei=False):
        length = len(self.__list) # 候補数
        if self.__index == length:
            value = self.__key
        else:
            value = self.__list[self.__index]
            if kakutei:
                self.__list.insert(0, self.__list.pop(self.__index))

        # 補足説明
        index = value.find(u";")
        if index >= 0:
            result = value[:index]
            remarks = value[index:]
        else:
            result = value
            remarks = None

        return result + self.__okuri, remarks 

    def getwidth(self):
        if self.isempty():
            return 0
        result, remarks = self.getcurrent()
        main_length = wcwidth.wcswidth(result)
        if len(self.__okuri) == 0:
            return main_length
        else:
            return main_length + wcwidth.wcswidth(self.__okuri)

    def movenext(self):
        length = len(self.__list) # 候補数
        if self.__index < length:
            self.__movedir = _POPUP_NORMALDIR
            self.__index += 1
            if self.__index - 4 > self.__scrollpos:
                self.__scrollpos = self.__index - 4

    def moveprev(self):
        if self.__index > 0:
            self.__movedir = _POPUP_REVERSEDIR
            self.__index -= 1
            if self.__index < self.__scrollpos:
                self.__scrollpos = self.__index

    def __getdisplayinfo(self, vdirection):
        width = self.width
        l = self.__list
        if len(l) > 5:
            l = l[self.__scrollpos:self.__scrollpos + 5]
            pos = self.__index - self.__scrollpos
        else:
            pos = self.__index

        for value in l:
            width = max(width, wcwidth.wcswidth(value) + 6)

        width = max(self.width, width)
        self.width = width
        self.height = min(5, len(l))
        if self.__screen.cursor.col + width > self.__screen.width:
            offset = self.__screen.cursor.col + width - self.__screen.width + 1
        else:
            offset = 0
        return l, pos, width, offset

    def __getdirection(self):
        screen = self.__screen
        if screen.cursor.row * 2 > screen.height:
            vdirection = _POPUP_REVERSEDIR
        else:            
            vdirection = _POPUP_NORMALDIR 
        return vdirection

    def getselections(self):
        if self.__index >= len(self.__list):
            self.erase()
            return u''
        vdirection = self.__getdirection()
        l, pos, width, offset = self.__getdisplayinfo(self.__movedir)
        s = StringIO()
        if vdirection:
            s.write(u'\x1b[B')
        else:
            s.write(u'\x1b[%dA' % self.height)
        if offset > 0:
            s.write(u'\x1b[%dD' % offset)
        for i, value in enumerate(l):
            s.write(u'\x1b[41m')
            if i == pos:
                s.write(u'\x1b[42m')
            s.write(u' ' * width + u'\x1b[%dD' % width)
            if i == pos:
                s.write(u'\x1b[1;42m')
            s.write(value + u'\x1b[%dD' % wcwidth.wcswidth(value))
            if i == pos:
                s.write(u'\x1b[41m')
            s.write(u'\x1b[B')
            s.write(u'\x1b[m')
        if vdirection:
            s.write(u'\x1b[%dA' % (self.height + 1))
        else:
            pass
        return s.getvalue()

    def erase(self):
        if self.__screen.cursor.col + self.width >= self.__screen.width:
            offset = self.__screen.cursor.col + self.width - self.__screen.width + 2
        else:
            offset = 0
        vdirection = self.__getdirection()
        screen = self.__screen
        x = screen.cursor.col - offset 
        if vdirection == _POPUP_NORMALDIR:
            y = screen.cursor.row + 1
        else:
            y = screen.cursor.row - self.height
        w = self.width + 2
        h = self.height
        sys.stdout.write("\x1b7")
        screen.drawrect(x, y, w, h)
        sys.stdout.write("\x1b8")
         
    def clear(self):
        self.erase()
        self.reset()

