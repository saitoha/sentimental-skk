#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ***** BEGIN LICENSE BLOCK *****
# Copyright (C) 2012-2013  Hayaki Saito <user@zuse.jp>
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
from canossa import IModeListenerImpl
import key

'''

 既存の実装をいろいろ動かしてみたところ、
 モード遷移はおおむね以下のようになっていると理解しました。

 /(シングルシフト)というのは、一回のみのトグルという意味で使っています。
 つまり、確定するなどして英数変換入力が終わると、
 元の状態(ひらがなモードまたはカタカナモード)に戻ります。

                   +----------+
                   | abbrev   |  /(シングルシフト)
                   |          | <-------------+
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


'''

# モード
_SKK_MODE_HANKAKU = 0
_SKK_MODE_ZENKAKU = 1
_SKK_MODE_HIRAGANA = 2
_SKK_MODE_KATAKANA = 3
_SKK_SUBMODE_ABBREV = 4

_SKK_MODE_MARK_MAP = {_SKK_MODE_HANKAKU: u'SKK',
                      _SKK_MODE_ZENKAKU: u'全英',
                      _SKK_MODE_HIRAGANA: u'かな',
                      _SKK_MODE_KATAKANA: u'カナ',
                      _SKK_SUBMODE_ABBREV: u'Aあ'}

import eisuudb


class InputMode(IModeListenerImpl):
    '''
    モードの管理をします。
    '''
    _value = -1

    def __init__(self, tty):
        self._tty = tty
        self.__setmode(_SKK_MODE_HANKAKU)

    def __setmode(self, mode):
        if self._value != mode:
            self._value = mode
            if self.hasevent():
                if self.isabbrev():
                    self._tty.write("\x1b[8854~")
                else:
                    self._tty.write("\x1b[%d~" % (8850 + self._value))
        title.setmode(_SKK_MODE_MARK_MAP[min(mode, 4)])

    def handle_char(self, context, c):

        if c == key.skk_j_mode:  # LF C-j
            self.endabbrev()
            if self.ishan():
                self.starthira()
                return True
            elif self.iszen():
                self.starthira()
                return True

        elif self.ishan():
            # 半角直接入力
            context.write(c)
            return True

        elif self.iszen():
            # 全角直接入力
            context.write(eisuudb.to_zenkaku_cp(c))
            return True

        return False

    def isdirect(self):
        value = self._value
        return value == _SKK_MODE_HANKAKU or value == _SKK_MODE_ZENKAKU

    def reset(self):
        self.__setmode(_SKK_MODE_HANKAKU)

    def startabbrev(self):
        ''' 英数サブモードを開始 '''
        if self.getenabled():
            self.__setmode(self._value | _SKK_SUBMODE_ABBREV)

    def endabbrev(self):
        ''' 英数サブモードを終了 '''
        self.__setmode(self._value & ~_SKK_SUBMODE_ABBREV)

    def startzen(self):
        ''' 全角英数モードを開始 '''
        if self.getenabled():
            self.__setmode(_SKK_MODE_ZENKAKU)

    def starthira(self):
        ''' ひらがなモードを開始 '''
        if self.getenabled():
            self.__setmode(_SKK_MODE_HIRAGANA)

    def startkata(self):
        ''' カタカナモードを開始 '''
        if self.getenabled():
            self.__setmode(_SKK_MODE_KATAKANA)

    def ishira(self):
        ''' ひらがなモードかどうか '''
        return self._value == _SKK_MODE_HIRAGANA

    def iskata(self):
        ''' カタカナモードかどうか '''
        return self._value == _SKK_MODE_KATAKANA

    def isabbrev(self):
        return self._value & _SKK_SUBMODE_ABBREV != 0

    def iszen(self):
        return self._value == _SKK_MODE_ZENKAKU

    def ishan(self):
        return self._value == _SKK_MODE_HANKAKU


def test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()
