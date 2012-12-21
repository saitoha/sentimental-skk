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

import title
from popup import IModeListener

'''

 既存の実装をいろいろ動かしてみたところ、
 モード遷移はおおむね以下のようになっていると理解しました。

 /(シングルシフト)というのは、一回のみのトグルという意味で使っています。
 つまり、確定するなどして英数変換入力が終わると、
 元の状態(ひらがなモードまたはカタカナモード)に戻ります。

                   +----------+ 
                   | 英数サブ |  /(シングルシフト) 
                   | 変換入力 | <-------------+
                   +----------+               |
                       ^                      |
                       | /(シングルシフト)    |
                       |                      |
+---------+  C-j   +----------+    q    +----------+
|  ASCII  | -----> | ひらがな | ------> | カタカナ |
| 直接入力| <----- | 変換入力 | <------ | 変換入力 |
+---------+   l    +----------+    q    +----------+
                       ^  |                   |
                   C-j |  | L                 |
                       |  v                   |
                   +----------+               |
                   | 全角英数 |     L         |
                   | 直接入力 | <-------------+
                   +----------+


sentimental-skkでは、1)の方式を採用します。

'''

# モード
_SKK_MODE_HANKAKU      = 0
_SKK_MODE_ZENKAKU      = 1
_SKK_MODE_HIRAGANA     = 2
_SKK_MODE_KATAKANA     = 3
_SKK_SUBMODE_EISUU     = 4

# モードに対応するマーク(タイトルバーに表示されます)
_SKK_MODE_MARK_MAP = {
    _SKK_MODE_HANKAKU      : u'@',
    _SKK_MODE_ZENKAKU      : u'Ａ',
    _SKK_MODE_HIRAGANA     : u'あ',
    _SKK_MODE_KATAKANA     : u'ア',
    _SKK_SUBMODE_EISUU     : u'A',
    }


class IModeListenerImpl(IModeListener):

    _enabled = True
    _has_event = False

    def notifyenabled(self, n):
        if n == 8861:
            self._has_event = True
        elif n == 8860:
            self._enabled = True

    def notifydisabled(self, n):
        if n == 8861:
            self._has_event = False
        elif n == 8860:
            self._enabled = False

    def hasevent(self):
        return self._has_event

    def getenabled(self):
        return self._enabled

class InputMode(IModeListenerImpl):
    '''
    モードの管理をします。
    '''
    __value = -1


    def __init__(self, tty):
        self._tty = tty 
        self.__setmode(_SKK_MODE_HANKAKU)

    def __setmode(self, mode):
        if self.__value != mode:
            self.__value = mode
            if self.hasevent():
                if self.iseisuu():
                    self._tty.write("\x1b[8854~")
                else:
                    self._tty.write("\x1b[%d~" % (8850 + self.__value))
        title.setmode(_SKK_MODE_MARK_MAP[min(mode, 4)])

    def isdirect(self):
        value = self.__value
        return value == _SKK_MODE_HANKAKU or value == _SKK_MODE_ZENKAKU
    
    def reset(self):
        self.__setmode(_SKK_MODE_HANKAKU)
    
    def starteisuu(self):
        ''' 英数サブモードを開始 '''
        self.__setmode(self.__value | _SKK_SUBMODE_EISUU)

    def endeisuu(self):
        ''' 英数サブモードを終了 '''
        self.__setmode(self.__value & ~_SKK_SUBMODE_EISUU)

    def startzen(self):
        ''' 全角英数モードを開始 '''
        self.__setmode(_SKK_MODE_ZENKAKU)

    def starthira(self):
        ''' ひらがなモードを開始 '''
        self.__setmode(_SKK_MODE_HIRAGANA)

    def startkata(self):
        ''' カタカナモードを開始 '''
        self.__setmode(_SKK_MODE_KATAKANA)

    def ishira(self):
        ''' ひらがなモードかどうか '''
        return self.__value == _SKK_MODE_HIRAGANA

    def iskata(self):
        ''' カタカナモードかどうか '''
        return self.__value == _SKK_MODE_KATAKANA

    def iseisuu(self):
        return self.__value & _SKK_SUBMODE_EISUU != 0

    def iszen(self):
        return self.__value == _SKK_MODE_ZENKAKU

    def ishan(self):
        return self.__value == _SKK_MODE_HANKAKU


