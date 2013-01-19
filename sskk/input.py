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

import os
import tff

import title
import kanadb, eisuudb, dictionary
import word

from charbuf import CharacterContext
from canossa import Listbox, IListboxListener
from canossa import InnerFrame, IInnerFrameListener
from canossa import IScreenListener

import codecs, re
import logging, traceback

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

# マーク
_SKK_MARK_SELECT = u'▼'
_SKK_MARK_OPEN = u'【'
_SKK_MARK_CLOSE = u'】'

rcdir = os.path.join(os.getenv("HOME"), ".sskk")
histdir = os.path.join(rcdir, "history")
if not os.path.exists(histdir):
    os.makedirs(histdir)

class IScreenListenerImpl(IScreenListener):

    def ontitlechanged(self, s):
        title.setoriginal(s)
        self._refleshtitle()
        return None 

    def onmodeenabled(self, n):
        return False

    def onmodedisabled(self, n):
        return False


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

class IListboxListenerImpl(IListboxListener):

    def oninput(self, listbox, context, c):
        if c == 0x0d: # CR C-m
            self.onsettled(listbox, context)
        elif c == 0x0a: # LF C-j
            self.onsettled(listbox, context)
        elif c == 0x07: # BEL C-g
            self.oncancel(listbox, context)
        elif c == 0x08 or c == 0x7f: # C-h BS or DEL
            if self._clauses:
                self._clauses.shift_left()
                listbox.close()
                candidates = self._clauses.getcandidates()
                listbox.assign(candidates)
            else:
                self.onsettled(listbox, context)
                context.write(c)
        elif c == 0x09: # TAB C-i
            listbox.movenext()
        elif c == 0x0c: # LF C-l
            clauses = self._clauses
            if clauses:
                clauses.shift_right()
                self._listbox.close()
                candidates = clauses.getcandidates()
                listbox.assign(candidates)
        elif c == 0x0e: # C-n
            listbox.movenext()
        elif c == 0x16: # C-v
            listbox.jumpnext()
        elif c == 0x17: # C-w
            word = self._clauses.getvalue()
            self.open_wikipedia(word)
        elif c == 0x10: # C-p
            listbox.moveprev()
        elif c == 0x1b: # ESC C-[ 
            self.oncancel(listbox, context)
        elif c == 0x02: # C-b 
            return False
        elif c == 0x06: # C-f 
            return False
        elif c < 0x20: # other control chars 
            self.onsettled(listbox, context)
            context.write(c)
        elif c == 0x20: # SP 
            listbox.movenext()
        elif c == 0x78: # x
            listbox.moveprev()
        elif c <= 0x7e:
            self.onsettled(listbox, context)
            return False
        return True

    def onselected(self, listbox, index, text, remarks):
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

    def onsettled(self, listbox, context):
        if self._clauses:
            self._settle(context)
        elif self._wordbuf.length() > 0:
            self._listbox.close()
            self._showpopup()

    def oncancel(self, listbox, context):
        if self._clauses:
            listbox.close()
        text = self._clauses.getkey()
        self._clauses = None
        self._wordbuf.reset()
        self._wordbuf.startedit()
        self._wordbuf.append(text + self._okuri)
        self._complete()

    def onrepeat(self, listbox):
        return False

class IInnerFrameListenerImpl(IInnerFrameListener):

    def onclose(self, iframe, context):
        iframe.clear()
        self._iframe = None
        screen = self._screen

