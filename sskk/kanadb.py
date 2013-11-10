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

#import thread

_kanadb = ((u'あ', u'ア', u'ｱ'),
           (u'い', u'イ', u'ｲ'),
           (u'う', u'ウ', u'ｳ'),
           (u'え', u'エ', u'ｴ'),
           (u'お', u'オ', u'ｵ'),
           (u'ぁ', u'ァ', u'ｧ'),
           (u'ぃ', u'ィ', u'ｨ'),
           (u'ぅ', u'ゥ', u'ｩ'),
           (u'ぇ', u'ェ', u'ｪ'),
           (u'ぉ', u'ォ', u'ｫ'),
           (u'か', u'カ', u'ｶ'),
           (u'き', u'キ', u'ｷ'),
           (u'く', u'ク', u'ｸ'),
           (u'け', u'ケ', u'ｹ'),
           (u'こ', u'コ', u'ｺ'),
           (u'が', u'ガ', u'ｶﾞ'),
           (u'ぎ', u'ギ', u'ｷﾞ'),
           (u'ぐ', u'グ', u'ｸﾞ'),
           (u'げ', u'ゲ', u'ｹﾞ'),
           (u'ご', u'ゴ', u'ｺﾞ'),
           (u'さ', u'サ', u'ｻ'),
           (u'し', u'シ', u'ｼ'),
           (u'す', u'ス', u'ｽ'),
           (u'せ', u'セ', u'ｾ'),
           (u'そ', u'ソ', u'ｿ'),
           (u'ざ', u'ザ', u'ｻﾞ'),
           (u'じ', u'ジ', u'ｼﾞ'),
           (u'ず', u'ズ', u'ｽﾞ'),
           (u'ぜ', u'ゼ', u'ｾﾞ'),
           (u'ぞ', u'ゾ', u'ｿﾞ'),
           (u'た', u'タ', u'ﾀ'),
           (u'ち', u'チ', u'ﾁ'),
           (u'つ', u'ツ', u'ﾂ'),
           (u'て', u'テ', u'ﾃ'),
           (u'と', u'ト', u'ﾄ'),
           (u'だ', u'ダ', u'ﾀﾞ'),
           (u'ぢ', u'ヂ', u'ﾁﾞ'),
           (u'づ', u'ヅ', u'ﾂﾞ'),
           (u'で', u'デ', u'ﾃﾞ'),
           (u'ど', u'ド', u'ﾄﾞ'),
           (u'な', u'ナ', u'ﾅ'),
           (u'に', u'ニ', u'ﾆ'),
           (u'ぬ', u'ヌ', u'ﾇ'),
           (u'ね', u'ネ', u'ﾈ'),
           (u'の', u'ノ', u'ﾉ'),
           (u'は', u'ハ', u'ﾊ'),
           (u'ひ', u'ヒ', u'ﾋ'),
           (u'ふ', u'フ', u'ﾌ'),
           (u'へ', u'ヘ', u'ﾍ'),
           (u'ほ', u'ホ', u'ﾎ'),
           (u'ぱ', u'パ', u'ﾊﾟ'),
           (u'ぴ', u'ピ', u'ﾋﾟ'),
           (u'ぷ', u'プ', u'ﾌﾟ'),
           (u'ぺ', u'ペ', u'ﾍﾟ'),
           (u'ぽ', u'ポ', u'ﾎﾟ'),
           (u'ば', u'バ', u'ﾊﾞ'),
           (u'び', u'ビ', u'ﾋﾞ'),
           (u'ぶ', u'ブ', u'ﾌﾞ'),
           (u'べ', u'ベ', u'ﾍﾞ'),
           (u'ぼ', u'ボ', u'ﾎﾞ'),
           (u'ま', u'マ', u'ﾏ'),
           (u'み', u'ミ', u'ﾐ'),
           (u'む', u'ム', u'ﾑ'),
           (u'め', u'メ', u'ﾒ'),
           (u'も', u'モ', u'ﾓ'),
           (u'や', u'ヤ', u'ﾔ'),
           (u'ゆ', u'ユ', u'ﾕ'),
           (u'よ', u'ヨ', u'ﾖ'),
           (u'ら', u'ラ', u'ﾗ'),
           (u'り', u'リ', u'ﾘ'),
           (u'る', u'ル', u'ﾙ'),
           (u'れ', u'レ', u'ﾚ'),
           (u'ろ', u'ロ', u'ﾛ'),
           (u'わ', u'ワ', u'ﾜ'),
           (u'を', u'ヲ', u'ｦ'),
           (u'っ', u'ッ', u'ｯ'),
           (u'ゃ', u'ャ', u'ｬ'),
           (u'ゅ', u'ュ', u'ｭ'),
           (u'ょ', u'ョ', u'ｮ'),
           (u'ん', u'ン', u'ﾝ'))

_to_kata = {}
_to_hira = {}
_to_hankata = {}


def compile():
    for hira, kata, hankata in _kanadb:
        _to_kata[hira] = kata
        _to_hira[kata] = hira
        _to_hankata[hira] = hankata
        _to_hankata[kata] = hankata


def to_kata(s):
    ''' convert Japanese Hiragana String to Katakana '''
    def conv(c):
        if c in _to_kata:
            return _to_kata[c]
        return c
    return ''.join([conv(c) for c in s])


def to_hira(s):
    ''' convert Japanese Katakana String to Hiragana '''
    def conv(c):
        if c in _to_hira:
            return _to_hira[c]
        return c
    return ''.join([conv(c) for c in s])


def to_hankata(s):
    ''' convert Japanese Kana String to Half-Width-Katakana '''
    def conv(c):
        if c in _to_hankata:
            return _to_hankata[c]
        return c
    return ''.join([conv(c) for c in s])


compile()
#thread.start_new_thread(compile, ())


def test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()
