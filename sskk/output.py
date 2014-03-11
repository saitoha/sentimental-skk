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


from canossa import tff
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class OutputHandler(tff.DefaultHandler):

    def __init__(self, screen, mode_handler):
        """
        >>> mode_handler = tff.DefaultHandler()
        >>> from canossa import Screen, termprop
        >>> termprop = termprop.MockTermprop()
        >>> screen = Screen(24, 80, 0, 0, "utf-8", termprop)
        >>> output_handler = OutputHandler(screen, mode_handler)
        >>> output_handler.dirty_flag
        False
        """

        self._output = StringIO()
        self._screen = screen
        self._mode_handler = mode_handler
        self.dirty_flag = False

    def handle_esc(self, context, intermediate, final):
        return self._mode_handler.handle_esc(context, intermediate, final)

    def handle_csi(self, context, parameter, intermediate, final):
        """
        >>> mode_handler = tff.DefaultHandler()
        >>> from canossa import MockScreenWithWindows, termprop
        >>> termprop = termprop.MockTermprop()
        >>> screen = MockScreenWithWindows()
        >>> output_handler = OutputHandler(screen, mode_handler)
        >>> context = tff.MockParseContext()
        >>> output_handler.dirty_flag
        False
        >>> output_handler.handle_csi(context, (), (), 0x4c)
        False
        >>> output_handler.dirty_flag
        True
        """
        if self._mode_handler.handle_csi(context, parameter, intermediate, final):
            return True
        if final in (0x4c, 0x4d, 0x53, 0x54):
            if not intermediate:
                if self._screen.has_visible_windows():
                    self.dirty_flag = True
        return False

    def handle_char(self, context, c):
        """
        >>> mode_handler = tff.DefaultHandler()
        >>> from canossa import MockScreenWithWindows, termprop
        >>> termprop = termprop.MockTermprop()
        >>> screen = MockScreenWithWindows()
        >>> output_handler = OutputHandler(screen, mode_handler)
        >>> context = tff.MockParseContext()
        >>> output_handler.dirty_flag
        False
        >>> output_handler.handle_char(context, 0x0b)
        False
        >>> output_handler.dirty_flag
        False
        >>> screen.cursor.row = screen.scroll_bottom - 1
        >>> output_handler.handle_char(context, 0x0a)
        False
        >>> output_handler.dirty_flag
        True
        """
        if c == 0x0a:  # LF
            screen = self._screen
            if screen.cursor.row == screen.scroll_bottom - 1:
                if screen.has_visible_windows():
                    self.dirty_flag = True
        return False

#    def handle_control_string(self, context, prefix, value):
#        if prefix != 0x5d:  # not OSC
#            return False
#        return False

    def handle_draw(self, context):
        """
        >>> mode_handler = tff.DefaultHandler()
        >>> from canossa import MockScreenWithWindows, termprop
        >>> termprop = termprop.MockTermprop()
        >>> screen = MockScreenWithWindows()
        >>> output_handler = OutputHandler(screen, mode_handler)
        >>> context = tff.MockParseContext()
        >>> output_handler.dirty_flag
        False
        >>> output_handler.handle_csi(context, (), (), 0x4c)
        False
        >>> output_handler.dirty_flag
        True
        >>> output_handler.handle_draw(context)
        False
        >>> output_handler.dirty_flag
        False
        """
        screen = self._screen
        output = self._output
        screen.cursor.attr.draw(output)
        context.puts(output.getvalue())
        output.truncate(0)

        if self.dirty_flag:
            self.dirty_flag = False
            y, x = screen.getyx()
            screen.drawall(context)
            #screen.update_when_scroll(context, 1)
            screen.drawwindows(context)
            context.puts("\x1b[%d;%dH" % (y + 1, x + 1))

        return False


def test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()
