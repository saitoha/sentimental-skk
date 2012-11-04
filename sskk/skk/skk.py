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

import sys, os

import kanadb
import eisuudb
import romanrule
import dictionary

import tff

################################################################################
#
# CharacterContext
#
class CharacterContext:

    def __init__(self):
        self.__hira_tree = romanrule.makehiratree()
        self.__kata_tree = romanrule.makekatatree()
        self.__current_tree = self.__hira_tree
        self.reset()

    def switch_hira(self):
        self.__current_tree = self.__hira_tree

    def switch_kata(self):
        self.__current_tree = self.__kata_tree

    def reset(self):
        self.context = self.__current_tree

    def isempty(self):
        return self.context == self.__current_tree

    def isfinal(self):
        return self.context.has_key('value')

    def drain(self):
        if self.context.has_key('value'):
            s = self.context['value']
            if self.context.has_key('next'):
                self.context = self.context['next']
            else:
                self.reset()
            return s
        return u''

    def getbuffer(self):
        return self.context['buffer']

    def put(self, c):
        if self.context.has_key(c):
            self.context = self.context[c]
            return True
        return False

    def back(self):
        self.context = self.context['prev']

SKK_MODE_HANKAKU = 0
SKK_MODE_ZENKAKU = 1
SKK_MODE_HIRAGANA = 2
SKK_MODE_KATAKANA = 3
SKK_MODE_EISUU_HENKAN = 4

COOK_MARK = u'▽'
SELECT_MARK = u'▼'
OKURI_MARK = u'*'

################################################################################
#
# Candidate
#
class Candidate():

    def __init__(self):
        self.reset()

    def assign(self, value, okuri=u''):
        self.__index = 0
        self.__list = value.split(u'/')
        self.__okuri = okuri

    def reset(self):
        self.__index = 0
        self.__list = None
        self.__okuri = None

    def isempty(self):
        return self.__list == None

    def getcurrent(self):
        self.__index %= len(self.__list)
        value = self.__list[self.__index]

        # 補足説明
        index = value.find(";")
        if index >= 0:
            result = value[:index]
            remarks = value[index:]
        else:
            result = value
            remarks = None

        return SELECT_MARK + result + self.__okuri, remarks 

    def getwidth(self):
        if self.isempty():
            return 0
        result, remarks = self.getcurrent()
        return len(result) * 2

    def movenext(self):
        self.__index += 1

    def moveprev(self):
        self.__index -= 1