################################################################################
#
# InputHandler
#
class InputHandler(tff.DefaultHandler, 
                   IScreenListenerImpl,
                   IListboxListenerImpl,
                   IInnerFrameListenerImpl,
                   TitleTrait):

    _stack = None
    _prev_length = 0
    _anti_optimization_flag = False 
    _selected_text = None 
    _okuri = ""
    _bracket_left = _SKK_MARK_OPEN
    _bracket_right = _SKK_MARK_CLOSE
    _clauses = None
    _iframe = None

    def __init__(self, session, screen, termenc, termprop,
                 use_title, mousemode, inputmode,
                 canossa2=None):
        self._screen = screen
        self._output = codecs.getwriter(termenc)(StringIO(), errors='ignore')
        self._termenc = termenc
        self._charbuf = CharacterContext()
        self._inputmode = inputmode
        self._wordbuf = word.WordBuffer(termprop)
        self._listbox = Listbox(self, screen, termprop, mousemode, self._output)
        self._termprop = termprop
        self._mousemode = mousemode
        self.set_titlemode(use_title)
        self._stack = []
        self._canossa2 = canossa2
        self._session = session
        self._screen.setlistener(self)
        # detects libvte + Ambiguous=narrow environment
        if not termprop.is_cjk and termprop.is_vte():
            pad = u" "
            self._selectmark = _SKK_MARK_SELECT + pad
            self._bracket_left = _SKK_MARK_OPEN + pad 
            self._bracket_right = _SKK_MARK_CLOSE + pad 
        else:
            self._selectmark = _SKK_MARK_SELECT
            self._bracket_left = _SKK_MARK_OPEN
            self._bracket_right = _SKK_MARK_CLOSE

    def _reset(self):
        self._listbox.close()
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

    def _convert_tango(self):
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
        self._listbox.assign(candidates)
        self._clauses = clauses

        self.settitle(key)
        return True

    def _convert_okuri(self):

        clauses = self._clauses

        buf = self._charbuf.getbuffer()
        if not buf:
            return False
        assert buf
        okuri = self._draincharacters()
        buf = buf[0]
        key = self._wordbuf.get()

        if self._inputmode.iskata():
            key = kanadb.to_hira(key)
        result = dictionary.getokuri(key + buf)
        if result: 
            clauses = dictionary.Clauses()
            clauses.add(dictionary.Clause(key, result))
        else:
            if self._inputmode.iskata():
                key = kanadb.to_kata(key)
            clauses = dictionary.get_from_google_cgi_api(key)
            if not clauses:
                clauses = dictionary.Clauses()
                clauses.add(dictionary.Clause(key, [key]))
        self._clauses = clauses

        self._okuri = okuri 

        self._listbox.assign(clauses.getcandidates())
        self._wordbuf.startedit() 

        self.settitle(u'%s - %s' % (key, buf))
        return True

    def _settle(self, context):
        ''' 確定 '''
        clauses = self._clauses
        if clauses:
            key = clauses.getkey()
            word = clauses.getvalue() + self._okuri
            self._clauses = None
            self._okuri = u""
        else:
            s = self._draincharacters()
            word = self._wordbuf.get()
            word += s
        #dictionary.feedback(key, value)
        title.setmessage(u'＼(^o^)／')
        self._refleshtitle()
        self._listbox.close()
        self._inputmode.endabbrev()
        self._wordbuf.reset() 
        self._anti_optimization_flag = False
        context.putu(word)

    def _showpopup(self):
        ''' 次候補 '''
        wordbuf = self._wordbuf
        if wordbuf.has_okuri():
            self._convert_okuri()
        else:
            s = self._draincharacters()
            wordbuf.append(s)
            self._convert_tango()

    def _complete(self):
        completions = self._wordbuf.getcompletions(self._charbuf.complete())
        if completions:
            self._listbox.assign(completions, -1)
        else:
            self._listbox.close()

    def open_wikipedia(self, word):
        import urllib
        url = "http://ja.wikipedia.org/wiki/"
        url += urllib.quote_plus(word.encode('utf-8'))

        screen = self._screen

        height = min(20, int(screen.height * 0.7))
        width = min(60, int(screen.width * 0.7))
        top = int((screen.height - height) / 2)
        left = int((screen.width - width) / 2)
        self._iframe = InnerFrame(self._session, 
                                  self,
                                  screen,
                                  top, left, height, width,
                                  "w3m '%s'" % url,
                                  self._termenc,
                                  self._termprop,
                                  self._mousemode,
                                  self._output)

    def destruct_subprocess(self):
        session = self._session
        session.destruct_subprocess()

    # override
    def handle_char(self, context, c):

        if not self._inputmode.getenabled():
            return False

        if self._clauses and self._listbox.handle_char(context, c):
            return True

        if self._inputmode.handle_char(context, c):
            return True

        if self._charbuf.handle_char(context, c):
            return True

        if c == 0x0a: # LF C-j
            if self._iscooking():
                self._settle(context)

        elif c == 0x0d: # CR C-m
            if self._iscooking():
                self._settle(context)
            else:
                context.write(c)

        elif c == 0x07: # BEL C-g
            if self._iscooking():
                self._reset()
            else:
                context.write(c)

        elif c == 0x08 or c == 0x7f: # BS or DEL
            if not self._charbuf.isempty():
                self._charbuf.back()
                if not self._charbuf.getbuffer():
                    self._listbox.close()
                else:
                    self._complete()
            elif not self._wordbuf.isempty():
                self._wordbuf.back()
                if not self._wordbuf.getbuffer():
                    self._listbox.close()
                else:
                    self._complete()
            else:
                context.write(c)

        elif c == 0x09: # TAB C-i
            if not self._wordbuf.isempty():
                # ワードバッファ編集中
                s = self._draincharacters()
                self._wordbuf.append(s)
                self._wordbuf.complete()
                self._charbuf.reset()
                self._listbox.movenext()
            else:
                context.write(c)

        elif c == 0x0e: # C-n
            if self._listbox.isshown():
                self._listbox.movenext()
            elif not self._wordbuf.isempty():
                self._showpopup()
            elif not self._charbuf.isempty():
                self._showpopup()
            else:
                context.write(c)

        elif c == 0x10: # C-p
            if self._listbox.isshown():
                self._listbox.moveprev()
            elif self._wordbuf.isempty():
                if self._charbuf.isempty():
                    context.write(c)

        elif c == 0x11: # C-q
            if self._listbox.isshown():
                self._listbox.close()
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

        elif c == 0x17: # C-w
            if not self._wordbuf.isempty():
                word = self._wordbuf.get()
                self.open_wikipedia(word)
            else:
                self._reset()
                context.write(c)

        elif c == 0x1b: # ESC 
            if self._iscooking():
                self._reset()
                self._inputmode.reset()
                context.write(c)
            else:
                context.write(c)

        elif c == 0x20: # SP 
            if not self._wordbuf.isempty():
                s = self._draincharacters()
                self._wordbuf.append(s)
                if self._wordbuf.length() > 0:
                    self._showpopup()
            elif not self._charbuf.isempty():
                s = self._draincharacters()
                self._wordbuf.startedit()
                self._wordbuf.append(s)
                if self._wordbuf.length() > 0:
                    self._settle(context)
            else:
                context.write(c)

        elif c == 0x02: # C-b 
            if not self._moveprevclause():
                context.write(c)
            
        elif c == 0x06: # C-f 
            if not self._movenextclause():
                context.write(c)

        elif c < 0x20:
            self._reset()
            context.write(c)

        elif c > 0x7f:
            self._wordbuf.append(unichr(c))

        elif self._inputmode.isabbrev():
            # abbrev mode 
            self._wordbuf.append(unichr(c))
            self._complete()
        elif self._inputmode.ishira() or self._inputmode.iskata():
            # ひらがな変換モード・カタカナ変換モード
            charbuf = self._charbuf
            wordbuf = self._wordbuf
            inputmode = self._inputmode
            listbox = self._listbox

            if c == 0x2f and (charbuf.isempty() or charbuf.getbuffer() != u'z'): # /
                if not self._iscooking():
                    inputmode.startabbrev()
                    wordbuf.reset()
                    wordbuf.startedit()
            elif c == 0x71: # q
                if self._iscooking():
                    s = self._draincharacters()
                    wordbuf.append(s)
                    word = wordbuf.get()
                    self._reset()
                    if inputmode.ishira():
                        s = kanadb.to_kata(word)
                    else:
                        s = kanadb.to_hira(word)
                    context.putu(s)
                else:
                    charbuf.toggle()
                    if inputmode.ishira():
                        inputmode.startkata()
                    elif inputmode.iskata():
                        inputmode.starthira()
                    self._reset()
            elif c == 0x6c and charbuf.getbuffer() != "z": # l
                if listbox.isshown():
                    self._settle(context)
                inputmode.reset()
                self._reset()
            elif c == 0x2c or c == 0x2e or c == 0x3a or c == 0x3b or c == 0x5b or c == 0x5d: # , . ; : [ ]
                charbuf.reset()
                if listbox.isempty():
                    if not wordbuf.isempty():
                        self._convert_tango()
                        charbuf.put(c)
                        s = charbuf.drain()
                        self._okuri += s 
                    elif charbuf.put(c):
                        s = charbuf.drain()
                        context.write(ord(s))
                    else:
                        context.write(c)
                else:
                    self._settle(context)
                    if charbuf.put(c):
                        s = charbuf.drain()
                        context.write(ord(s))
                    else:
                        context.write(c)

            elif (0x61 <= c and c <= 0x7a) or charbuf.getbuffer() == "z": # _, a - z, z*
                if charbuf.put(c):
                    if wordbuf.isempty():
                        s = charbuf.drain()
                        context.putu(s)
                        self._complete()
                    elif wordbuf.has_okuri():
                        # 送り仮名変換
                        self._convert_okuri()
                    else:
                        s = charbuf.drain()
                        wordbuf.append(s)
                        self._complete()
                else:
                    self._complete()
 
            elif 0x41 <= c and c <= 0x5a: # A - Z
                # 大文字のとき
                # 先行する入力があるか
                if wordbuf.isempty() or not wordbuf.get():
                    wordbuf.startedit()
                    charbuf.put(c)
                    if charbuf.isfinal(): # 文字バッファに溜める
                        s = charbuf.drain()
                        wordbuf.append(s)
                        self._complete()
                    elif c == 0x4c: # L
                        if self._iscooking():
                            self._settle(context)
                        self._inputmode.startzen()
                        self._reset()
                    else:
                        self._complete()
                else:
                    s = charbuf.getbuffer()
                    if s == u'n':
                        charbuf.put(0x6e) # n
                        s = charbuf.drain()
                        wordbuf.append(s)
                        charbuf.reset()
                    if not charbuf.put(c) and not charbuf.isfinal() and c == 0x4c: # L
                        if self._iscooking():
                            self._settle(context)
                        self._inputmode.startzen()
                        self._reset()
                    else: 
                        if charbuf.hasnext():
                            s = charbuf.getbuffer()
                            wordbuf.append(s)
                            charbuf.reset()
                            charbuf.put(c)
                        # 先行する入力があるとき、送り仮名マーク('*')をつける
                        wordbuf.startokuri()
                        # キャラクタバッファが終了状態か 
                        if charbuf.isfinal():
                            # 送り仮名変換
                            self._convert_okuri()
            else:
                if self._iscooking():
                    self._settle(context)
                if self._charbuf.put(c):
                    s = self._charbuf.drain()
                    context.write(ord(s))
                else:
                    context.write(c)

        return True # handled

    def _handle_amb_report(self, context, parameter, intermediate, final):
        if not intermediate:
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
            self._listbox.close()
            self._listbox.assign(result)
            return True
        return False

    def _moveprevclause(self):
        if self._clauses:
            self._clauses.moveprev()
            result = self._clauses.getcandidates()
            self._listbox.close()
            self._listbox.assign(result)
            return True
        return False

    def _handle_csi_cursor(self, context, parameter, intermediate, final):
        if self._listbox.isshown():
            if final == 0x43: # C
                self._movenextclause()
                return True
            elif final == 0x44: # D
                self._moveprevclause()
                return True
        if final == 0x7e: # ~
            if parameter == [0x33] and not intermediate:
                if not self._charbuf.isempty():
                    self._charbuf.back()
                    if not self._charbuf.getbuffer():
                        self._listbox.close()
                    else:
                        self._complete()
                elif not self._wordbuf.isempty():
                    self._wordbuf.back()
                    if not self._wordbuf.getbuffer():
                        self._listbox.close()
                    else:
                        self._complete()
                else:
                    return False 
            return True
        return False

    def _handle_ss3_cursor(self, context, final):
        if self._listbox.isshown():
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
        if self._listbox.handle_csi(context, parameter, intermediate, final):
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
        if self._listbox.handle_esc(context, intermediate, final):
            return True
        return False

    def handle_ss3(self, context, final):
        if not self._inputmode.getenabled():
            return False
        if self._listbox.handle_ss3(context, final):
            return True
        if self._handle_ss3_cursor(context, final):
            return True
        if final == 0x5b: # [
            if self._iscooking():
                self._settle(context)
                self._inputmode.reset()
                self._reset()
            return False
        if not self._wordbuf.isempty():
            return True
        if not self._charbuf.isempty():
            return True
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
                if not self._listbox.isshown():
                    self._listbox.set_offset(cur_width, 0)
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

        self._listbox.draw(output)
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
        if char and not word and self._anti_optimization_flag:
            if y < screen.height - 1:
                screen.copyline(output, 0, y, screen.width)
            self._anti_optimization_flag = False
        elif len(char) == 1 and not word:
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

        if self._listbox:
            self._listbox.draw(output)

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

    def handle_resize(self, context, row, col):
        try:
            if self._iframe:
                self._iframe.close()
        except:
            logging.error("Resize failed")
        finally:
            self._iframe = None

    # override
    def handle_draw(self, context):
        if not self._inputmode.getenabled():
            return False
        output = self._output
        clauses = self._clauses
        iframe = self._iframe
        if clauses and not self._listbox.isempty():
            self._draw_clauses_with_popup(output)
            if iframe:
                iframe.draw(output)
        elif not self._wordbuf.isempty() or not self._charbuf.isempty():
            self._draw_word(output)
            if iframe:
                iframe.draw(output)
        else:
            self._draw_nothing(output)
        self._refleshtitle()
        buf = output.getvalue()
        if buf:
            context.puts(buf)
            output.truncate(0)

def test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()


