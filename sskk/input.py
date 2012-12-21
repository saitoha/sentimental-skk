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
import kanadb, eisuudb, dictionary
import context, word
from popup import Listbox, IListboxListener

import codecs, re

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

# マーク
_SKK_MARK_SELECT = u'▼'
_SKK_MARK_OPEN = u'【'
_SKK_MARK_CLOSE = u'】'

class TitleTrait():

    _counter = 0
    _use_title = False

    def set_titlemode(self, use_title):
        self._use_title = use_title
        self._counter = 0

    def _getface(self):
        self._counter = 1 - self._counter
        return [u'三 ┗( ^o^)┓ ＜', u'三 ┏( ^o^)┛ ＜'][self._counter]

    def _refleshtitle(self):
        if self._use_title:
            self._output.write(u'\x1b]2;%s\x1b\\' % title.get())

    def settitle(self, value):
        face = self._getface()
        title.setmessage(face + " " + value)
        self._refleshtitle()

    def onkakutei(self):
        title.setmessage(u'＼(^o^)／')
        self._refleshtitle()

class IListboxListenerImpl(IListboxListener):

    def onselected(self, index, text, remarks):
        self._selected_text = text + self._okuri
        self._remarks = remarks
        if self._use_title:
            if self._remarks:
                self.settitle(u'%s - %s' % (self._selected_text, self._remarks))
            else:
                self.settitle(self._selected_text)

    def onsettled(self, context):
        self._kakutei(context)

