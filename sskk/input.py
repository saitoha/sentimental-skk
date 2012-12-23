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
        if self._rensetsu:
            self._rensetsu[self._index][0] = text
            self._remarks = remarks
        else: 
            self._remarks = remarks
        if self._use_title:
            if self._remarks:
                self.settitle(u'%s - %s' % (text, remarks))
            else:
                self.settitle(text)

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
    _anti_optimization_flag = False 
    _selected_text = None 
    _okuri = ""
    _bracket_left = _SKK_MARK_OPEN
    _bracket_right = _SKK_MARK_CLOSE
    _rensetsu = None

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
        self._rensetsu = None

    def __draincharacters(self):
        s = self._charbuf.getbuffer()
        if s == u'n':
            self._charbuf.put(0x6e) # n
        s = self._charbuf.drain()
        return s

    def __iscooking(self):
        if self._rensetsu:
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

    def _get_google(self, key):
        import urllib, urllib2, json
        try:
            params = urllib.urlencode({ 'langpair' : 'ja-Hira|ja', 'text' : key.encode("UTF-8") })
            self._rensetsu = json.loads(urllib2.urlopen('http://www.google.com/transliterate?', params).read())
            self._index = 0

            (primary, others) = self._rensetsu[self._index]

            result = []
            for word in others:
                result.append(unicode(word))

            for setsu in self._rensetsu:
                setsu[0] = setsu[1][0]
        except:
            return []
        return result

    def __tango_henkan(self):
        key = self._wordbuf.get()

        if self._inputmode.iskata():
            key = kanadb.to_hira(key)

        result = dictionary.gettango(key)

        self._okuri = u""
        self._index = 0

        if result: 
            self._rensetsu = [[key, result]]
        else:
            result = self._get_google(key)
            if len(result) == 0:
                result = [[key, [key]]]

        self.settitle(key)
        self._popup.assign(result)
        return True

    def __okuri_henkan(self):
        buf = self._charbuf.getbuffer()
        assert len(buf) > 0
        buf = buf[0]
        okuri = self.__draincharacters()
        key = self._wordbuf.get()

        self._okuri = u""
        self._index = 0

        if self._inputmode.iskata():
            key = kanadb.to_hira(key)

        result = dictionary.getokuri(key + buf)
        if result: 
            self._rensetsu = [[key, result]]
        else:
            if self._inputmode.iskata():
                key = kanadb.to_kata(key)
            result = self._get_google(key)
            if len(result) == 0:
                result = [[key, [key]]]

        self._okuri += okuri 

        self._popup.assign(result)
        self._wordbuf.reset() 

        self.settitle(u'%s - %s' % (key, buf))

        return True

    def _kakutei(self, context):
        ''' 確定 '''
        if self._rensetsu:
            word = u""
            for i in xrange(0, len(self._rensetsu)):
                word += self._rensetsu[i][0]
            word += self._okuri
            self._rensetsu = None
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

        elif c == 0x02: # C-b 
            self._moveprevclause()

        elif c == 0x06: # C-f 
            self._movenextclause()

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
            #if c > 0x20 and c < 0x2f:
            #    self._kakutei(context)
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
            elif c == 0x2c or c == 0x2e or c == 0x3a or c == 0x3b or c == 0x5b or c == 0x5d: # , . ; : [ ]
                self._charbuf.reset()
                if self._popup.isempty():
                    if not self._wordbuf.isempty():
                        self.__tango_henkan()
                        self._charbuf.put(c)
                        s = self._charbuf.drain()
                        self._okuri += s 
                    elif self._charbuf.put(c):
                        s = self._charbuf.drain()
                        context.write(ord(s))
                    else:
                        s = unichr(c)
                        context.write(c)
                    #raise
                else:
                    self._kakutei(context)
                    if self._charbuf.put(c):
                        s = self._charbuf.drain()
                        context.write(ord(s))
                    else:
                        context.write(c)
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

            elif c == 0x2d or 0x61 <= c and c <= 0x7a: # a - z
                if self._charbuf.put(c):
                    self._anti_optimization_flag = True
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
                if self.__iscooking():
                    self._kakutei(context)
                if self._charbuf.put(c):
                    s = self._charbuf.drain()
                    context.write(ord(s))
                else:
                    context.write(c)

        return True # handled

    def _handle_amb_report(self, context, parameter, intermediate, final):
        if len(intermediate) == 0:
            if final == 0x57: # W
                if parameter == [0x32]:
                    self._termprop.set_amb_as_double()                    
                elif parameter == [0x31] or parameter == []:
                    self._termprop.set_amb_as_single()                    
                return True
        return False

    def _get_candidates(self):
        primary, others = self._rensetsu[self._index]
        result = []
        for word in others:
            result.append(unicode(word))
        return result

    def _movenextclause(self):
        if self._rensetsu:
            self._index += 1
            self._index = self._index % len(self._rensetsu)
            result = self._get_candidates()
            self._popup.hide(self._output)
            self._popup.assign(result)

    def _moveprevclause(self):
        if self._rensetsu:
            self._index -= 1
            self._index = self._index % len(self._rensetsu)
            result = self._get_candidates()
            self._popup.hide(self._output)
            self._popup.assign(result)

    def _handle_csi_cursor(self, context, parameter, intermediate, final):
        if len(intermediate) == 0:
            if final == 0x43: # C
                self._movenextclause()
                return True
            elif final == 0x44: # D
                self._moveprevclause()
                return True
        return False

    def _handle_ss3_cursor(self, context, final):
        if final == 0x43: # C
            self._movenextclause()
            return True
        elif final == 0x44: # D
            self._moveprevclause()
            return True
        return False

    # override
    def handle_csi(self, context, parameter, intermediate, final):
        if self._popup.handle_csi(context, parameter, intermediate, final):
            return True
        if self._handle_csi_cursor(context, parameter, intermediate, final):
            return True
        if self._handle_amb_report(context, parameter, intermediate, final):
            return True
        if not self._wordbuf.isempty():
            return True
        if not self._charbuf.isempty():
            return True
        return False

    def handle_ss3(self, context, final):
        if self._popup.handle_ss3(context, final):
            return True
        if self._handle_ss3_cursor(context, final):
            return True
        return False

    # override
    def handle_draw(self, context):
        screen = self._screen
        termprop = self._termprop
        if self._rensetsu and not self._popup.isempty():
            self._termprop
            result = self._selectmark + self._rensetsu[self._index][0]
            y, x = screen.getyx()
            cur_width = 0
            self._output.write(u'\x1b[%d;%dH' % (y + 1, x + 1))
            #cur_width += termprop.wcswidth(self._bracket_left)
            #self._output.write(u'\x1b[m' + self._bracket_left)
            if self._rensetsu:
                for i in xrange(0, len(self._rensetsu)):
                    word = self._rensetsu[i][0]
                    if i == self._index:
                        if not self._popup.isshown():
                            self._popup.set_offset(cur_width, 0)
                        self._output.write(u'\x1b[0;1;4;31m')
                    else:
                        self._output.write(u'\x1b[0;32m')
                    cur_width += termprop.wcswidth(word)
                    self._output.write(word)
            else:
                cur_width += termprop.wcswidth(result)
                self._output.write(u'\x1b[1;4;31m' + result)
            if self._okuri:
                cur_width += termprop.wcswidth(self._okuri)
                self._output.write(u'\x1b[m' + self._okuri)
            #cur_width += termprop.wcswidth(self._bracket_right)
            #self._output.write(u'\x1b[m' + self._bracket_right)
            self._popup.draw(self._output)
            self._output.write(u"\x1b[%d;%dH" % (y + 1, x + 1))

            #cur_width = termprop.wcswidth(result)
            if self._prev_length > cur_width:
                length = self._prev_length - cur_width
                try:
                    screen.copyline(self._output, x + cur_width, y, length)
                finally:
                    pass
                self._output.write(u"\x1b[%d;%dH" % (y + 1, x + 1))
            self._prev_length = cur_width

        elif not self._wordbuf.isempty() or not self._charbuf.isempty():
            word = self._wordbuf.getbuffer()
            char = self._charbuf.getbuffer() 
            if self._anti_optimization_flag:
                self._anti_optimization_flag = False
                if len(word) == 0:
                    char = u''
            y, x = screen.getyx()
            cur_width = 0
            self._output.write(u"\x1b[%d;%dH" % (y + 1, x + 1))
            #cur_width += termprop.wcswidth(self._bracket_left) 
            #self._output.write(u'\x1b[m%s' % self._bracket_left)
            cur_width += termprop.wcswidth(word) 
            self._output.write(u'\x1b[0;1;4;31m' + word)
            cur_width += termprop.wcswidth(char) 
            self._output.write(u'\x1b[33m' + char)
            #cur_width += termprop.wcswidth(self._bracket_right) 
            #self._output.write(u'\x1b[m%s' % self._bracket_right)
            self._output.write(u'\x1b[m\x1b[%d;%dH' % (y + 1, x + 1))
            if self._prev_length > cur_width:
                length = self._prev_length - cur_width
                try:
                    screen.copyline(self._output, x + cur_width, y, length)
                finally:
                    pass
                self._output.write(u"\x1b[%d;%dH" % (y + 1, x + 1))
            self._prev_length = cur_width 

            if cur_width > 0:
                self._output.write(u'\x1b[?25l')
            else:
                self._output.write(u'\x1b[?25h')
        else:
            length = self._prev_length
            if length > 0:
                y, x = screen.getyx()
                try:
                    screen.copyline(self._output, x, y, length)
                finally:
                    pass
                self._output.write(u"\x1b[%d;%dH\x1b[?25h" % (y + 1, x + 1))
                self._prev_length = 0 
        buf = self._output.getvalue()
        if len(buf) > 0:
            context.puts(buf)
            self._output.truncate(0)

