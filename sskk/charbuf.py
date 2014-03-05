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


import romanrule
import settings
import logging


###############################################################################
#
# CharacterContext
#
class CharacterContext:

    def __init__(self):
        """
        >>> chrbuf = CharacterContext()
        """
        method = settings.get("romanrule")
        self.compile(method)

    def compile(self, method=None):
        """
        >>> charbuf = CharacterContext()
        >>> charbuf.compile("builtin_normal")
        """
        # makes trie trees
        try:
            hira_tree, kata_tree = romanrule.compile(method)
        except ImportError, e:
            logging.error(e)
            hira_tree, kata_tree = romanrule.compile()
        except TypeError, e:
            logging.error(e)
            hira_tree, kata_tree = romanrule.compile()
        self._hira_tree = hira_tree
        self._kata_tree = kata_tree
        self.hardreset()

    def toggle(self):
        """
        >>> charbuf = CharacterContext()
        >>> id(charbuf._current_tree) == id(charbuf._hira_tree)
        True
        >>> charbuf.toggle()
        >>> id(charbuf._current_tree) == id(charbuf._hira_tree)
        False
        >>> id(charbuf._current_tree) == id(charbuf._kata_tree)
        True
        >>> charbuf.hardreset()
        >>> id(charbuf._current_tree) == id(charbuf._hira_tree)
        True
        """
        if id(self._current_tree) == id(self._hira_tree):
            self._current_tree = self._kata_tree
        else:
            self._current_tree = self._hira_tree

    def reset(self):
        self.context = self._current_tree

    def hardreset(self):
        self._current_tree = self._hira_tree
        self.reset()

    def isempty(self):
        return id(self.context) == id(self._current_tree)

    def isfinal(self):
        return romanrule.SKK_ROMAN_VALUE in self.context

    def hasnext(self):
        """
        >>> charbuf = CharacterContext()
        >>> charbuf.compile("builtin_normal")
        >>> charbuf.hasnext()
        False
        >>> charbuf.put(ord("k"))
        True
        >>> charbuf.hasnext()
        False
        >>> charbuf.put(ord("a"))
        True
        >>> charbuf.hasnext()
        False
        """
        return romanrule.SKK_ROMAN_NEXT in self.context

    def drain(self):
        """
        >>> charbuf = CharacterContext()
        >>> charbuf.compile("builtin_normal")
        >>> charbuf.drain()
        u''
        >>> charbuf.put(ord("k"))
        True
        >>> charbuf.drain()
        u''
        >>> charbuf.put(ord("a"))
        True
        >>> charbuf.drain()
        u'\u304b'
        >>> charbuf.drain()
        u''
        """
        if romanrule.SKK_ROMAN_VALUE in self.context:
            s = self.context[romanrule.SKK_ROMAN_VALUE]
            if romanrule.SKK_ROMAN_NEXT in self.context:
                self.context = self.context[romanrule.SKK_ROMAN_NEXT]
            else:
                self.reset()
            return s
        return u''

    def getbuffer(self):
        """
        #>>> charbuf = CharacterContext()
        #>>> charbuf.compile("builtin_normal")
        #>>> charbuf.getbuffer()
        #u''
        #>>> charbuf.put(ord("k"))
        #True
        #>>> charbuf.getbuffer()
        #u'k'
        #>>> charbuf.put(ord("y"))
        #True
        #>>> charbuf.put(ord("a"))
        #True
        #>>> charbuf.getbuffer()
        #u'kya'
        #>>> charbuf.getbuffer()
        #u'kya'
        """
        key = romanrule.SKK_ROMAN_BUFFER
        if key in self.context:
            return self.context[key]
        return u''

    def complete(self):
        """
        >>> charbuf = CharacterContext()
        >>> charbuf.compile("builtin_normal")
        >>> charbuf.complete() is None
        True
        >>> charbuf.put(ord("k"))
        True
        >>> len(charbuf.complete()) > 0
        True
        >>> charbuf.put(ord("a"))
        True
        >>> len(charbuf.complete()) > 0
        True
        """
        if not self.getbuffer():
            return None

        def expand(context):
            for key, value in context.items():
                if key == romanrule.SKK_ROMAN_VALUE:
                    yield value
                elif key == romanrule.SKK_ROMAN_NEXT:
                    pass
                elif key == romanrule.SKK_ROMAN_PREV:
                    pass
                elif key == romanrule.SKK_ROMAN_BUFFER:
                    pass
                elif key != 0x6e:
                    for key, value in value.items():
                        if key == romanrule.SKK_ROMAN_VALUE:
                            yield value
        return list(set([c for c in expand(self.context)]))

    def test(self, c):
        """
        >>> charbuf = CharacterContext()
        >>> charbuf.compile("builtin_normal")
        >>> charbuf.test(ord('a'))
        True
        """
        if c in self.context:
            return True
        return False

    def put(self, c):
        """
        >>> charbuf = CharacterContext()
        >>> charbuf.compile("builtin_normal")
        >>> charbuf.put(ord('a'))
        True
        """
        if c in self.context:
            self.context = self.context[c]
            return True
        return False

    def back(self):
        """
        >>> charbuf = CharacterContext()
        >>> charbuf.compile("builtin_normal")
        >>> charbuf.put(ord("k"))
        True
        >>> charbuf.put(ord("y"))
        True
        >>> charbuf.getbuffer()
        u'ky'
        >>> charbuf.back()
        >>> charbuf.getbuffer()
        u'k'
        >>> charbuf.back()
        >>> charbuf.getbuffer()
        u''
        """
        self.context = self.context[romanrule.SKK_ROMAN_PREV]

    def save(self):
        self._backup = self.context

    def restore(self):
        self.context = self._backup

    def handle_char(self, context, c):
        """
        >>> charbuf = CharacterContext()
        >>> charbuf.compile("builtin_normal")
        >>> charbuf.handle_char(None, 0x00)
        False
        """
        return False


def test():
    """
    >>> test()
    """
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    """
    __name__ == '__main__'
    """
    test()