################################################################################
#
# InputHandler
#
class InputHandler(tff.DefaultHandler):

    def __init__(self, stdout, termenc):
        self.__stdout = stdout
        self.__termenc = termenc
        self.__context = CharacterContext()
        self.__mode = SKK_MODE_HANKAKU
        self.__word_buffer = u'' 
        self.__candidate = Candidate()

    def __reset(self):
        self.__clear()
        self.__context.reset()
        self.__candidate.reset()
        self.__word_buffer = u'' 

    def __clear(self):
        candidate_length = self.__candidate.getwidth()
        cooking_length = len(self.__word_buffer) * 2 + len(self.__context.getbuffer())
        s = ' ' * max(candidate_length, cooking_length)
        self.__write('\x1b7%s\x1b8\x1b[?25h' % s)

    def __write(self, s):
        self.__stdout.write(s.encode(self.__termenc))
        self.__stdout.flush()

    def __display(self):
        if not self.__candidate.isempty():
            result, remarks = self.__candidate.getcurrent()

            self.__write('\x1b7\x1b[1;4;32;44m%s\x1b[m\x1b8\x1b[?25l' % result)
            if remarks:
                self.__write('\x1b]0;[sskk] 三 ┏( ^o^)┛ ＜ %s - %s\x07' % (result, remarks))
        else:
            s1 = self.__word_buffer
            s2 = self.__context.getbuffer() 
            if not len(s1) + len(s2) == 0:
                self.__write('\x1b7\x1b[1;4;31m%s\x1b[1;4;33m%s\x1b[m\x1b8\x1b[?25l' % (s1, s2))
            else:
                self.__write('\x1b[?25h')

    def __draincharacters(self):
        s = self.__context.getbuffer()
        if s == 'n':
            self.__context.put(0x6e) # n
        s = self.__context.drain()
        return s

    def __fix(self):
        s = self.__draincharacters()
        if len(self.__word_buffer) == 0:
            self.__word_buffer += COOK_MARK
        self.__word_buffer += s

    def __iscooking(self):
        if not self.__candidate.isempty():
            return True
        if len(self.__word_buffer) > 0:
            return True
        if not self.__context.isempty():
            return True
        return False

    def __convert_kana(self, value):
        if self.__mode == SKK_MODE_HIRAGANA:
            return kanadb.to_kata(value)
        elif self.__mode == SKK_MODE_KATAKANA:
            return kanadb.to_hira(value)
        else:
            raise

    def __toggle_kana(self):
        if self.__mode == SKK_MODE_HIRAGANA:
            self.__mode = SKK_MODE_KATAKANA
            self.__context.switch_kata()
        elif self.__mode == SKK_MODE_KATAKANA:
            self.__mode = SKK_MODE_HIRAGANA
            self.__context.switch_hira()
        else:
            raise
        self.__reset()

    def __tango_henkan(self):
        key = self.__word_buffer[1:]
        result = dictionary.gettango(key)

        if not result is None: 
            self.__write(u'\x1b]0;[sskk] 三 ┏( ^o^)┛ ＜ %s\x07' % (key))
            self.__candidate.assign(result + u'/' + key)
            self.__clear()
            self.__display()
            return True

        # かな読みだけを候補とする
        self.__candidate.assign(key)

        return True

    def __okuri_henkan(self):
        buf = self.__context.getbuffer()[0]
        s = self.__context.drain()
        self.__word_buffer += s
        key, okuri = self.__word_buffer[1:].split(OKURI_MARK)

        result = dictionary.getokuri(key + buf)

        self.__write(u'\x1b]0;[sskk] 三 ┏( ^o^)┛ ＜ %s - %s\x07' % (key, buf))
        if not result is None:
            self.__candidate.assign(result + u'/' + key, okuri)
            self.__clear()
            self.__word_buffer = u''
            return True

        # かな読みだけを候補とする
        self.__candidate.assign(key, okuri)

        return True

    def __kakutei(self, context):
        self.__fix()
        if self.__candidate.isempty():
            word = self.__word_buffer[1:]
        else:
            result, remarks = self.__candidate.getcurrent()
            word = result[1:]
        self.__reset()
        context.writestring(word)
        self.__write(u'\x1b]0;[sskk] ＼(^o^)／\x07')

    def handle_char(self, context, c):
        if c == 0xa5:
            c = 0x5c
        if c == 0x07:
            self.__reset()
        elif c == 0x0a: # LF C-j
            if self.__mode == SKK_MODE_HANKAKU or self.__mode == SKK_MODE_ZENKAKU:
                self.__mode = SKK_MODE_HIRAGANA
            else:
                if self.__iscooking():
                    self.__kakutei(context)
                else:
                    context.write(c)
        elif c == 0x0d: # CR C-m
            if self.__iscooking():
                self.__kakutei(context)
            else:
                context.write(c)
        elif c == 0x08 or c == 0x7f: # BS or DEL
            if self.__context.isempty():
                word = self.__word_buffer
                if not self.__candidate.isempty():
                    self.__candidate.reset()
                    self.__clear()
                    self.__display()
                if len(word) == 0:
                    context.write(c)
                else:
                    self.__clear()
                    self.__word_buffer = word[:-1]
                    self.__display()
            else:
                self.__clear()
                self.__context.back()
                self.__display()
        elif c == 0x20:        
            if self.__mode == SKK_MODE_HANKAKU:
                context.write(c)
            elif self.__mode == SKK_MODE_ZENKAKU:
                context.write(eisuudb.to_zenkaku_cp(c))
            else:
                if self.__iscooking():
                    # 単語変換
                    if self.__candidate.isempty():
                        s = self.__draincharacters()
                        self.__word_buffer += s
                        if not self.__tango_henkan():
                            self.__kakutei(context)
                    else:
                        self.__clear()
                        self.__candidate.movenext()
                        self.__display()
                else:
                    context.write(c)
        elif c < 0x20 or 0x7f < c:
            if self.__mode == SKK_MODE_HANKAKU or self.__mode == SKK_MODE_ZENKAKU:
                context.write(c)
            else:
                self.__reset()
                context.write(c)
        else:
            if self.__mode == SKK_MODE_HANKAKU:
                # 半角直接入力
                context.write(c)
            elif self.__mode == SKK_MODE_ZENKAKU:
                # 全角直接入力
                context.write(eisuudb.to_zenkaku_cp(c))
            elif self.__mode == SKK_MODE_EISUU_HENKAN:
                # 英数変換モード
                if len(self.__word_buffer) == 0:
                    self.__word_buffer = COOK_MARK
                self.__word_buffer += unichr(c)
                self.__display()
            elif self.__mode == SKK_MODE_HIRAGANA or self.__mode == SKK_MODE_KATAKANA:
                # ひらがな変換モード・カタカナ変換モード
                if c == 0x2f: # /
                    if self.__iscooking():
                        self.__word_buffer += unichr(c)
                        self.__display()
                    else:
                        self.__mode = SKK_MODE_EISUU_HENKAN
                        self.__word_buffer = COOK_MARK
                        self.__display()
                elif c == 0x71: # q
                    word = self.__word_buffer
                    if self.__iscooking():
                        self.__fix()
                        word = self.__word_buffer
                        self.__reset()
                        s = self.__convert_kana(word[1:])
                        context.writestring(s)
                    else:
                        self.__toggle_kana()
                elif c == 0x4c: # L
                    if self.__iscooking():
                        self.__kakutei(context)
                    self.__mode = SKK_MODE_ZENKAKU
                    self.__reset()
                elif c == 0x6c: # l
                    if self.__iscooking():
                        self.__kakutei(context)
                    self.__mode = SKK_MODE_HANKAKU
                    self.__reset()
                else:
                    # 変換中か
                    if not self.__candidate.isempty():
                        # 変換中であれば、現在の候補をバックアップしておく
                        backup, remarks = self.__candidate.getcurrent()
                        self.__word_buffer = u''
                    else:
                        backup = None

                    if 0x41 <= c and c <= 0x5a: # A - Z
                        # 大文字のとき
                        self.__context.put(c + 0x20) # 子音に変換し、文字バッファに溜める

                        # バックアップがあるか
                        if backup:
                            # バックアップがあるとき、変換候補をリセット
                            self.__candidate.reset()

                            # 現在の候補を確定
                            context.writestring(backup[1:])
                            self.__word_buffer = COOK_MARK
                            if self.__context.isfinal():
                                # cが母音のとき、文字バッファを吸い出し、
                                s = self.__context.drain()
                                # 単語バッファに追加
                                self.__word_buffer += s
                            s = backup[1:]
                            s += self.__word_buffer
                            s += self.__context.getbuffer()
                            self.__write('\x1b7\x1b[1;4;35m%s\x1b[m\x1b8\x1b[?25l' % s)

                        # 先行する入力があるか
                        elif len(self.__word_buffer) > 1:
                            # 先行する入力があるとき、送り仮名マーク('*')をつける
                            if self.__word_buffer[-1] != OKURI_MARK:
                                self.__word_buffer += OKURI_MARK
                            # cが母音か
                            if self.__context.isfinal():

                                # 送り仮名変換
                                self.__okuri_henkan()

                                ## cが母音のとき、文字バッファを吸い出し、
                                #s = self.__context.drain()
                                ## 単語バッファに追加
                                #self.__word_buffer += s

                        else:
                            # 先行する入力が無いとき、単語バッファを編集マーク('▽')とする
                            self.__word_buffer = COOK_MARK
                            # cが母音か
                            if self.__context.isfinal():
                                # cが母音のとき、文字バッファを吸い出し、
                                s = self.__context.drain()
                                # 単語バッファに追加
                                self.__word_buffer += s

                    elif self.__context.put(c):
                        if not backup is None:
                            self.__candidate.reset()
                            context.writestring(backup[1:])
                            s = backup[1:]
                            s += self.__word_buffer
                            s += self.__context.getbuffer()
                            self.__write('\x1b7\x1b[1;4;31m%s\x1b[m\x1b8\x1b[?25l' % s)
                            self.__word_buffer = u''
                        if self.__context.isfinal():
                            if backup or len(self.__word_buffer) == 0:
                                s = self.__context.drain()
                                context.writestring(s)
                            else:
                                # 送り仮名変換
                                if self.__word_buffer[-1] == OKURI_MARK:
                                    self.__okuri_henkan()
                                    #s = self.__context.drain()
                                    #self.__word_buffer += s
                                else:
                                    s = self.__context.drain()
                                    self.__word_buffer += s
                    else:
                        self.__reset()
                        context.write(c)
                    self.__display()

################################################################################
#
# OutputHandler
#
class OutputHandler(tff.DefaultHandler):

    def __init__(self):
        self.__super = super(OutputHandler, self)

#    def handle_csi(self, context, prefix, params, final):
#        self.__super.handle_csi(context, prefix, params, final)
#
#    def handle_esc(self, context, prefix, final):
#        self.__super.handle_esc(context, prefix, final)
#
    def handle_control_string(self, context, prefix, value):
        if prefix == 0x5d: # ']'
            pos = value.index(0x3b)
            if pos == -1:
                pass
            elif pos == 0:
                num = [0]
            else:
                try:
                    num = value[:pos]
                except:
                    num = None 
            if not num is None:
                if num == [0x30] or num == [0x31] or num == [0x32]:
                    arg = value[pos + 1:]
                    arg = [ord(x) for x in "[sskk] "] + arg
                    value = num + [0x3b] + arg
        self.__super.handle_control_string(context, prefix, value)

#    def handle_char(self, context, c):
#        self.__super.handle_char(context, c)


