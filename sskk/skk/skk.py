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


# マーク
_SKK_MARK_COOK = u'▽'
_SKK_MARK_SELECT = u'▼'
_SKK_MARK_OKURI = u'*'
_SKK_MARK_OPEN = u'【'
_SKK_MARK_CLOSE = u'】'

################################################################################
#
# InputHandler
#
class InputHandler(tff.DefaultHandler):

    def __init__(self, screen, stdout, termenc):
        self.__screen = screen
        self.__stdout = stdout
        self.__termenc = termenc
        self.__context = context.CharacterContext()
        self.__mode = mode.ModeManager()
        self.__word = word.WordBuffer()
        self.__candidate = candidate.CandidateManager(screen)
        self.__counter = 0

    def __reset(self):
        self.__clear()
        self.__context.reset()
        if not self.__candidate.isempty():
            self.__candidate.clear()
        self.__mode.endeisuu()
        self.__word.reset() 
        self.__refleshtitle()

    def __clear(self):
        candidate_length = wcwidth.wcswidth(_SKK_MARK_SELECT) + self.__candidate.getwidth()
        cooking_length = wcwidth.wcswidth(_SKK_MARK_COOK) + self.__word.length() + wcwidth.wcswidth(self.__context.getbuffer())
        length = max(candidate_length, cooking_length)
        x = self.__screen.cursor.col
        y = self.__screen.cursor.row
        self.__screen.drawrect(x, y, length, 1)
        self.__write(u"\x1b[%d;%dH" % (y + 1, x + 1))
        self.__write(u'%s' % terminfo.cvvis)

    def __write(self, s):
        self.__stdout.write(s.encode(self.__termenc))
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
            seq = self.__candidate.getselections()
            self.__write(
                u'%s\x1b[1;4;32;44m%s%s%s%s%s'
                % (terminfo.sc,
                   result,
                   terminfo.sgr0,
                   terminfo.rc,
                   terminfo.civis,
                   seq))
        elif not self.__word.isempty() or not self.__context.isempty():
            if self.__word.isempty():
                s1 = u''
            elif self.__word.is_okuri():
                s1 = _SKK_MARK_COOK + self.__word.get() + _SKK_MARK_OKURI
            else:
                s1 = _SKK_MARK_COOK + self.__word.get()
            s2 = self.__context.getbuffer() 
            if len(s1) + len(s2) == 0:
                self.__write(u'%s' % terminfo.cvvis)
            else:
                self.__write(
                    u'%s\x1b[1;4;31m%s\x1b[33m%s%s%s%s'
                    % (terminfo.sc, s1, s2, terminfo.sgr0, terminfo.rc, terminfo.civis))
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
        if not result is None:
            self.__candidate.assign(key, result, okuri)
            self.__clear()
            self.__display()
            self.__word.reset() 
            return True

        # かな読みだけを候補とする
        if self.__mode.iskata():
            key = kanadb.to_kata(key)
        self.__candidate.assign(key, [], okuri)

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
        context.writestring(word)
        self.__candidate.clear()
        self.__reset()

    def __restore(self):
        ''' 再変換 '''
        self.__clear()
        self.__word.reset()
        self.__word.append(self.__candidate.getyomi())
        self.__candidate.clear()
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
            self.__clear()
            self.__candidate.movenext()
            self.__display()

    def __prev(self):
        ''' 前候補 '''
        if not self.__candidate.isempty():
            self.__clear()
            self.__candidate.moveprev()
            self.__display()

    def handle_char(self, context, c):
        if c == 0x0a: # LF C-j
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

        elif c == 0x07: # BEL
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
            if not self.__word.isempty():
                self.__next()
            elif not self.__context.isempty():
                self.__reset()
            elif not self.__candidate.isempty():
                self.__next()
            else:
                context.write(c)

        elif c == 0x10: # C-p
            if self.__iscooking():
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
            elif not self.__word.isempty():
                self.__next()
            elif not self.__context.isempty():
                self.__reset()
                context.write(c)
            elif not self.__candidate.isempty():
                self.__next()
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
                            self.__candidate.clear()

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
                            # 先行する入力が無いとき、単語バッファを編集マーク('▽')とする
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
                            self.__candidate.clear()
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

