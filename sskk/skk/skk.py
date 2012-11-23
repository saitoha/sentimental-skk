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
import wcwidth
import terminfo
import kanadb, eisuudb, dictionary
import mode, candidate, context, word

import codecs
import time

# マーク
_SKK_MARK_COOK = u'▽ '
_SKK_MARK_SELECT = u'▼ '
_SKK_MARK_OKURI = u'*'
_SKK_MARK_OPEN = u'【'
_SKK_MARK_CLOSE = u'】'

################################################################################
#
# InputHandler
#
class InputHandler(tff.DefaultHandler):

    __mouse_state = None
    _x = 0
    _y = 0
    _lastclick = 0
    _mousedown = False
    _mousedrag = False

    def __init__(self,
                 screen,
                 stdout,
                 termenc,
                 is_cjk,
                 mouse_mode):
        self.__screen = screen
        self.__stdout = codecs.getwriter(termenc)(stdout, errors='ignore')
        self.__termenc = termenc
        self.__context = context.CharacterContext()
        self.__mode = mode.ModeManager()
        self.__word = word.WordBuffer(is_cjk)
        self.__candidate = candidate.CandidateManager(screen, is_cjk, mouse_mode)
        self.__counter = 0
        self.__mouse_mode = mouse_mode
        if is_cjk:
            self._wcswidth = wcwidth.wcswidth_cjk
        else:
            self._wcswidth = wcwidth.wcswidth

    def __reset(self):
        self.__clear()
        self.__context.reset()
        if not self.__candidate.isempty():
            self.__candidate.clear(self.__stdout)
        self.__mode.endeisuu()
        self.__word.reset() 
        self.__refleshtitle()

    def __clear(self):
        candidate_length = self._wcswidth(_SKK_MARK_SELECT)
        candidate_length += self.__candidate.getwidth()
        cooking_length = self._wcswidth(_SKK_MARK_COOK)
        cooking_length += self.__word.length()
        cooking_length += self._wcswidth(_SKK_MARK_OKURI)
        cooking_length += self._wcswidth(self.__context.getbuffer())
        length = max(candidate_length, cooking_length) + 4
        x = self.__screen.cursor.col
        y = self.__screen.cursor.row
        self.__screen.drawrect(self.__stdout, x, y, length, 1)
        self.__write(u"\x1b[%d;%dH\x1b[?25h" % (y + 1, x + 1))

    def __write(self, s):
        self.__stdout.write(s)
        self.__stdout.flush()

    def __settitle(self, value):
        title.setmessage(value)
        self.__refleshtitle()

    def __refleshtitle(self):
        self.__write(u'\x1b]0;%s\x07' % title.get())

    def __getface(self):
        self.__counter = 1 - self.__counter
        return [u'三 ┗( ^o^)┓ ＜', u'三 ┏( ^o^)┛ ＜'][self.__counter]

    def __display(self):
        if not self.__candidate.isempty():
            result, remarks = self.__candidate.getcurrent()

            face = self.__getface()

            if remarks:
                self.__settitle(u'%s %s - %s' % (face, result, remarks))
            else:
                self.__settitle(u'%s %s' % (face, result))

            result = _SKK_MARK_SELECT + result
            x = self.__screen.cursor.col
            y = self.__screen.cursor.row
            self.__write(u'\x1b[1;4;31m%s\x1b[m\x1b[?25l\x1b[%d;%dH' % (result, y + 1, x + 1))

            self.__candidate.draw(self.__stdout)
        elif not self.__word.isempty() or not self.__context.isempty():
            if self.__word.isempty():
                s1 = u''
            elif self.__word.is_okuri():
                s1 = _SKK_MARK_COOK + self.__word.get() + _SKK_MARK_OKURI
            else:
                s1 = _SKK_MARK_COOK + self.__word.get()
            s2 = self.__context.getbuffer() 
            x = self.__screen.cursor.col
            y = self.__screen.cursor.row
            self.__write(u'\x1b[1;4;31m%s\x1b[33m%s\x1b[m\x1b[?25l\x1b[%d;%dH' % (s1, s2, y + 1, x + 1))
        else:
            pass

    def __draincharacters(self):
        s = self.__context.getbuffer()
        if s == 'n':
            self.__context.put(0x6e) # n
        s = self.__context.drain()
        return s

    def __iscooking(self):
        if not self.__candidate.isempty():
            return True
        if not self.__word.isempty():
            return True
        if not self.__context.isempty():
            return True
        return False

    def __convert_kana(self, value):
        if self.__mode.ishira():
            return kanadb.to_kata(value)
        else:
            assert self.__mode.iskata()
            return kanadb.to_hira(value)

    def __toggle_kana(self):
        self.__context.toggle()
        self.__mode.toggle()
        self.__reset()

    def __tango_henkan(self):
        key = self.__word.get()

        if self.__mode.iskata():
            key = kanadb.to_hira(key)

        result = dictionary.gettango(key)

        if result: 
            face = self.__getface()
            self.__settitle(u'%s %s' % (face, key))
            self.__candidate.assign(key, result)
            self.__clear()
            self.__display()
            return True

        # かな読みだけを候補とする
        self.__candidate.assign(key)

        return True

    def __okuri_henkan(self):
        buf = self.__context.getbuffer()[0]
        okuri = self.__draincharacters()
        key = self.__word.get()

        if self.__mode.iskata():
            key = kanadb.to_hira(key)

        result = dictionary.getokuri(key + buf)

        face = self.__getface()
        self.__settitle(u'%s %s - %s' % (face, key, buf))
        if result:
            self.__candidate.assign(key, result, okuri)
            self.__clear()
            self.__display()
            self.__word.reset() 
            return True

        # かな読みだけを候補とする
        if self.__mode.iskata():
            key = kanadb.to_kata(key)
        self.__candidate.assign(key, None, okuri)

        return True

    def __kakutei(self, context):
        ''' 確定 '''
        s = self.__draincharacters()
        self.__word.append(s)
        if self.__candidate.isempty():
            word = self.__word.get()
        else:
            word, remarks = self.__candidate.getcurrent(kakutei=True)
        self.__settitle(u'＼(^o^)／')
        self.__clear()
        self.__word.reset()
        self.__context.reset()
        self.__candidate.clear(self.__stdout)
        context.writestring(word)

    def __restore(self):
        ''' 再変換 '''
        self.__clear()
        self.__word.reset()
        self.__word.append(self.__candidate.getyomi())
        self.__candidate.clear(self.__stdout)
        self.__display()

    def __next(self):
        ''' 次候補 '''
        if self.__candidate.isempty():
            if self.__word.is_okuri():
                self.__okuri_henkan()
            else:
                s = self.__draincharacters()
                self.__word.append(s)
                if not self.__tango_henkan():
                    self.__kakutei(context)
        else:
            #self.__clear()
            self.__candidate.movenext()
            self.__display()

    def __prev(self):
        ''' 前候補 '''
        if not self.__candidate.isempty():
            #self.__clear()
            self.__candidate.moveprev()
            self.__display()

    def handle_char(self, context, c):
        
        if not self.__mouse_state is None:
            # xterm のX10/normal mouse encodingが互換じゃないので
            # TFFだけではちゃんと補足できない。
            # なので、CSI M
            self.__mouse_state.append(c - 32)
            if len(self.__mouse_state) == 3:
                code, x, y = self.__mouse_state
                self.__mouse_state = None
                if self.__candidate.isshown():
                    self.__dispatch_mouse(context, code, x - 1, y - 1) 
                if self.__mouse_mode.protocol != 0:
                    params = (code + 32, x + 32, y + 32)
                    context.writestring("\x1b[M%c%c%c" % params)
            return True 
        elif c == 0x0a: # LF C-j
            if self.__mode.isdirect():
                self.__mode.toggle()
                self.__refleshtitle()
            else:
                if self.__iscooking():
                    self.__kakutei(context)

        elif c == 0x0d: # CR C-m
            if self.__iscooking():
                self.__kakutei(context)
            else:
                context.write(c)

        elif c == 0x07: # BEL C-g
            if self.__candidate.isempty():
                self.__reset()
            else:
                self.__restore()

        elif c == 0x08 or c == 0x7f: # BS or DEL
            if self.__context.isempty():
                if not self.__candidate.isempty():
                    self.__restore()
                elif self.__word.isempty():
                    context.write(c)
                else:
                    self.__clear()
                    self.__mode.endeisuu()
                    self.__word.back()
                    self.__display()
            else:
                self.__clear()
                self.__context.back()
                self.__display()

        elif c == 0x09: # 
            if not self.__context.isempty():
                # キャラクタバッファ編集中
                pass # 何もしない 
            elif not self.__word.isempty():
                # ワードバッファ編集中
                pass # 何もしない TODO: 補完
            elif not self.__candidate.isempty():
                # 候補選択中
                self.__next()
            else:
                context.write(c)

        elif c == 0x0e: # C-n
            if not self.__candidate.isempty():
                if self.__context.isempty():
                    self.__context.reset()
                self.__next()
            elif not self.__word.isempty():
                if self.__context.isempty():
                    self.__context.reset()
                self.__next()
            elif not self.__context.isempty():
                self.__context.reset()
            else:
                context.write(c)

        elif c == 0x10: # C-p
            if self.__iscooking():
                self.__clear()
                self.__prev()
            else:
                context.write(c)

        elif c == 0x11: # C-q
            if not self.__word.isempty():
                s = self.__draincharacters()
                w = self.__word.get()
                s = kanadb.to_hankata(w + s)
                context.writestring(s)
                self.__clear()
                self.__word.reset()
            else:
                context.write(c)

        elif c == 0x20: # SP 
            if self.__mode.ishan():
                context.write(c)
            elif self.__mode.iszen():
                context.write(eisuudb.to_zenkaku_cp(c))
            elif not self.__candidate.isempty():
                if self.__context.isempty():
                    self.__context.reset()
                self.__next()
            elif not self.__word.isempty():
                if self.__context.isempty():
                    self.__context.reset()
                self.__next()
            elif not self.__context.isempty():
                self.__context.reset()
            else:
                context.write(c)

        elif c < 0x20 or 0x7f < c:
            if self.__mode.isdirect():
                context.write(c)
            else:
                self.__reset()
                context.write(c)

        else:
            if self.__mode.ishan():
                # 半角直接入力
                context.write(c)
            elif self.__mode.iszen():
                # 全角直接入力
                context.write(eisuudb.to_zenkaku_cp(c))
            elif self.__mode.iseisuu():
                # 英数変換モード
                self.__word.append(unichr(c))
                self.__display()
            elif self.__mode.ishira() or self.__mode.iskata():
                # ひらがな変換モード・カタカナ変換モード
                if c == 0x2f and (self.__context.isempty() or self.__context.getbuffer() != u'z'): # /
                    if self.__iscooking():
                        self.__word.append(unichr(c))
                        self.__display()
                    else:
                        self.__mode.starteisuu()
                        self.__refleshtitle()
                        self.__word.reset()
                        self.__word.startedit()
                        self.__display()
                elif c == 0x71: # q
                    if self.__iscooking():
                        s = self.__draincharacters()
                        self.__word.append(s)
                        word = self.__word.get()
                        self.__reset()
                        s = self.__convert_kana(word)
                        context.writestring(s)
                    else:
                        self.__toggle_kana()
                elif c == 0x4c: # L
                    if self.__iscooking():
                        self.__kakutei(context)
                    self.__mode.startzen()
                    self.__reset()
                elif c == 0x6c: # l
                    if self.__iscooking():
                        self.__kakutei(context)
                    self.__mode.reset()
                    self.__reset()
                else:
                    if 0x41 <= c and c <= 0x5a: # A - Z
                        # 大文字のとき
                        self.__context.put(c + 0x20) # 子音に変換し、文字バッファに溜める
                        # 変換中か
                        if not self.__candidate.isempty():
                            # 変換中であれば、現在の候補をバックアップしておく
                            backup, remarks = self.__candidate.getcurrent(kakutei=True)
                            # バックアップがあるとき、変換候補をリセット
                            #self.__clear()
                            self.__candidate.clear(self.__stdout)
                            self.__clear()

                            # 現在の候補を確定
                            context.writestring(backup)
                            self.__word.reset()
                            self.__word.startedit()
                            if self.__context.isfinal():
                                # cが母音のとき、文字バッファを吸い出し、
                                s = self.__context.drain()
                                # 単語バッファに追加
                                self.__word.append(s)

                        # 先行する入力があるか
                        elif self.__word.isempty() or len(self.__word.get()) == 0:
                            # 先行する入力が無いとき、
                            # 単語バッファを編集マーク('▽')とする
                            self.__word.startedit()
                            # cが母音か
                            if self.__context.isfinal():
                                # cが母音のとき、文字バッファを吸い出し、
                                s = self.__context.drain()
                                # 単語バッファに追加
                                self.__word.append(s)
                        else:
                            # 先行する入力があるとき、送り仮名マーク('*')をつける
                            self.__word.startokuri()
                            # cが母音か
                            if self.__context.isfinal():
                                # 送り仮名変換
                                self.__okuri_henkan()

                    elif self.__context.put(c):
                        # 変換中か
                        if not self.__candidate.isempty():
                            # 変換中であれば、確定
                            result, remarks = self.__candidate.getcurrent(kakutei=True)
                            self.__word.reset() 
                            #self.__clear()
                            self.__candidate.clear(self.__stdout)
                            context.writestring(result)
                            if self.__context.isfinal():
                                s = self.__context.drain()
                                context.writestring(s)
                        elif self.__context.isfinal():
                            if self.__word.isempty():
                                s = self.__context.drain()
                                context.writestring(s)
                            else:
                                # 送り仮名変換
                                if self.__word.is_okuri():
                                    self.__okuri_henkan()
                                else:
                                    s = self.__context.drain()
                                    self.__word.append(s)
                    else:
                        self.__reset()
                        context.write(c)
                    self.__display()

        return True # handled

    def onmouseclick(self, context, x, y):
        candidate = self.__candidate
        if candidate.includes(x, y):
            if candidate.position_is_selected(y):
                self.__kakutei(context)
            else:
                self.__candidate.click(x, y)
            self.__display()
        else:
            self.__restore()

    def onmouseup(self, context, x, y):
        pass

    def onmousemove(self, context, x, y):
        candidate = self.__candidate
        if candidate.isshown() and candidate.includes(x, y):
            candidate.click(x, y)
            self.__display()

    def onmousedragmove(self, context, x, y):
        if self.__dragstart_pos:
            origin_x, origin_y = self.__dragstart_pos
            offset_x = x - origin_x
            offset_y = y - origin_y
            candidate = self.__candidate
            candidate.set_offset(self.__stdout, offset_x, offset_y)
            self.__display()

    def onmousedragstart(self, context, x, y):
        if self.__candidate.includes(x, y):
            self.__dragstart_pos = (x, y)

    def onmousedragend(self, context, x, y):
        if self.__dragstart_pos:
            self.__dragstart_pos = None
            self.__candidate.erase(self.__stdout)
            self.__candidate.offset_left = 0 
            self.__candidate.offset_top = 0 
            self.__display()

    def onmousedoubleclick(self, context, x, y):
        self.__kakutei(context)

    def onmousescrolldown(self, context, x, y):
        self.__candidate.movenext()
        self.__display()

    def onmousescrollup(self, context, x, y):
        self.__candidate.moveprev()
        self.__display()

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
                if now - self._lastclick < 0.1:
                    self.onmousedoubleclick(context, x, y)
                else:
                    self.onmouseclick(context, x, y)
                self._lastclick = now
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

    def handle_csi(self, context, parameter, intermediate, final):

        mouse_info = self._decode_mouse(context, parameter, intermediate, final)
        if mouse_info:
            mode, mouseup, code, x, y = mouse_info 
            if mode == 1000:
                self.__mouse_state = [] 
                return True
            elif self.__candidate.isshown():
                if mouseup:
                    code |= 0x3
                self.__dispatch_mouse(context, code, x, y) 
                return True
            if self.__mouse_mode.protocol == 1006:
                if mode == 1006: 
                    return False
                elif mode == 1015:
                    params = (code + 32, x, y)
                    context.writestring("\x1b[%d;%d;%dM" % params)
                    return True
                elif mode == 1000:
                    params = (Min(0x7e, code) + 32, x + 32, y + 32)
                    context.writestring("\x1b[M%c%c%c" % params)
                    return True
                return True
            if self.__mouse_mode.protocol == 1015:
                if mode == 1015: 
                    return False
                elif mode == 1006:
                    params = (code + 32, x, y)
                    if mouseup:
                        context.writestring("\x1b[%d;%d;%dm" % params)
                    else:
                        context.writestring("\x1b[%d;%d;%dM" % params)
                    return True
                elif mode == 1000:
                    params = (Min(0x7e, code) + 32, x + 32, y + 32)
                    context.writestring("\x1b[M%c%c%c" % params)
                    return True
            else:
                return True
            return True

        return False 


