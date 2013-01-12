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

import kanadb

_rule = {'a'   : u'あ'    , 'i'   : u'い'    , 'u'   : u'う'    , 'e'   : u'え'    , 'o'   : u'お'    ,
         'xa'  : u'ぁ'    , 'xi'  : u'ぃ'    , 'xu'  : u'ぅ'    , 'xe'  : u'ぇ'    , 'xo'  : u'ぉ'    ,
         'va'  : u'う゛ぁ', 'vi'  : u'う゛ぃ', 'vu'  : u'う゛'  , 've'  : u'う゛ぇ', 'vo'  : u'う゛ぉ',
         'ka'  : u'か'    , 'ki'  : u'き'    , 'ku'  : u'く'    , 'ke'  : u'け'    , 'ko'  : u'こ'    ,
         'ga'  : u'が'    , 'gi'  : u'ぎ'    , 'gu'  : u'ぐ'    , 'ge'  : u'げ'    , 'go'  : u'ご'    ,
         'kya' : u'きゃ'  , 'kyi' : u'きぃ'  , 'kyu' : u'きゅ'  , 'kye' : u'きぇ'  , 'kyo' : u'きょ'  ,
         'gya' : u'ぎゃ'  , 'gyi' : u'ぎぃ'  , 'gyu' : u'ぎゅ'  , 'gye' : u'ぎぇ'  , 'gyo' : u'ぎょ'  ,
         'sa'  : u'さ'    , 'si'  : u'し'    , 'su'  : u'す'    , 'se'  : u'せ'    , 'so'  : u'そ'    ,
         'za'  : u'ざ'    , 'zi'  : u'じ'    , 'zu'  : u'ず'    , 'ze'  : u'ぜ'    , 'zo'  : u'ぞ'    ,
         'sya' : u'しゃ'  , 'syi' : u'しぃ'  , 'syu' : u'しゅ'  , 'sye' : u'しぇ'  , 'syo' : u'しょ'  ,
         'sha' : u'しゃ'  , 'shi' : u'し'    , 'shu' : u'しゅ'  , 'she' : u'しぇ'  , 'sho' : u'しょ'  ,
         'ja'  : u'じゃ'  , 'ji'  : u'じ'    , 'ju'  : u'じゅ'  , 'je'  : u'じぇ'  , 'jo'  : u'じょ'  ,
         'jya' : u'じゃ'  , 'jyi' : u'じぃ'  , 'jyu' : u'じゅ'  , 'jye' : u'じぇ'  , 'jyo' : u'じょ'  ,
         'zya' : u'じゃ'  , 'zyi' : u'じぃ'  , 'zyu' : u'じゅ'  , 'zye' : u'じぇ'  , 'zyo' : u'じょ'  ,
         'ta'  : u'た'    , 'ti'  : u'ち'    , 'tu'  : u'つ'    , 'te'  : u'て'    , 'to'  : u'と'    ,
         'da'  : u'だ'    , 'di'  : u'ぢ'    , 'du'  : u'づ'    , 'de'  : u'で'    , 'do'  : u'ど'    ,
         'cha' : u'ちゃ'  , 'chi' : u'ち'    , 'chu' : u'ちゅ'  , 'che' : u'ちぇ'  , 'cho' : u'ちょ'  ,
         'tya' : u'ちゃ'  , 'tyi' : u'ちぃ'  , 'tyu' : u'ちゅ'  , 'tye' : u'ちぇ'  , 'tyo' : u'ちょ'  ,
         'tha' : u'てぁ'  , 'thi' : u'てぃ'  , 'thu' : u'てゅ'  , 'the' : u'てぇ'  , 'tho' : u'てょ'  ,
         'dya' : u'ぢゃ'  , 'dyi' : u'ぢぃ'  , 'dyu' : u'ぢゅ'  , 'dye' : u'ぢぇ'  , 'dyo' : u'ぢょ'  ,
         'dha' : u'でゃ'  , 'dhi' : u'でぃ'  , 'dhu' : u'でゅ'  , 'dhe' : u'でぇ'  , 'dho' : u'でょ'  ,
         'na'  : u'な'    , 'ni'  : u'に'    , 'nu'  : u'ぬ'    , 'ne'  : u'ね'    , 'no'  : u'の'    ,
         'nya' : u'にゃ'  , 'nyi' : u'にぃ'  , 'nyu' : u'にゅ'  , 'nye' : u'にぇ'  , 'nyo' : u'にょ'  ,
         'ha'  : u'は'    , 'hi'  : u'ひ'    , 'hu'  : u'ふ'    , 'he'  : u'へ'    , 'ho'  : u'ほ'    ,
         'pa'  : u'ぱ'    , 'pi'  : u'ぴ'    , 'pu'  : u'ぷ'    , 'pe'  : u'ぺ'    , 'po'  : u'ぽ'    ,
         'ba'  : u'ば'    , 'bi'  : u'び'    , 'bu'  : u'ぶ'    , 'be'  : u'べ'    , 'bo'  : u'ぼ'    ,
         'fa'  : u'ふぁ'  , 'fi'  : u'ふぃ'  , 'fu'  : u'ふ'    , 'fe'  : u'ふぇ'  , 'fo'  : u'ふぉ'  ,
         'hya' : u'ひゃ'  , 'hyi' : u'ひぃ'  , 'hyu' : u'ひゅ'  , 'hye' : u'ひぇ'  , 'hyo' : u'ひょ'  ,
         'fya' : u'ふゃ'  , 'fyi' : u'ふぃ'  , 'fyu' : u'ふゅ'  , 'fye' : u'ふぇ'  , 'fyo' : u'ふょ'  ,
         'bya' : u'びゃ'  , 'byi' : u'びぃ'  , 'byu' : u'びゅ'  , 'bye' : u'びぇ'  , 'byo' : u'びょ'  ,
         'ma'  : u'ま'    , 'mi'  : u'み'    , 'mu'  : u'む'    , 'me'  : u'め'    , 'mo'  : u'も'    ,
         'mya' : u'みゃ'  , 'myi' : u'みぃ'  , 'myu' : u'みゅ'  , 'mye' : u'みぇ'  , 'myo' : u'みょ'  ,
         'ya'  : u'や'    , 'yi'  : u'い'    , 'yu'  : u'ゆ'    , 'ye'  : u'いぇ'  , 'yo'  : u'よ'    ,
         'ra'  : u'ら'    , 'ri'  : u'り'    , 'ru'  : u'る'    , 're'  : u'れ'    , 'ro'  : u'ろ'    ,
         'rya' : u'りゃ'  , 'ryi' : u'りぃ'  , 'ryu' : u'りゅ'  , 'rye' : u'りぇ'  , 'ryo' : u'りょ'  ,
         'wa'  : u'わ'    , 'wi'  : u'うぃ'  , 'wu'  : u'う'    , 'we'  : u'うぇ'  , 'wo'  : u'を'    ,
         'nn'  : u'ん'    , 'tsu' : u'つ'    , 'xtu' : u'っ'    , 'xtsu': u'っ'    , 
         '-'   : u'ー'    , ','   : u'、'    , '.'   : u'。'    , 'z:'  : u'：'    , 'z;'  : u'；'    ,
         'zh'  : u'←'     , 'zj'  : u'↓'     , 'zk'  : u'↑'     , 'zl'  : u'→'     , 'z-'  : u'〜'    ,
         'z,'  : u'‥'     , 'z.'  : u'…'     , 'z/'  : u'・'    , 'z['  : u'『'    , 'z]'  : u'』'    ,
         'z?'  : u'？'    , 'z('  : u'（'    , 'z)'  : u'）'    , 'z{'  : u'【'    , 'z}'  : u'】'    ,
         'zL'  : u'⇒'     , 'z '  : u'　'    ,
         '['   : u'「'    , ']'   : u'」'    , ':'   : u'：'    , ';'   : u'；'                       }

