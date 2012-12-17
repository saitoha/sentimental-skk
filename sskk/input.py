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
import mode, candidate, context, word

import codecs
import time

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

# マーク
_SKK_MARK_COOK = u'▽ '
_SKK_MARK_SELECT = u'▼ '
_SKK_MARK_OKURI = u'*'
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

class MouseDecodingTrait():

    _mouse_state = None
    _x = 0
    _y = 0
    __lastclick = 0
    _mousedown = False
    _mousedrag = False
    __mouse_mode = None

    def set_mousemode(self, mouse_mode):
        self.__mouse_mode = mouse_mode

    def _handle_amb_report(self, context, parameter, intermediate, final):
        ''' '''
        if len(intermediate) == 0:
            if final == 0x57: # W
                if parameter == [0x32]:
                    self._termprop.set_amb_as_double()                    
                elif parameter == [0x31] or parameter == []:
                    self.onambstatechanged(1)                    
                return True
        return False

    def _handle_focus(self, context, parameter, intermediate, final):
        ''' '''
        if len(intermediate) == 0:
            if len(parameter) == 0:
                if final == 0x49: # I
                    self.onfocusin()                    
                    return True
                elif final == 0x4f: # O
                    self.onfocusout()                    
                    return True
        return False

    def _handle_mouse(self, context, parameter, intermediate, final):
        ''' '''
        if self.__mouse_mode is None:
            return False
        try:
            mouse_info = self._decode_mouse(context, parameter, intermediate, final)
            if mouse_info:
                mode, mouseup, code, x, y = mouse_info 
                if mode == 1000:
                    self._mouse_state = [] 
                    return True
                elif self._candidate.isshown():
                    if mouseup:
                        code |= 0x3
                    self.__dispatch_mouse(context, code, x, y) 
                    return True
                if self.__mouse_mode.protocol == 1006:
                    if mode == 1006: 
                        return False
                    elif mode == 1015:
                        params = (code + 32, x, y)
                        context.puts("\x1b[%d;%d;%dM" % params)
                        return True
                    elif mode == 1000:
                        params = (min(0x7e, code) + 32, x + 32, y + 32)
                        context.puts("\x1b[M%c%c%c" % params)
                        return True
                    return True
                if self.__mouse_mode.protocol == 1015:
                    if mode == 1015: 
                        return False
                    elif mode == 1006:
                        params = (code + 32, x, y)
                        if mouseup:
                            context.puts("\x1b[%d;%d;%dm" % params)
                        else:
                            context.puts("\x1b[%d;%d;%dM" % params)
                        return True
                    elif mode == 1000:
                        params = (min(0x7e, code) + 32, x + 32, y + 32)
                        context.puts("\x1b[M%c%c%c" % params)
                        return True
                else:
                    return True
        except:
            # TODO: logging
            pass
        return False 

    def onfocusin(self):
        pass

    def onfocusout(self):
        self._restore()

    def onmouseclick(self, context, x, y):
        candidate = self._candidate
        if candidate.includes(x, y):
            if candidate.position_is_selected(y):
                self._kakutei(context)
            else:
                self._candidate.click(x, y)
        else:
            self._restore()

    def onmouseup(self, context, x, y):
        pass

    def onmousemove(self, context, x, y):
        candidate = self._candidate
        if candidate.isshown() and candidate.includes(x, y):
            candidate.click(x, y)

    def onmousedragmove(self, context, x, y):
        if self.__dragstart_pos:
            origin_x, origin_y = self.__dragstart_pos
            offset_x = x - origin_x
            offset_y = y - origin_y
            candidate = self._candidate
            candidate.set_offset(self._output, offset_x, offset_y)

    def onmousedragstart(self, context, x, y):
        if self._candidate.includes(x, y):
            self.__dragstart_pos = (x, y)

    def onmousedragend(self, context, x, y):
        if self.__dragstart_pos:
            self.__dragstart_pos = None
            self._candidate.erase(self._output)
            self._candidate.offset_left = 0 
            self._candidate.offset_top = 0 

    def onmousedoubleclick(self, context, x, y):
        self._kakutei(context)

    def onmousescrolldown(self, context, x, y):
        self._candidate.safe_movenext()

    def onmousescrollup(self, context, x, y):
        self._candidate.moveprev()

    def _put_mouse_glitch_char(self, context, c):
        # xterm のX10/normal mouse encodingが互換じゃないので
        # TFFだけではちゃんと補足できない。
        # なので、CSI M
        self._mouse_state.append(c - 0x20)
        if len(self._mouse_state) == 3:
            code, x, y = self._mouse_state
            self._mouse_state = None
            if self._candidate.isshown():
                self.__dispatch_mouse(context, code, x - 1, y - 1) 
            if self.__mouse_mode.protocol != 0:
                params = (code + 0x20, x + 0x20, y + 0x20)
                context.puts("\x1b[M%c%c%c" % params)

    def _decode_mouse(self, context, parameter, intermediate, final):
        if len(parameter) == 0:
            if final == 0x4d: # M
                return 1000, None, None, None, None
            return None
        elif parameter[0] == 0x3c:
            if final == 0x4d: # M
                p = ''.join([chr(c) for c in parameter[1:]])
                try:
                    params = [int(c) for c in p.split(";")]
                    if len(params) != 3:
                        return  False
                    code, x, y = params
                    x -= 1
                    y -= 1
                except ValueError:
                    return False
                return 1006, False, code, x, y 
            elif final == 0x6d: # m
                p = ''.join([chr(c) for c in parameter[1:]])
                try:
                    params = [int(c) for c in p.split(";")]
                    if len(params) != 3:
                        return  False
                    code, x, y = params
                    x -= 1
                    y -= 1
                except ValueError:
                    return None
                return 1006, True, code, x, y 
        elif 0x30 <= parameter[0] and parameter[0] <= 0x39:
            if final == 0x4d: # M
                p = ''.join([chr(c) for c in parameter])
                try:
                    params = [int(c) for c in p.split(";")]
                    if len(params) != 3:
                        return  False
                    code, x, y = params
                    code -= 32
                    x -= 1
                    y -= 1
                except ValueError:
                    return False
                return 1015, False, code, x, y 
        return None

    def __dispatch_mouse(self, context, code, x, y):

        if code & 32: # mouse move
            if self._mousedrag:
                self.onmousedragmove(context, x, y)
            elif self._mousedown:
                self._mousedrag = True
                self.onmousedragstart(context, x, y)
            else:
                self.onmousemove(context, x, y)

        elif code & 0x3 == 0x3: # mouse up
            self._mousedown = False
            if self._mousedrag:
                self._mousedrag = False
                self.onmousedragend(context, x, y)
            elif x == self._x and y == self._y:
                now = time.time()
                if now - self.__lastclick < 0.1:
                    self.onmousedoubleclick(context, x, y)
                else:
                    self.onmouseclick(context, x, y)
                self.__lastclick = now
            else:
                self.onmouseup(context, x, y)

        elif code & 64: # mouse scroll
            if code & 0x1:
                self.onmousescrollup(context, x, y)
            else:
                self.onmousescrolldown(context, x, y)
        else: # mouse down
            self._x = x
            self._y = y
            self._mousedown = True
            self._mousedrag = False

