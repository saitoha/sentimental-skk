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


import romanrule

################################################################################
#
# CharacterContext
#
class CharacterContext:

    def __init__(self):
        # makes trie trees 
        self.__hira_tree = romanrule.makehiratree()
        self.__kata_tree = romanrule.makekatatree()
        self.hardreset()

    def toggle(self):
        if id(self.__current_tree) == id(self.__hira_tree):
            self.__current_tree = self.__kata_tree
        else:
            self.__current_tree = self.__hira_tree

    def reset(self):
        self.context = self.__current_tree

    def hardreset(self):
        self.__current_tree = self.__hira_tree
        self.reset()

    def isempty(self):
        return id(self.context) == id(self.__current_tree)

    def isfinal(self):
        return self.context.has_key(romanrule.SKK_ROMAN_VALUE)

    def hasnext(self):
        return self.context.has_key(romanrule.SKK_ROMAN_NEXT)

    def drain(self):
        if self.context.has_key(romanrule.SKK_ROMAN_VALUE):
            s = self.context[romanrule.SKK_ROMAN_VALUE]
            if self.context.has_key(romanrule.SKK_ROMAN_NEXT):
                self.context = self.context[romanrule.SKK_ROMAN_NEXT]
            else:
                self.reset()
            return s
        return u""

    def getbuffer(self):
        key = romanrule.SKK_ROMAN_BUFFER
        if self.context.has_key(key):
            return self.context[key]
        return u""

    def complete(self):
        """
        >>> context = CharacterContext()
        >>> context.put(ord("k"))
        True
        """
        if not self.getbuffer():
            return None
        def expand(context):
            for key, value in context.items():
                if key == romanrule.SKK_ROMAN_VALUE:
                    yield value 
                elif key > 0x1f and key != 0x6e:
                    for key, value in value.items():
                        if key == romanrule.SKK_ROMAN_VALUE:
                            yield value 
        return list(set([c for c in expand(self.context)]))

    def put(self, c):
        if self.context.has_key(c):
            self.context = self.context[c]
            return True
        if 0x41 <= c and c <= 0x5a: # A - Z
            c += 0x20 # convert to a - z
        if self.context.has_key(c):
            self.context = self.context[c]
            return True
        return False

    def back(self):
        self.context = self.context[romanrule.SKK_ROMAN_PREV]

    def handle_char(self, context, c):
        return False

def test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()