_hira_rule = _rule 
_kata_rule = {}
for key, value in _hira_rule.items():
    _kata_rule[key] = kanadb.to_kata(value) 

SKK_ROMAN_VALUE  = 0
SKK_ROMAN_NEXT   = 1
SKK_ROMAN_PREV   = 2
SKK_ROMAN_BUFFER = 3

def _maketree(rule):
    """ makes try-tree """
    tree = {}
    for key, value in rule.items():
        buf = u''
        context = tree
        for code in [ord(c) for c in key]:
            if not context.has_key(code):
                context[code] = { SKK_ROMAN_PREV: context }
            context = context[code]
            buf += chr(code)
            context[SKK_ROMAN_BUFFER] = buf 
        context[SKK_ROMAN_VALUE] = value
        first = key[0]
        if first in 'bcdfghjkmprstvwxz':
            key = first + key
            value = rule['xtu'] + value
            buf = u''
            context = tree
            for code in [ord(c) for c in key]:
                if not context.has_key(code):
                    context[code] = { SKK_ROMAN_PREV: context }
                context = context[code]
                if buf == chr(code):
                    buf = rule['xtu']
                buf += chr(code)
                context[SKK_ROMAN_BUFFER] = buf 

            context[SKK_ROMAN_VALUE] = value

    for key, value in tree.items(): 
        context = tree
        if key == 0x6e: # 'n'
            for code in [ord(c) for c in 'bcdfghjkmprstvwxz']: 
                value[code] = { SKK_ROMAN_VALUE: rule['nn'],
                                SKK_ROMAN_NEXT: tree[code] }
    tree[SKK_ROMAN_BUFFER] = '' 
    tree[SKK_ROMAN_PREV] = tree 
    return tree

_hira_tree = _maketree(_hira_rule)
_kata_tree = _maketree(_kata_rule)

def makehiratree():
    ''' make hirakana input state tree
    >>> t = makekatatree() 
    >>> t[ord('k')][ord('y')][ord('a')][SKK_ROMAN_VALUE]
    u'\u30ad\u30e3'
    '''
    return _hira_tree

def makekatatree():
    ''' make katakana input state tree
    >>> t = makehiratree() 
    >>> t[ord('k')][ord('y')][ord('a')][SKK_ROMAN_VALUE] 
    u'\u304d\u3083'
    '''
    return _kata_tree

def test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()