################################################################################
#
# InputHandler
#
class InputHandler(tff.DefaultHandler, 
                   IListboxListenerImpl,
                   TitleTrait):

    _stack = None
    _prev_length = 0
    _anti_opt_flag = False 
    _selected_text = None 
    _okuri = ""

    def __init__(self, screen, termenc, termprop, use_title, mousemode, inputmode):
        self._screen = screen
        self._output = codecs.getwriter(termenc)(StringIO(), errors='ignore')
        self._charbuf = context.CharacterContext()
        self._inputmode = inputmode
        self._wordbuf = word.WordBuffer(termprop)
        self._popup = Listbox(self, screen, termprop, mousemode, self._output)
        self._termprop = termprop
        self.set_titlemode(use_title)
        self._stack = []
        if not termprop.is_cjk and termprop.da1 == "?62;9;" and re.match(">1;[23][0-9]{3};0", termprop.da2):
            self._selectmark = _SKK_MARK_SELECT + u" "
        else:
            self._selectmark = _SKK_MARK_SELECT

    def __reset(self):
        self._popup.hide(self._output)
        self._inputmode.endeisuu()
        self._wordbuf.reset() 
        self._charbuf.reset()
        self._okuri = u""
        self._selected_text = None 

    def __draincharacters(self):
        s = self._charbuf.getbuffer()
        if s == u'n':
            self._charbuf.put(0x6e) # n
        s = self._charbuf.drain()
        return s

    def __iscooking(self):
        if self._selected_text:
            return True
        if not self._wordbuf.isempty():
            return True
        if not self._charbuf.isempty():
            return True
        return False

    def __convert_kana(self, value):
        if self._inputmode.ishira():
            return kanadb.to_kata(value)
        else:
            assert self._inputmode.iskata()
            return kanadb.to_hira(value)

    def __toggle_kana(self):
        self._charbuf.toggle()
        if self._inputmode.ishira():
            self._inputmode.startkata()
        elif self._inputmode.iskata():
            self._inputmode.starthira()
        self.__reset()

    def __tango_henkan(self):
        key = self._wordbuf.get()

        if self._inputmode.iskata():
            key = kanadb.to_hira(key)

        result = dictionary.gettango(key)

        self._okuri = ""

        if not result: 
            result = [key]

        self.settitle(key)
        self._popup.assign(result)
        return True

    def __okuri_henkan(self):
        buf = self._charbuf.getbuffer()[0]
        self._okuri = self.__draincharacters()
        key = self._wordbuf.get()

        if self._inputmode.iskata():
            key = kanadb.to_hira(key)

        result = dictionary.getokuri(key + buf)

        self.settitle(u'%s - %s' % (key, buf))

        if not result:
            if self._inputmode.iskata():
                key = kanadb.to_kata(key)
            result = [key]

        self._popup.assign(result)
        self._wordbuf.reset() 

        return True

    def _kakutei(self, context):
        ''' 確定 '''
        if self._selected_text:
            word = self._selected_text 
            self._selected_text = None 
        else:
            s = self.__draincharacters()
            self._wordbuf.append(s)
            word = self._wordbuf.get()
        self.onkakutei()
        self._inputmode.endeisuu()
        self._wordbuf.reset()
        self._charbuf.reset()
        self._popup.hide(self._output)
        context.putu(word)

    def __showpopup(self):
        ''' 次候補 '''
        if self._wordbuf.has_okuri():
            self.__okuri_henkan()
        else:
            s = self.__draincharacters()
            self._wordbuf.append(s)
            if not self.__tango_henkan():
                self._kakutei(context)

    # override
    def handle_char(self, context, c):
        
        if self._popup.handle_char(context, c):
            return True

        elif c == 0x0a: # LF C-j
            self._inputmode.endeisuu()
            if self._inputmode.ishan():
                self._inputmode.starthira()
            elif self._inputmode.iszen():
                self._inputmode.starthira()
            elif self.__iscooking():
                self._kakutei(context)

        elif c == 0x0d: # CR C-m
            if self.__iscooking():
                self._kakutei(context)
            else:
                context.write(c)

        elif c == 0x07: # BEL C-g
            self.__reset()

        elif c == 0x08 or c == 0x7f: # BS or DEL
            if self._charbuf.isempty():
                if self._wordbuf.isempty():
                    context.write(c)
                else:
                    self._inputmode.endeisuu()
                    self._wordbuf.back()
            else:
                self._charbuf.back()

        elif c == 0x09: # TAB C-i
            if not self._charbuf.isempty():
                # キャラクタバッファ編集中
                pass # 何もしない 
            elif not self._wordbuf.isempty():
                # ワードバッファ編集中
                s = self.__draincharacters()
                self._wordbuf.append(s)
                self._wordbuf.complete()
            else:
                context.write(c)

        elif c == 0x0e: # C-n
            if not self._wordbuf.isempty():
                self.__showpopup()
            elif not self._charbuf.isempty():
                self.__showpopup()
            else:
                context.write(c)

        elif c == 0x10: # C-p
            if self._wordbuf.isempty():
                if self._charbuf.isempty():
                    context.write(c)

        elif c == 0x11: # C-q
            if not self._wordbuf.isempty():
                s = self.__draincharacters()
                w = self._wordbuf.get()
                str_hankata = kanadb.to_hankata(w + s)
                context.putu(str_hankata)
                self._wordbuf.reset()
            else:
                context.write(c)

        elif c == 0x1b: # ESC 
            if self.__iscooking():
                self._kakutei(context)
                self.__reset()
                self._inputmode.reset()
                context.write(c)
            else:
                context.write(c)

        elif c == 0x20: # SP 
            if self._inputmode.ishan():
                context.write(c)
            elif self._inputmode.iszen():
                context.write(eisuudb.to_zenkaku_cp(c))
            elif not self._wordbuf.isempty():
                s = self.__draincharacters()
                self._wordbuf.append(s)
                if self._wordbuf.length() > 0:
                    self.__showpopup()
            elif not self._charbuf.isempty():
                s = self.__draincharacters()
                self._wordbuf.startedit()
                self._wordbuf.append(s)
                if self._wordbuf.length() > 0:
                    self._kakutei(context)
            else:
                context.write(c)

        elif c < 0x20 or 0x7f < c:
            if self._inputmode.isdirect():
                context.write(c)
            else:
                self.__reset()
                context.write(c)

        elif self._inputmode.ishan():
            # 半角直接入力
            context.write(c)
        elif self._inputmode.iszen():
            # 全角直接入力
            context.write(eisuudb.to_zenkaku_cp(c))
        elif self._inputmode.iseisuu():
            # 英数変換モード
            self._wordbuf.append(unichr(c))
        elif self._inputmode.ishira() or self._inputmode.iskata():
            # ひらがな変換モード・カタカナ変換モード
            if c == 0x2f and (self._charbuf.isempty() or self._charbuf.getbuffer() != u'z'): # /
                if self.__iscooking():
                    self._wordbuf.append(unichr(c))
                else:
                    self._inputmode.starteisuu()
                    self._wordbuf.reset()
                    self._wordbuf.startedit()
            elif c == 0x71: # q
                if self.__iscooking():
                    s = self.__draincharacters()
                    self._wordbuf.append(s)
                    word = self._wordbuf.get()
                    self.__reset()
                    s = self.__convert_kana(word)
                    context.putu(s)
                else:
                    self.__toggle_kana()
            elif c == 0x4c: # L
                if self.__iscooking():
                    self._kakutei(context)
                self._inputmode.startzen()
                self.__reset()
            elif c == 0x6c: # l
                if self.__iscooking():
                    self._kakutei(context)
                self._inputmode.reset()
                self.__reset()
            elif 0x41 <= c and c <= 0x5a: # A - Z
                # 大文字のとき
                self._charbuf.put(c + 0x20) # 小文字に変換し、文字バッファに溜める
                # 先行する入力があるか
                if self._wordbuf.isempty() or len(self._wordbuf.get()) == 0:
                    # 先行する入力が無いとき、
                    # 単語バッファを編集マーク('▽')とする
                    self._wordbuf.startedit()
                    # cが母音か
                    if self._charbuf.isfinal():
                        # cが母音のとき、文字バッファを吸い出し、
                        s = self._charbuf.drain()
                        # 単語バッファに追加
                        self._wordbuf.append(s)
                else:
                    # 先行する入力があるとき、送り仮名マーク('*')をつける
                    self._wordbuf.startokuri()
                    # キャラクタバッファが終了状態か 
                    if self._charbuf.isfinal():
                        # 送り仮名変換
                        self.__okuri_henkan()

            #elif 0x61 <= c and c <= 0x7a: # a - z
            elif self._charbuf.put(c):
                self._anti_opt_flag = True
                if self._charbuf.isfinal():
                    if self._wordbuf.isempty():
                        s = self._charbuf.drain()
                        context.putu(s)
                    elif self._wordbuf.has_okuri():
                        # 送り仮名変換
                        self.__okuri_henkan()
                    else:
                        s = self._charbuf.drain()
                        self._wordbuf.append(s)
            else:
                self.__reset()
                context.write(c)

        return True # handled

    def _handle_amb_report(self, context, parameter, intermediate, final):
        ''' '''
        if len(intermediate) == 0:
            if final == 0x57: # W
                if parameter == [0x32]:
                    self._termprop.set_amb_as_double()                    
                elif parameter == [0x31] or parameter == []:
                    self._termprop.set_amb_as_single()                    
                return True
        return False

    # override
    def handle_csi(self, context, parameter, intermediate, final):
        if self._popup.handle_csi(context, parameter, intermediate, final):
            return True
        if self._handle_amb_report(context, parameter, intermediate, final):
            return True
        if not self._wordbuf.isempty():
            return True
        if not self._charbuf.isempty():
            return True
        return False

    # override
    def handle_draw(self, context):
        screen = self._screen
        termprop = self._termprop
        if self._selected_text and not self._popup.isempty():
            self._popup.draw(self._output)
            self._termprop
            result = self._selectmark + self._selected_text

            y, x = screen.getyx()
            self._output.write(u'\x1b[%d;%dH\x1b[1;4;31m%s\x1b[m\x1b[?25l' % (y + 1, x + 1, result))

            cur_width = termprop.wcswidth(result) 
            if self._prev_length > cur_width:
                length = self._prev_length - cur_width
                y, x = screen.getyx()
                screen.copyrect(self._output, x + cur_width, y, length, 1)
                self._output.write(u"\x1b[%d;%dH" % (y + 1, x + 1))
            self._prev_length = cur_width

        elif not self._wordbuf.isempty() or not self._charbuf.isempty():
            word = self._wordbuf.getbuffer()
            char = self._charbuf.getbuffer() 
            if self._anti_opt_flag:
                self._anti_opt_flag = False
                if len(word) == 0:
                    char = u''
            cur_width = termprop.wcswidth(word + char)
            y, x = screen.getyx()
            if self._prev_length > cur_width:
                length = self._prev_length - cur_width
                screen.copyrect(self._output, x + cur_width, y, length, 1)
            self._prev_length = cur_width 
            self._output.write(u"\x1b[%d;%dH" % (y + 1, x + 1))
            self._output.write(u'\x1b[0;1;4;31m%s' % word)
            self._output.write(u'\x1b[33m%s' % char)
            self._output.write(u'\x1b[m\x1b[?25l\x1b[%d;%dH' % (y + 1, x + 1))
        else:
            length = self._prev_length
            if length > 0:
                y, x = screen.getyx()
                screen.copyrect(self._output, x, y, length, 1)
                self._output.write(u"\x1b[%d;%dH\x1b[?25h" % (y + 1, x + 1))
                self._prev_length = 0 
        buf = self._output.getvalue()
        if len(buf) > 0:
            context.puts(buf)
            self._output.truncate(0)

