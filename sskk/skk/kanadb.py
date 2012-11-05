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

import thread

_kanadb = [[u'あ', u'ア'], [u'い', u'イ'], [u'う', u'ウ'], [u'え', u'エ'], [u'お', u'オ'],
           [u'ぁ', u'ァ'], [u'ぃ', u'ィ'], [u'ぅ', u'ゥ'], [u'ぇ', u'ェ'], [u'ぉ', u'ォ'],
           [u'か', u'カ'], [u'き', u'キ'], [u'く', u'ク'], [u'け', u'ケ'], [u'こ', u'コ'],
           [u'が', u'ガ'], [u'ぎ', u'ギ'], [u'ぐ', u'グ'], [u'げ', u'ゲ'], [u'ご', u'ゴ'],
           [u'さ', u'サ'], [u'し', u'シ'], [u'す', u'ス'], [u'せ', u'セ'], [u'そ', u'ソ'],
           [u'ざ', u'ザ'], [u'じ', u'ジ'], [u'ず', u'ズ'], [u'ぜ', u'ゼ'], [u'ぞ', u'ゾ'],
           [u'た', u'タ'], [u'ち', u'チ'], [u'つ', u'ツ'], [u'て', u'テ'], [u'と', u'ト'],
           [u'だ', u'ダ'], [u'ぢ', u'ヂ'], [u'づ', u'ヅ'], [u'で', u'デ'], [u'ど', u'ド'],
           [u'な', u'ナ'], [u'に', u'ニ'], [u'ぬ', u'ヌ'], [u'ね', u'ネ'], [u'の', u'ノ'],
           [u'は', u'ハ'], [u'ひ', u'ヒ'], [u'ふ', u'フ'], [u'へ', u'ヘ'], [u'ほ', u'ホ'],
           [u'ぱ', u'パ'], [u'ぴ', u'ピ'], [u'ぷ', u'プ'], [u'ぺ', u'ペ'], [u'ぽ', u'ポ'],
           [u'ば', u'バ'], [u'び', u'ビ'], [u'ぶ', u'ブ'], [u'べ', u'ベ'], [u'ぼ', u'ボ'],
           [u'ま', u'マ'], [u'み', u'ミ'], [u'む', u'ム'], [u'め', u'メ'], [u'も', u'モ'],
           [u'や', u'ヤ'], [u'ゆ', u'ユ'], [u'よ', u'ヨ'], [u'ら', u'ラ'], [u'り', u'リ'],
           [u'る', u'ル'], [u'れ', u'レ'], [u'ろ', u'ロ'], [u'わ', u'ワ'], [u'を', u'ヲ'],
           [u'っ', u'ッ'], [u'ゃ', u'ャ'], [u'ゅ', u'ュ'], [u'ょ', u'ョ'], [u'ん', u'ン']]

_hira_to_kata = {}
_kata_to_hira = {}

def _loaddb():
    for hira, kata in _kanadb:
        _hira_to_kata[hira] = kata
        _kata_to_hira[kata] = hira

def to_kata(s):
    ''' convert Japanese Hiragana String into Katakana '''
    def conv(c):
        if _hira_to_kata.has_key(c):
            return _hira_to_kata[c]
        return c
    return ''.join([conv(c) for c in s])

def to_hira(s):
    ''' convert Japanese Katakana String into Hiragana '''
    def conv(c):
        if _kata_to_hira.has_key(c):
            return _kata_to_hira[c]
        return c
    return ''.join([conv(c) for c in s])

_loaddb()
#thread.start_new_thread(_loaddb, ())


