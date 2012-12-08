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



class MouseMode():
    """
    >>> import StringIO
    >>> s = StringIO.StringIO()
    >>> mouse_mode = MouseMode()
    >>> mouse_mode.set_on(s)
    >>> print s.getvalue().replace("\x1b", "<ESC>")
    >>> s.truncate(0)
    >>> mouse_mode.set_on(s)
    >>> print s.getvalue().replace("\x1b", "<ESC>")
    >>> s.truncate(0)
    """

    protocol = 0
    encoding = 0
    focusmode = 0

    def set_on(self, s):
        s.write(u"\x1b[?1000h")
        s.write(u"\x1b[?1002h")
        s.write(u"\x1b[?1003h")
        s.write(u"\x1b[?1004h")
        s.write(u"\x1b[?1015h")
        s.write(u"\x1b[?1006h")
        s.write(u"\x1b[?30s\x1b[?30l") # hide scroll bar (rxvt)
        s.write(u"\x1b[?7766s\x1b[?7766l") # hide scroll bar (MinTTY)

    def set_off(self, s):
        if self.protocol == 0:
            s.write(u"\x1b[?1000l")
        else:
            s.write(u"\x1b[?%dl" % self.protocol)
            if self.encoding != 0:
                s.write(u"\x1b[?%dl" % self.encoding)
        if self.focusmode == 0:
            s.write(u"\x1b[?1004l")
        s.write(u"\x1b[?30r") # restore scroll bar state (rxvt)
        s.write(u"\x1b[?7766r") # restore scroll bar state (MinTTY)


def test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()

