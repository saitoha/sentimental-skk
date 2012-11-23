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

_POPUP_DIR_NORMAL = True
_POPUP_DIR_REVERSE = False
_POPUP_HEIGHT = 10

################################################################################
#
# CandidateManager
#
class CandidateManager():

    __list = None
    __movedir = _POPUP_DIR_NORMAL
    __scrollpos = 0
    __show = False 

    left = None
    top = None
    width = 10
    height = _POPUP_HEIGHT 
    offset_left = 0
    offset_top = 0

    def __init__(self, screen, is_cjk=False, mouse_mode=None):
        if is_cjk:
            self._wcswidth = wcwidth.wcswidth_cjk
        else:
            self._wcswidth = wcwidth.wcswidth
        self.__screen = screen
        self.__mouse_mode = mouse_mode
        self.reset()

    def assign(self, key, value=None, okuri=u''):
        self.__index = 0
        self.__key = key
        if value:
            self.__list = value.split(u"/")
        else:
            self.__list = [] 
        self.__okuri = okuri

    def reset(self):
        self.__index = 0
        self.__list = None
        self.__okuri = None
        self.__key = None
        self.__movedir = _POPUP_DIR_NORMAL
        self.width = 8
        self.height = 0
        self.left = None
        self.top = None
        self.offset_left = 0
        self.offset_top = 0
        self.__scrollpos = 0
        return u''

    def isempty(self):
        return self.__list == None

    def isshown(self):
        return self.__show

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
        main_length = self._wcswidth(result)
        if len(self.__okuri) == 0:
            return main_length
        else:
            return main_length + self._wcswidth(self.__okuri)

    def includes(self, x, y):
        if not self.isshown():
            return False
        elif x < self.left:
            return False
        elif x >= self.left + self.width:
            return False
        elif y < self.top:
            return False
        elif y >= self.top + self.height:
            return False
        return True

    def movenext(self):
        length = len(self.__list) # 候補数
        if self.__index < length:
            self.__movedir = _POPUP_DIR_NORMAL
            self.__index += 1
            if self.__index - _POPUP_HEIGHT + 1 > self.__scrollpos:
                self.__scrollpos = self.__index - _POPUP_HEIGHT + 1 

    def moveprev(self):
        if self.__index > 0:
            self.__movedir = _POPUP_DIR_REVERSE
            self.__index -= 1
            if self.__index < self.__scrollpos:
                self.__scrollpos = self.__index

    def position_is_selected(self, y):
        n = y - self.top
        return self.__scrollpos + n == self.__index

    def click(self, x, y):
        n = y - self.top
        while self.__scrollpos + n < self.__index:
            self.moveprev()
        while self.__scrollpos + n > self.__index:
            self.movenext()

    def __truncate_str(self, s, length):
        if self._wcswidth(s) > length:
            return s[:length] + u"..."
        return s

    def __getdisplayinfo(self, vdirection):
        width = 0
        l = [self.__truncate_str(s, 20) for s in self.__list]

        if len(l) > _POPUP_HEIGHT:
            l = l[self.__scrollpos:self.__scrollpos + _POPUP_HEIGHT]
            pos = self.__index - self.__scrollpos
        else:
            pos = self.__index

        for value in l:
            width = max(width, self._wcswidth(value) + 6)

        #width = max(self.width, width)
        height = min(_POPUP_HEIGHT, len(l))
        if self.__screen.cursor.col + width > self.__screen.width:
            offset = self.__screen.cursor.col + width - self.__screen.width + 1
        else:
            offset = 0

        y = self.__screen.cursor.row
        x = self.__screen.cursor.col

        if self.__getdirection(y):
            top = y + 1
        else:
            top = y - height

        if offset > 0:
            left = x - offset
        else:
            left = x

        return l, pos, left, top, width, height

    def __getdirection(self, row):
        screen = self.__screen
        if row * 2 > screen.height:
            vdirection = _POPUP_DIR_REVERSE
        else:            
            vdirection = _POPUP_DIR_NORMAL 
        return vdirection

    def set_offset(self, s, offset_x, offset_y):
        screen = self.__screen
        if self.left + offset_x < 0:
            offset_x = 0 - self.left
        elif self.left + self.width + offset_x > screen.width:
            offset_x = self.__screen.width - self.left - self.width
        if self.top + offset_y < 0:
            offset_y = 0 - self.top
        elif self.top + self.height + offset_y > screen.height:
            offset_y = self.__screen.height - self.top - self.height
        if self.offset_left == offset_x:
            if self.offset_top == offset_y:
                return

        if self.offset_left < offset_x:
            screen.drawrect(s,
                            self.left + self.offset_left,
                            self.top + self.offset_top,
                            offset_x - self.offset_left,
                            self.height)
        elif self.offset_left > offset_x:
            screen.drawrect(s,
                            self.left + self.width + offset_x,
                            self.top + self.offset_top,
                            self.offset_left - offset_x,
                            self.height)

        if self.offset_top < offset_y:
            screen.drawrect(s,
                            self.left + self.offset_left,
                            self.top + self.offset_top,
                            self.width,
                            offset_y - self.offset_top)
        elif self.offset_top > offset_y:
            screen.drawrect(s,
                            self.left + self.offset_left,
                            self.top + self.height + offset_y,
                            self.width,
                            self.offset_top - offset_y)

        self.offset_left = offset_x
        self.offset_top = offset_y 
        y = self.__screen.cursor.row
        x = self.__screen.cursor.col
        s.write(u'\x1b[%d;%dH' % (y + 1, x + 1))


    def draw(self, s):
        if self.__index >= len(self.__list):
            self.erase(s)
            return u''
        l, pos, left, top, width, height = self.__getdisplayinfo(self.__movedir)

        if not self.left is None:
            if self.left < left:
                self.__screen.drawrect(s,left,
                                       top,
                                       self.left - left,
                                       height)
            if self.left + self.width > left + width:
                self.__screen.drawrect(s,
                                       left + width,
                                       top,
                                       self.left + self.width - (left + width),
                                       height)
        else:
            self.__mouse_mode.set_on(s)
        self.left = left 
        self.top = top 
        self.width = width
        self.height = height

        left += self.offset_left
        top += self.offset_top

        for i, value in enumerate(l):
            if i == pos: # 選択行
                s.write(u'\x1b[0;1;37;42m')
            else: # 非選択行
                s.write(u'\x1b[0;1;37;41m')
            s.write(u'\x1b[%d;%dH' % (top + 1 + i, left + 1))
            s.write(u' ' * width)
            if i == pos: s.write(u'\x1b[1;42m')
            s.write(u'\x1b[%d;%dH' % (top + 1 + i, left + 1))
            s.write(value)
            if i == pos: s.write(u'\x1b[41m')
            s.write(u'\x1b[m')

        y = self.__screen.cursor.row
        x = self.__screen.cursor.col
        s.write(u'\x1b[%d;%dH' % (y + 1, x + 1))
        self.__show = True

    def erase(self, s):
        if not self.left is None: 
            self.__screen.drawrect(sys.stdout,
                                   self.left + self.offset_left,
                                   self.top + self.offset_top,
                                   self.width,
                                   self.height)

        x = self.__screen.cursor.col
        y = self.__screen.cursor.row
        s.write(u"\x1b[%d;%dH" % (y + 1, x + 1))
        self.__show = False
         
    def clear(self, s):
        self.erase(s)
        self.__mouse_mode.set_off(s)
        self.reset()