################################################################################
#
# InputHandler
#
class InputHandler(tff.DefaultHandler, TitleTrait, MouseDecodingTrait):

    _stack = None
    _prev_length = 0

    def __init__(self, screen, stdout, termenc, termprop, use_title, mouse_mode):
        self._screen = screen
        self._output = codecs.getwriter(termenc)(StringIO(), errors='ignore')
        self.__stdout = stdout
        self.__termenc = termenc
        self._charbuf = context.CharacterContext()
        self.__mode = mode.ModeManager()
        self._wordbuf = word.WordBuffer(termprop)
        self._candidate = candidate.CandidateManager(screen, termprop, mouse_mode)
        self._termprop = termprop
        self.set_titlemode(use_title)
        self.set_mousemode(mouse_mode)
        self._stack = []

    def __reset(self):
        if not self._candidate.isempty():
            self._candidate.clear(self._output)
        self.__mode.endeisuu()
        self._wordbuf.reset() 
        self._charbuf.reset()

    def __draincharacters(self):
        s = self._charbuf.getbuffer()
        if s == 'n':
            self._charbuf.put(0x6e) # n
        s = self._charbuf.drain()
        return s

    def __iscooking(self):
        if not self._candidate.isempty():
            return True
        if not self._wordbuf.isempty():
            return True
        if not self._charbuf.isempty():
            return True
        return False

    def __convert_kana(self, value):
        if self.__mode.ishira():
            return kanadb.to_kata(value)
        else:
            assert self.__mode.iskata()
            return kanadb.to_hira(value)

    def __toggle_kana(self):
        self._charbuf.toggle()
        self.__mode.toggle()
        self.__reset()

    def __tango_henkan(self):
        key = self._wordbuf.get()

        if self.__mode.iskata():
            key = kanadb.to_hira(key)

        result = dictionary.gettango(key)

        if result: 
            self.settitle(key)
            self._candidate.assign(key, result)
            return True

        # かな読みだけを候補とする
        self._candidate.assign(key)

        return True

    def __okuri_henkan(self):
        buf = self._charbuf.getbuffer()[0]
        okuri = self.__draincharacters()
        if buf == 'n':
            self._wordbuf.append(u"ん")
            return
        key = self._wordbuf.get()

        if self.__mode.iskata():
            key = kanadb.to_hira(key)

        result = dictionary.getokuri(key + buf)

        self.settitle(u'%s - %s' % (key, buf))

        if result:
            self._candidate.assign(key, result, okuri)
            self._wordbuf.reset() 
            return True

        # かな読みだけを候補とする
        if self.__mode.iskata():
            key = kanadb.to_kata(key)
        self._candidate.assign(key, None, okuri)

        return True

    def _kakutei(self, context):
        ''' 確定 '''
        s = self.__draincharacters()
        self._wordbuf.append(s)
        if self._candidate.isempty():
            word = self._wordbuf.get()
        else:
            word, remarks = self._candidate.getcurrent(kakutei=True)
        self.onkakutei()
        self._wordbuf.reset()
        self._charbuf.reset()
        self._candidate.clear(self._output)
        context.putu(word)

    def _restore(self):
        ''' 再変換 '''
        self._wordbuf.reset()
        self._wordbuf.startedit()
        self._wordbuf.append(self._candidate.getyomi())
        self._candidate.clear(self._output)

        
    def __next(self):
        ''' 次候補 '''
        if self._candidate.isempty():
            if self._wordbuf.has_okuri():
                self.__okuri_henkan()
            else:
                s = self.__draincharacters()
                self._wordbuf.append(s)
                if not self.__tango_henkan():
                    self._kakutei(context)
        else:
            self._candidate.movenext()

        result, remarks = self._candidate.getcurrent()
        if self._use_title:
            if remarks:
                self.settitle(u'%s - %s' % (result, remarks))
            else:
                self.settitle(result)

    def __prev(self):
        ''' 前候補 '''
        if not self._candidate.isempty():
            self._candidate.moveprev()

        result, remarks = self._candidate.getcurrent()
        if self._use_title:
            if remarks:
                self.settitle(u'%s - %s' % (result, remarks))
            else:
                self.settitle(result)

    # override
    def handle_char(self, context, c):
        
        if not self._mouse_state is None and c >= 0x20 and c <= 0x7f:
            self._put_mouse_glitch_char(context, c)
            return True 

        elif c == 0x0a: # LF C-j
            if self.__mode.isdirect():
                self.__mode.toggle()
            else:
                if self.__iscooking():
                    self._kakutei(context)

        elif c == 0x0d: # CR C-m
            if self.__iscooking():
                self._kakutei(context)
            else:
                context.write(c)

        elif c == 0x07: # BEL C-g
            if self._candidate.isempty():
                self.__reset()
            else:
                self._restore()

        elif c == 0x08 or c == 0x7f: # BS or DEL
            if self._charbuf.isempty():
                if self._candidate.isshown():
                    self._kakutei(context)
                    context.write(c)
                elif self._wordbuf.isempty():
                    context.write(c)
                else:
                    self.__mode.endeisuu()
                    self._wordbuf.back()
            else:
                self._charbuf.back()

        elif c == 0x09: # TAB
            if not self._charbuf.isempty():
                # キャラクタバッファ編集中
                pass # 何もしない 
            elif not self._wordbuf.isempty():
                # ワードバッファ編集中
                pass # 何もしない TODO: 補完
            elif not self._candidate.isempty():
                # 候補選択中
                self.__next()
            else:
                context.write(c)

        elif c == 0x0e: # C-n
            if self._candidate.isshown():
                self.__next()
            elif not self._wordbuf.isempty():
                pass
            elif not self._charbuf.isempty():
                pass
            else:
                context.write(c)

        elif c == 0x10: # C-p
            if self._candidate.isshown():
                self.__prev()
            elif not self._wordbuf.isempty():
                pass
                #self.__prev()
            elif not self._charbuf.isempty():
                pass
                #self.__prev()
            else:
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
                self.__mode.reset()
                self.__reset()
            context.write(c)

        elif c == 0x20: # SP 
            if self.__mode.ishan():
                context.write(c)
            elif self.__mode.iszen():
                context.write(eisuudb.to_zenkaku_cp(c))
            elif not self._candidate.isempty():
                if self._charbuf.isempty():
                    self._charbuf.reset()
                self.__next()
            elif not self._wordbuf.isempty():
                s = self.__draincharacters()
                self._wordbuf.append(s)
                if self._wordbuf.length() > 0:
                    self.__next()
            elif not self._charbuf.isempty():
                self.__reset()
            else:
                context.write(c)

        elif c < 0x20 or 0x7f < c:
            if self.__mode.isdirect():
                context.write(c)
            else:
                self.__reset()
                context.write(c)

        elif c == 0x78 and self._candidate.isshown(): # x
            self.__prev()
        elif self.__mode.ishan():
            # 半角直接入力
            context.write(c)
        elif self.__mode.iszen():
            # 全角直接入力
            context.write(eisuudb.to_zenkaku_cp(c))
        elif self.__mode.iseisuu():
            # 英数変換モード
            self._wordbuf.append(unichr(c))
        elif self.__mode.ishira() or self.__mode.iskata():
            # ひらがな変換モード・カタカナ変換モード
            if c == 0x2f and (self._charbuf.isempty() or self._charbuf.getbuffer() != u'z'): # /
                if self.__iscooking():
                    self._wordbuf.append(unichr(c))
                else:
                    self.__mode.starteisuu()
                    self._wordbuf.reset()
                    self._wordbuf.startedit()
            elif c == 0x71: # q
                if self._candidate.isshown():
                    self._kakutei(context)
                    self.__toggle_kana()
                elif self.__iscooking():
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
                self.__mode.startzen()
                self.__reset()
            elif c == 0x6c: # l
                if self.__iscooking():
                    self._kakutei(context)
                self.__mode.reset()
                self.__reset()
            elif 0x41 <= c and c <= 0x5a: # A - Z
                # 大文字のとき
                self._charbuf.put(c + 0x20) # 子音に変換し、文字バッファに溜める
                # 変換中か
                if not self._candidate.isempty():
                    # 現在の候補を確定
                    result, remarks = self._candidate.getcurrent(kakutei=True)
                    context.putu(result)
                    # 変換候補をリセット
                    self._candidate.clear(self._output)

                    self._wordbuf.reset()
                    self._wordbuf.startedit()

                    if self._charbuf.isfinal():
                        # cが母音のとき、文字バッファを吸い出し、
                        s = self._charbuf.drain()
                        # 単語バッファに追加
                        self._wordbuf.append(s)

                # 先行する入力があるか
                elif self._wordbuf.isempty() or len(self._wordbuf.get()) == 0:
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
                # 変換中か
                if not self._candidate.isempty():
                    # 変換中であれば、確定
                    result, remarks = self._candidate.getcurrent(kakutei=True)
                    self._wordbuf.reset() 
                    self._candidate.clear(self._output)
                    context.putu(result)
                    if self._charbuf.isfinal():
                        s = self._charbuf.drain()
                        context.putu(s)
                elif self._charbuf.isfinal():
                    if self._wordbuf.isempty():
                        s = self._charbuf.drain()
                        context.putu(s)
                    else:
                        # 送り仮名変換
                        if self._wordbuf.has_okuri():
                            self.__okuri_henkan()
                        else:
                            s = self._charbuf.drain()
                            self._wordbuf.append(s)
            else:
                self.__reset()
                context.write(c)

        return True # handled

    # override
    def handle_csi(self, context, parameter, intermediate, final):
        if self._handle_mouse(context, parameter, intermediate, final):
            return True
        if self._handle_focus(context, parameter, intermediate, final):
            return True
        if self._handle_amb_report(context, parameter, intermediate, final):
            return True
        if not self._candidate.isempty():
            return True
        if not self._wordbuf.isempty():
            return True
        if not self._charbuf.isempty():
            return True
        return False

    # override
    def handle_draw(self, context):
        if not self._candidate.isempty():
            self._candidate.draw(self._output)
            result, remarks = self._candidate.getcurrent()
            result = _SKK_MARK_SELECT + result

            y, x = self._screen.getyx()
            self._output.write(u'\x1b[%d;%dH\x1b[1;4;31m%s\x1b[m\x1b[?25l' % (y + 1, x + 1, result))

            cur_width = self._termprop.wcswidth(result) 
            if self._candidate.isshown():
                if self._prev_length > cur_width:
                    length = self._prev_length - cur_width
                    y, x = self._screen.getyx()
                    self._screen.copyrect(self._output, x + cur_width, y, length, 1)
                    self._output.write(u"\x1b[%d;%dH" % (y + 1, x + 1))
                    #self._output.write(u" " * (self._prev_length - cur_width))
            self._prev_length = cur_width

        elif not self._wordbuf.isempty() or not self._charbuf.isempty():
            if self._wordbuf.isempty():
                s1 = u''
            elif self._wordbuf.has_okuri():
                s1 = _SKK_MARK_COOK + self._wordbuf.get() + _SKK_MARK_OKURI
            else:
                s1 = _SKK_MARK_COOK + self._wordbuf.get()
            s2 = self._charbuf.getbuffer() 
            termprop = self._termprop
            cur_width = termprop.wcswidth(s1) + termprop.wcswidth(s2)
            if self._prev_length > cur_width:
                length = self._prev_length - cur_width
                y, x = self._screen.getyx()
                self._screen.copyrect(self._output, x + cur_width, y, length, 1)
                self._output.write(u"\x1b[%d;%dH" % (y + 1, x + 1))
            self._prev_length = cur_width 
            y, x = self._screen.getyx()
            #self._output.write(u"\x1b[1;4;31m%s" % u"".join(self._stack))
            self._output.write(u'\x1b[1;4;31m%s\x1b[33m%s\x1b[m\x1b[?25l\x1b[%d;%dH' % (s1, s2, y + 1, x + 1))
        else:
            length = self._prev_length
            if length > 0:
                y, x = self._screen.getyx()
                self._screen.copyrect(self._output, x, y, length, 1)
                self._output.write(u"\x1b[%d;%dH\x1b[?25h" % (y + 1, x + 1))
                self._prev_length = 0 
        buf = self._output.getvalue()
        if len(buf) > 0:
            context.puts(buf)
            self._output.truncate(0)

