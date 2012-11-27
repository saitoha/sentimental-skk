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
_POPUP_HEIGHT_MAX = 24

_SKK_MARK_SELECT = u'▼ '


################################################################################
#
# CandidateManager
#
class CandidateManager():

    __list = None
    __movedir = _POPUP_DIR_NORMAL
    __scrollpos = 0
    __show = False 
    __mouse_mode = None 

    _prevwidth = 0

    left = None
    top = None
    width = 10
    height = _POPUP_HEIGHT_MAX
    offset_left = 0
    offset_top = 0

    def __init__(self, screen, is_cjk=False, mouse_mode=None):
        if is_cjk:
            self._wcswidth = wcwidth.wcswidth_cjk
        else:
            self._wcswidth = wcwidth.wcswidth
        self._screen = screen
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
            # 確定した候補を前にもってくる
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
        main_length = self._wcswidth(_SKK_MARK_SELECT) + self._wcswidth(result)
        if len(self.__okuri) == 0:
            return main_length
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

    def safe_movenext(self):
        length = len(self.__list) # 候補数
        if self.__index < length - 1:
            self.movenext()

    def movenext(self):
        length = len(self.__list) # 候補数
        if self.__index < length:
            self.__movedir = _POPUP_DIR_NORMAL
            self.__index += 1
            if self.__index - self.height + 1 > self.__scrollpos:
                self.__scrollpos = self.__index - self.height + 1 

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

    def __getdisplayinfo(self):
        width = 0
        l = [self.__truncate_str(s, 20) for s in self.__list]

        y, x = self._screen.getyx()

        vdirection = self._getdirection(y)
        if vdirection == _POPUP_DIR_NORMAL:
            height = self._screen.height - (y + 1) 
        else:
            height = y 

        height = min(height, _POPUP_HEIGHT_MAX)

        if len(l) > height:
            l = l[self.__scrollpos:self.__scrollpos + height]
            pos = self.__index - self.__scrollpos
        else:
            pos = self.__index

        for value in l:
            width = max(width, self._wcswidth(value) + 6)

        #width = max(self.width, width)
        height = min(height, len(l))

        if x + width > self._screen.width:
            offset = x + width - self._screen.width + 1
        else:
            offset = 0

        if vdirection == _POPUP_DIR_NORMAL:
            top = y + 1
        else:
            top = y - height

        if offset > 0:
            left = x - offset
        else:
            left = x

        return l, pos, left, top, width, height

    def _getdirection(self, row):
        screen = self._screen
        if row * 2 > screen.height:
            vdirection = _POPUP_DIR_REVERSE
        else:            
            vdirection = _POPUP_DIR_NORMAL 
        return vdirection

    def set_offset(self, s, offset_x, offset_y):
        screen = self._screen
        if self.left + offset_x < 0:
            offset_x = 0 - self.left
        elif self.left + self.width + offset_x > screen.width:
            offset_x = self._screen.width - self.left - self.width
        if self.top + offset_y < 0:
            offset_y = 0 - self.top
        elif self.top + self.height + offset_y > screen.height:
            offset_y = self._screen.height - self.top - self.height

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
        y, x = self._screen.getyx()
        s.write(u'\x1b[%d;%dH' % (y + 1, x + 1))


    def draw(self, s):
        result, remarks = self.getcurrent()
        result = _SKK_MARK_SELECT + result

        if self.__index >= len(self.__list):
            self.erase(s)
            s.write(u'\x1b[1;4;31m%s\x1b[m\x1b[?25l' % result)
            return 

        y, x = self._screen.getyx()
        s.write(u'\x1b[%d;%dH\x1b[1;4;31m%s\x1b[m\x1b[?25l' % (y + 1, x + 1, result))

        cur_width = self._wcswidth(result) 
        if self.isshown():
            if self._prevwidth > cur_width:
                s.write(u" " * (self._prevwidth - cur_width))
        self._prevwidth = cur_width

        l, pos, left, top, width, height = self.__getdisplayinfo()

        if not self.left is None:
            if self.left < left:
                self._screen.drawrect(s, self.left, top, left - self.left, height)
            if self.left + self.width > left + width:
                self._screen.drawrect(s, left + width, top, self.left + self.width - (left + width), height)
        elif not self.__mouse_mode is None:
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

        s.write(u'\x1b[%d;%dH' % (y + 1, x + 1))
        self.__show = True

    def erase(self, s):
        y, x = self._screen.getyx()
        s.write(u"\x1b[%d;%dH" % (y + 1, x + 1))
        s.write(u" " * self._prevwidth)

        if self.isshown(): 
            self.__show = False
            self._screen.drawrect(sys.stdout,
                                  self.left + self.offset_left,
                                  self.top + self.offset_top,
                                  self.width,
                                  self.height)

        s.write(u"\x1b[%d;%dH" % (y + 1, x + 1))
         
    def clear(self, s):
        self.erase(s)
        if not self.__mouse_mode is None:
            self.__mouse_mode.set_off(s)
        self.reset()

