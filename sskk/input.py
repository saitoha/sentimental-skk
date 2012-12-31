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

import os
import tff

import title
import kanadb, eisuudb, dictionary
import context, word
from canossa import Listbox, IListboxListener

import codecs, re

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

# マーク
_SKK_MARK_SELECT = u'▼'
_SKK_MARK_OPEN = u'【'
_SKK_MARK_CLOSE = u'】'

rcdir = os.path.join(os.getenv("HOME"), ".sskk")
histdir = os.path.join(rcdir, "history")
if not os.path.exists(histdir):
    os.makedirs(histdir)

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
            title.draw(self._output)

    def settitle(self, value):
        face = self._getface()
        title.setmessage(face + " " + value)
        self._refleshtitle()

    def onkakutei(self):
        title.setmessage(u'＼(^o^)／')
        self._refleshtitle()

class IListboxListenerImpl(IListboxListener):

    def oninput(self, popup, context, c):
        if c == 0x0d: # CR C-m
            self.onsettled(popup, context)
        elif c == 0x0a: # LF C-j
            self.onsettled(popup, context)
        elif c == 0x07: # BEL C-g
            self.oncancel(popup, context)
        elif c == 0x08 or c == 0x7f: # C-h BS or DEL
            if self._clauses:
                self._clauses.shift_left()
                self._popup.close()
                candidates = self._clauses.getcandidates()
                popup.assign(candidates)
            else:
                self.onsettled(popup, context)
                context.write(c)
        elif c == 0x09: # TAB C-i
            popup.movenext()
        elif c == 0x0c: # LF C-l
            if self._clauses:
                self._clauses.shift_right()
                self._popup.close()
                candidates = self._clauses.getcandidates()
                popup.assign(candidates)
        elif c == 0x0e: # C-n
            popup.movenext()
        elif c == 0x16: # C-v
            popup.jumpnext()
        elif c == 0x10: # C-p
            popup.moveprev()
        elif c == 0x1b: # ESC C-[ 
            self.oncancel(popup, context)
        elif c == 0x02: # C-b 
            return False
        elif c == 0x06: # C-f 
            return False
        elif c < 0x20: # other control chars 
            self.onsettled(popup, context)
            context.write(c)
        elif c == 0x20: # SP 
            popup.movenext()
        elif c == 0x78: # x
            popup.moveprev()
        elif c <= 0x7e:
            self.onsettled(popup, context)
            return False
        return True

    def onselected(self, popup, index, text, remarks):
        if self._clauses:
            self._clauses.getcurrentclause().select(index)
            self._remarks = remarks
            if self._use_title:
                if self._remarks:
                    self.settitle(u'%s - %s' % (text, remarks))
                else:
                    self.settitle(text)
        elif index >= 0: 
            self._remarks = remarks
            self._wordbuf.reset()
            self._wordbuf.startedit()
            self._wordbuf.append(text)
            self._charbuf.reset()

    def onsettled(self, popup, context):
        if self._clauses:
            self._kakutei(context)
        elif self._wordbuf.length() > 0:
            self._showpopup()

    def oncancel(self, popup, context):
        if self._clauses:
            popup.close()
        text = self._clauses.getkey()
        self._clauses = None
        self._wordbuf.reset()
        self._wordbuf.startedit()
        self._wordbuf.append(text)
        self._complete()

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
    _clauses = None

    def __init__(self, session, screen, termenc, termprop,
                 use_title, mousemode, inputmode,
                 canossa2=None):
        self._screen = screen
        self._output = codecs.getwriter(termenc)(StringIO(), errors='ignore')
        self._charbuf = context.CharacterContext()
        self._inputmode = inputmode
        self._wordbuf = word.WordBuffer(termprop)
        self._popup = Listbox(self, screen, termprop, mousemode, self._output)
        self._termprop = termprop
        self.set_titlemode(use_title)
        self._stack = []
        self._canossa2 = canossa2
        self._session = session
        # detects libvte + Ambiguous=narrow environment
        if not termprop.is_cjk and termprop.da1 == "?62;9;" and re.match(">1;[23][0-9]{3};0", termprop.da2):
            self._selectmark = _SKK_MARK_SELECT + u" " # add pad
            self._bracket_left = _SKK_MARK_OPEN + u" "
            self._bracket_right = _SKK_MARK_CLOSE + u" "
        else:
            self._selectmark = _SKK_MARK_SELECT
            self._bracket_left = _SKK_MARK_OPEN
            self._bracket_right = _SKK_MARK_CLOSE

    def _reset(self):
        self._popup.close()
        self._inputmode.endabbrev()
        self._wordbuf.reset() 
        self._charbuf.reset()
        self._okuri = u""
        self._clauses = None
        self._anti_optimization_flag = False

    def _draincharacters(self):
        charbuf = self._charbuf
        s = charbuf.getbuffer()
        if s == u'n':
            charbuf.put(0x6e) # n
        s = charbuf.drain()
        return s

    def _iscooking(self):
        if self._clauses:
            return True
        if not self._wordbuf.isempty():
            return True
        if not self._charbuf.isempty():
            return True
        return False

    def _tango_henkan(self):
        key = self._wordbuf.get()

        if self._inputmode.iskata():
            key = kanadb.to_hira(key)

        result = dictionary.gettango(key)

        self._okuri = u""

        if result: 
            clauses = dictionary.Clauses()
            clauses.add(dictionary.Clause(key, result))
        else:
            clauses = dictionary.get_from_google_cgi_api(key)
            if not clauses:
                clauses = dictionary.Clauses()
                clauses.add(dictionary.Clause(key, [key]))

        candidates = clauses.getcandidates()
        self._popup.assign(candidates)
        self._clauses = clauses

        self.settitle(key)
        return True

    def _okuri_henkan(self):
        buf = self._charbuf.getbuffer()
        assert len(buf) > 0
        buf = buf[0]
        okuri = self._draincharacters()
        key = self._wordbuf.get()

        self._okuri = u""

        if self._inputmode.iskata():
            key = kanadb.to_hira(key)
        result = dictionary.getokuri(key + buf)
        if result: 
            self._clauses = dictionary.Clauses()
            self._clauses.add(dictionary.Clause(key, result))
        else:
            if self._inputmode.iskata():
                key = kanadb.to_kata(key)
            self._clauses = dictionary.get_from_google_cgi_api(key)
            if not self._clauses:
                self._clauses = dictionary.Clauses()
                self._clauses.add(dictionary.Clause(key, [key]))

        self._okuri += okuri 

        self._popup.assign(self._clauses.getcandidates())
        self._wordbuf.startedit() 

        self.settitle(u'%s - %s' % (key, buf))
        return True

    def _kakutei(self, context):
        ''' 確定 '''
        if self._clauses:
            key = self._clauses.getkey()
            word = self._clauses.getvalue() + self._okuri
            self._clauses = None
            self._okuri = u""
        else:
            s = self._draincharacters()
            self._wordbuf.append(s)
            word = self._wordbuf.get()
        #dictionary.feedback(key, value)
        self.onkakutei()
        self._reset()
        context.putu(word)

    def _showpopup(self):
        ''' 次候補 '''
        if self._wordbuf.has_okuri():
            self._okuri_henkan()
        else:
            s = self._draincharacters()
            self._wordbuf.append(s)
            self._tango_henkan()

    def _complete(self):
        completions = self._wordbuf.getcompletions()
        if completions:
            self._popup.assign(completions, -1)
        else:
            self._popup.close()

    # override
    def handle_char(self, context, c):
        
        if not self._inputmode.getenabled():
            return False

        if self._clauses and self._popup.handle_char(context, c):
            return True

        elif c == 0x0a: # LF C-j
            self._inputmode.endabbrev()
            if self._inputmode.ishan():
                self._inputmode.starthira()
            elif self._inputmode.iszen():
                self._inputmode.starthira()
            elif self._iscooking():
                self._kakutei(context)

        elif self._inputmode.ishan():
            # 半角直接入力
            context.write(c)

        elif self._inputmode.iszen():
            # 全角直接入力
            context.write(eisuudb.to_zenkaku_cp(c))

        elif c == 0x0d: # CR C-m
            if self._iscooking():
                self._kakutei(context)
            else:
                context.write(c)

        #elif c == 0x1a: # BEL C-z
        #    self._session.switch_input_target()

        elif c == 0x07: # BEL C-g
            if self._iscooking():
                self._reset()
            else:
                context.write(c)

        elif c == 0x08 or c == 0x7f: # BS or DEL
            if not self._charbuf.isempty():
                self._charbuf.back()
            elif not self._wordbuf.isempty():
                self._inputmode.endabbrev()
                self._wordbuf.back()
                if len(self._wordbuf.getbuffer()) == 0:
                    self._popup.close()
                else:
                    self._complete()
            else:
                context.write(c)

        elif c == 0x09: # TAB C-i
            if self._popup.isshown():
                self._popup.movenext()
            elif not self._charbuf.isempty():
                # キャラクタバッファ編集中
                pass # 何もしない 
            elif not self._wordbuf.isempty():
                # ワードバッファ編集中
                s = self._draincharacters()
                self._wordbuf.append(s)
                self._wordbuf.complete()
            else:
                context.write(c)

        elif c == 0x0e: # C-n
            if self._popup.isshown():
                self._popup.movenext()
            elif not self._wordbuf.isempty():
                self._showpopup()
            elif not self._charbuf.isempty():
                self._showpopup()
            else:
                context.write(c)

        elif c == 0x10: # C-p
            if self._popup.isshown():
                self._popup.moveprev()
            elif self._wordbuf.isempty():
                if self._charbuf.isempty():
                    context.write(c)

        elif c == 0x11: # C-q
            if self._inputmode.isabbrev():
                word = self._wordbuf.get()
                word = eisuudb.to_zenkaku(word)
                context.putu(word)
                self._inputmode.endabbrev()
                self._wordbuf.reset()
            elif not self._wordbuf.isempty():
                s = self._draincharacters()
                word = self._wordbuf.get()
                str_hankata = kanadb.to_hankata(word + s)
                context.putu(str_hankata)
                self._wordbuf.reset()
            else:
                context.write(c)

        elif c == 0x1b: # ESC 
            if self._iscooking():
                #self._kakutei(context)
                self._reset()
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
                s = self._draincharacters()
                self._wordbuf.append(s)
                if self._wordbuf.length() > 0:
                    self._showpopup()
            elif not self._charbuf.isempty():
                s = self._draincharacters()
                self._wordbuf.startedit()
                self._wordbuf.append(s)
                if self._wordbuf.length() > 0:
                    self._kakutei(context)
            else:
                context.write(c)

        elif c == 0x02: # C-b 
            if not self._moveprevclause():
                context.write(c)
            
        elif c == 0x06: # C-f 
            if not self._movenextclause():
                context.write(c)

        elif c < 0x20 or 0x7f < c:
            if self._inputmode.isdirect():
                context.write(c)
            else:
                self._reset()
                context.write(c)

        elif self._inputmode.isabbrev():
            # abbrev mode 
            self._wordbuf.append(unichr(c))
            self._complete()
        elif self._inputmode.ishira() or self._inputmode.iskata():
            # ひらがな変換モード・カタカナ変換モード
            #if c > 0x20 and c < 0x2f:
            #    self._kakutei(context)
            if c == 0x2f and (self._charbuf.isempty() or self._charbuf.getbuffer() != u'z'): # /
                if not self._iscooking():
                    self._inputmode.startabbrev()
                    self._wordbuf.reset()
                    self._wordbuf.startedit()
            elif c == 0x71: # q
                if self._iscooking():
                    s = self._draincharacters()
                    self._wordbuf.append(s)
                    word = self._wordbuf.get()
                    self._reset()
                    if self._inputmode.ishira():
                        s = kanadb.to_kata(word)
                    else:
                        s = kanadb.to_hira(word)
                    context.putu(s)
                else:
                    self._charbuf.toggle()
                    if self._inputmode.ishira():
                        self._inputmode.startkata()
                    elif self._inputmode.iskata():
                        self._inputmode.starthira()
                    self._reset()
            elif c == 0x4c: # L
                if self._iscooking():
                    self._kakutei(context)
                self._inputmode.startzen()
                self._reset()
            elif c == 0x6c: # l
                if self._popup.isshown():
                    self._kakutei(context)
                self._inputmode.reset()
                self._reset()
            elif c == 0x3c: # <
                self._clauses.shift_left()
            elif c == 0x3e: # >
                self._clauses.shift_right()
            elif c == 0x2c or c == 0x2e or c == 0x3a or c == 0x3b or c == 0x5b or c == 0x5d: # , . ; : [ ]
                self._charbuf.reset()
                if self._popup.isempty():
                    if not self._wordbuf.isempty():
                        self._tango_henkan()
                        self._charbuf.put(c)
                        s = self._charbuf.drain()
                        self._okuri += s 
                    elif self._charbuf.put(c):
                        s = self._charbuf.drain()
                        context.write(ord(s))
                    else:
                        s = unichr(c)
                        context.write(c)
                else:
                    self._kakutei(context)
                    if self._charbuf.put(c):
                        s = self._charbuf.drain()
                        context.write(ord(s))
                    else:
                        context.write(c)
            elif 0x41 <= c and c <= 0x5a: # A - Z
                # 大文字のとき
                # 先行する入力があるか
                if self._wordbuf.isempty() or len(self._wordbuf.get()) == 0:
                    self._charbuf.put(c + 0x20) # 小文字に変換し、文字バッファに溜める
                    self._wordbuf.startedit()
                    if self._charbuf.isfinal():
                        s = self._charbuf.drain()
                        self._wordbuf.append(s)
                        self._complete()
                else:
                    s = self._draincharacters()
                    self._wordbuf.append(s)
                    self._charbuf.put(c + 0x20) # 小文字に変換し、文字バッファに溜める
                    # 先行する入力があるとき、送り仮名マーク('*')をつける
                    self._wordbuf.startokuri()
                    # キャラクタバッファが終了状態か 
                    if self._charbuf.isfinal():
                        # 送り仮名変換
                        self._okuri_henkan()

            elif c == 0x2d or 0x61 <= c and c <= 0x7a: # a - z
                if self._charbuf.put(c):
                    if self._charbuf.isfinal():
                        if self._wordbuf.isempty():
                            s = self._charbuf.drain()
                            context.putu(s)
                        elif self._wordbuf.has_okuri():
                            # 送り仮名変換
                            self._okuri_henkan()
                        else:
                            s = self._charbuf.drain()
                            self._wordbuf.append(s)
                            self._complete()
                else:
                    self._charbuf.reset()
                    self._charbuf.put(c)
            else:
                if self._iscooking():
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

    def _movenextclause(self):
        if self._clauses:
            self._clauses.movenext()
            result = self._clauses.getcandidates()
            self._popup.close()
            self._popup.assign(result)
            return True
        return False

    def _moveprevclause(self):
        if self._clauses:
            self._clauses.moveprev()
            result = self._clauses.getcandidates()
            self._popup.close()
            self._popup.assign(result)
            return True
        return False

    def _handle_csi_cursor(self, context, parameter, intermediate, final):
        if self._popup.isshown():
            if len(intermediate) == 0:
                if final == 0x43: # C
                    self._movenextclause()
                    return True
                elif final == 0x44: # D
                    self._moveprevclause()
                    return True
        return False

    def _handle_ss3_cursor(self, context, final):
        if self._popup.isshown():
            if final == 0x43: # C
                self._movenextclause()
                return True
            elif final == 0x44: # D
                self._moveprevclause()
                return True
        return False

    # override
    def handle_csi(self, context, parameter, intermediate, final):
        if not self._inputmode.getenabled():
            return False
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

    def handle_esc(self, context, intermediate, final):
        if not self._inputmode.getenabled():
            return False
        if self._popup.handle_esc(context, intermediate, final):
            return True
        return False

    def handle_ss3(self, context, final):
        if not self._inputmode.getenabled():
            return False
        if self._popup.handle_ss3(context, final):
            return True
        if self._handle_ss3_cursor(context, final):
            return True
        if final == 0x5b: # [
            if self._iscooking():
                self._kakutei(context)
                self._inputmode.reset()
                self._reset()
            return False
        return False

    def _draw_clauses_with_popup(self, output):
        screen = self._screen
        termprop = self._termprop
        clauses = self._clauses
        result = clauses.getcurrentvalue()
        y, x = screen.getyx()
        cur_width = 0
        selected_clause = clauses.getcurrentclause()
        for clause in clauses:
            word = clause.getcurrentvalue()
            if id(clause) == id(selected_clause):
                cur_width += termprop.wcswidth(self._selectmark)
                if not self._popup.isshown():
                    self._popup.set_offset(cur_width, 0)
            cur_width += termprop.wcswidth(word)
        if self._okuri:
            cur_width += termprop.wcswidth(self._okuri)
        if self._prev_length > cur_width:
            length = self._prev_length - cur_width
            if x + cur_width + length < screen.width:
                screen.copyline(output, x + cur_width, y, length)
            else:
                screen.copyline(output, 0, y, screen.width)
                if y + 1 < screen.height:
                    screen.copyline(output, 0, y + 1, screen.width)

        output.write(u'\x1b[%d;%dH' % (y + 1, x + 1))
        for clause in clauses:
            word = clause.getcurrentvalue()
            if id(clause) == id(selected_clause):
                word = self._selectmark + word
                output.write(u'\x1b[0;1;4;31m')
            else:
                output.write(u'\x1b[0;32m')
            output.write(word)
        if self._okuri:
            output.write(u'\x1b[0;32m' + self._okuri)
        output.write(u"\x1b[%d;%dH" % (y + 1, x + 1))

        self._popup.draw(output)
        self._prev_length = cur_width

    def _draw_word(self, output):
        screen = self._screen
        termprop = self._termprop
        word = self._wordbuf.getbuffer()
        char = self._charbuf.getbuffer() 
        y, x = screen.getyx()
        cur_width = 0
        cur_width += termprop.wcswidth(word) 
        cur_width += termprop.wcswidth(char) 
        if len(char) > 0 and len(word) == 0 and self._anti_optimization_flag:
            if y < screen.height - 1:
                screen.copyline(output, 0, y, screen.width)
            self._anti_optimization_flag = False
        elif len(char) == 1 and len(word) == 0:
            self._anti_optimization_flag = True
        if self._prev_length > cur_width:
            length = self._prev_length - cur_width
            if x + cur_width + length < screen.width:
                screen.copyline(output, x + cur_width, y, length)
            else:
                screen.copyline(output, 0, y, screen.width)
                if y + 1 < screen.height:
                    screen.copyline(output, 0, y + 1, screen.width)
        output.write(u"\x1b[%d;%dH" % (y + 1, x + 1))
        output.write(u'\x1b[0;1;4;31m' + word)
        output.write(u'\x1b[0;1;32m' + char)
        output.write(u'\x1b[m\x1b[%d;%dH' % (y + 1, x + 1))

        if self._popup:
            self._popup.draw(output)

        self._prev_length = cur_width 
        if cur_width > 0:
            output.write(u'\x1b[?25l')
        else:
            output.write(u'\x1b[?25h')

    def _draw_nothing(self, output):
        screen = self._screen
        length = self._prev_length
        if length > 0:
            y, x = screen.getyx()
            if x + length < screen.width:
                screen.copyline(output, x, y, length)
            else:
                screen.copyline(output, 0, y, screen.width)
                if y + 1 < screen.height:
                    screen.copyline(output, 0, y + 1, screen.width)
            output.write(u"\x1b[%d;%dH\x1b[?25h" % (y + 1, x + 1))
            self._prev_length = 0 

    # override
    def handle_draw(self, context):
        if not self._inputmode.getenabled():
            return False
        output = self._output
        clauses = self._clauses
        if clauses and not self._popup.isempty():
            self._draw_clauses_with_popup(output)
        elif not self._wordbuf.isempty() or not self._charbuf.isempty():
            self._draw_word(output)
        else:
            self._draw_nothing(output)
        self._refleshtitle()
        buf = output.getvalue()
        if len(buf) > 0:
            context.puts(buf)
            output.truncate(0)

def test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()


