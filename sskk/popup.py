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

_POPUP_DIR_NORMAL = True
_POPUP_DIR_REVERSE = False
_POPUP_WIDTH_MAX = 20
_POPUP_HEIGHT_MAX = 24

_MOUSE_PROTOCOL_X10          = 9
_MOUSE_PROTOCOL_NORMAL       = 1000
_MOUSE_PROTOCOL_HIGHLIGHT    = 1001
_MOUSE_PROTOCOL_BUTTON_EVENT = 1002
_MOUSE_PROTOCOL_ALL_EVENT    = 1003

_MOUSE_ENCODING_UTF8         = 1005
_MOUSE_ENCODING_SGR          = 1006
_MOUSE_ENCODING_URXVT        = 1015

_FOCUS_EVENT_TRACKING        = 1004

import time
import tff

class IMouseMode():

    def setenabled(self, value):
        raise NotImplementedError("IMouseMode::setenabled")

    def getprotocol(self):
        raise NotImplementedError("IMouseMode::getprotocol")
        
    def setprotocol(self, protocol):
        raise NotImplementedError("IMouseMode::setprotocol")

    def getencoding(self):
        raise NotImplementedError("IMouseMode::getencoding")
        
    def setencoding(self, encoding):
        raise NotImplementedError("IMouseMode::getencoding")

    def getfocusmode(self):
        raise NotImplementedError("IMouseMode::getfocusmode")

    def setfocusmode(self, mode):
        raise NotImplementedError("IMouseMode::setfocusmode")

class IFocusListener():

    def onfocusin(self):
        raise NotImplementedError("IFocusListener::onfocusin")

    def onfocusout(self):
        raise NotImplementedError("IFocusListener::onfocusout")

class IMouseListener():

    def onmouseup(self, context, x, y):
        raise NotImplementedError("IMouseListener::onmouseup")

    def onclick(self, context, x, y):
        raise NotImplementedError("IMouseListener::onclick")

    def ondoubleclick(self, context, x, y):
        raise NotImplementedError("IMouseListener::ondoubleclick")

    def onmousemove(self, context, x, y):
        raise NotImplementedError("IMouseListener::onmousemove")

    """ scroll """
    def onscrolldown(self, context, x, y):
        raise NotImplementedError("IMouseListener::onscrolldown")

    def onscrollup(self, context, x, y):
        raise NotImplementedError("IMouseListener::onscrollup")

    """ drag and drop """
    def ondragstart(self, s, x, y):
        raise NotImplementedError("IMouseListener::ondragstart")

    def ondragend(self, s, x, y):
        raise NotImplementedError("IMouseListener::ondragend")

    def ondragmove(self, context, x, y):
        raise NotImplementedError("IMouseListener::ondragmove")

class IModeListener():

    def notifyenabled(self, n):
        raise NotImplementedError("IModeListener::notifyenabled")

    def notifydisabled(self, n):
        raise NotImplementedError("IModeListener::notifydisabled")


class IListbox():

    def assign(self, a_list):
        raise NotImplementedError("IListbox::assign")

    def isempty(self):
        raise NotImplementedError("IListbox::isempty")

    def reset(self):
        raise NotImplementedError("IListbox::reset")

    def movenext(self):
        raise NotImplementedError("IListbox::movenext")

    def moveprev(self):
        raise NotImplementedError("IListbox::moveprev")

    def draw(self, s):
        raise NotImplementedError("IListbox::draw")

    def hide(self, s):
        raise NotImplementedError("IListbox::hide")
 
    def isshown(self):
        raise NotImplementedError("IListbox::isshown")

class IListboxListener():

    def onselected(self, index, text, remarks):
        raise NotImplementedError("IListboxListener::onselected")

    def onsettled(self, context):
        raise NotImplementedError("IListboxListener::onsettled")

class MouseDecoder(tff.DefaultHandler):

    _mouse_state = None
    _x = 0
    _y = 0
    _lastclick = 0
    _mousedown = False
    _mousedrag = False
    _mouse_mode = None

    def __init__(self, popup, termprop, mouse_mode):
        self._mouse_mode = mouse_mode
        self._termprop = termprop
        self._popup = popup

    """ tff.EventObserver overrides """
    def handle_csi(self, context, parameter, intermediate, final):
        ''' '''
        if self._mouse_mode:
            try:
                mouse_info = self._decode_mouse(context, parameter, intermediate, final)
                if mouse_info:
                    mode, mouseup, code, x, y = mouse_info 
                    if mode == _MOUSE_PROTOCOL_NORMAL:
                        self._mouse_state = [] 
                        return True
                    elif self._popup.isshown():
                        if mouseup:
                            code |= 0x3
                        self.__dispatch_mouse(context, code, x, y) 
                        return True
                    if self._mouse_mode.getprotocol() == _MOUSE_ENCODING_SGR:
                        if mode == _MOUSE_ENCODING_SGR: 
                            return False
                        elif mode == _MOUSE_ENCODING_URXVT:
                            params = (code + 32, x, y)
                            context.puts("\x1b[%d;%d;%dM" % params)
                            return True
                        elif mode == _MOUSE_PROTOCOL_NORMAL:
                            params = (min(0x7e, code) + 32, x + 32, y + 32)
                            context.puts("\x1b[M%c%c%c" % params)
                            return True
                        return True
                    if self._mouse_mode.getprotocol() == _MOUSE_ENCODING_URXVT:
                        if mode == _MOUSE_ENCODING_URXVT: 
                            return False
                        elif mode == _MOUSE_ENCODING_SGR:
                            params = (code + 32, x, y)
                            if mouseup:
                                context.puts("\x1b[%d;%d;%dm" % params)
                            else:
                                context.puts("\x1b[%d;%d;%dM" % params)
                            return True
                        elif mode == _MOUSE_PROTOCOL_NORMAL:
                            params = (min(0x7e, code) + 32, x + 32, y + 32)
                            context.puts("\x1b[M%c%c%c" % params)
                            return True
                    else:
                        return True
            finally:
                # TODO: logging
                pass

        if len(intermediate) == 0:
            if len(parameter) == 0:
                if final == 0x49: # I
                    self._popup.onfocusin()                    
                    return True
                elif final == 0x4f: # O
                    self._popup.onfocusout()                    
                    return True
        return False 

    def handle_char(self, context, c):
        # xterm's X10/normal mouse encoding could not be handled 
        # by TFF filter because it is not ECMA-48 compatible sequense,
        # so we make custome handler and check 3 bytes after CSI M.
        if not self._mouse_state is None:
            if c >= 0x20 and c < 0x7f:
                self._mouse_state.append(c - 0x20)
                if len(self._mouse_state) == 3:
                    code, x, y = self._mouse_state
                    self._mouse_state = None
                    if self._popup.isshown():
                        self.__dispatch_mouse(context, code, x - 1, y - 1) 
                    if self._mouse_mode.getprotocol() != 0:
                        params = (code + 0x20, x + 0x20, y + 0x20)
                        context.puts("\x1b[M%c%c%c" % params)
                return True
        return False

    def _decode_mouse(self, context, parameter, intermediate, final):
        if len(parameter) == 0:
            if final == 0x4d: # M
                return _MOUSE_PROTOCOL_NORMAL, None, None, None, None
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
                return _MOUSE_ENCODING_SGR, False, code, x, y 
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
                return _MOUSE_ENCODING_SGR, True, code, x, y 
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
                self._popup.ondragmove(context, x, y)
            elif self._mousedown:
                self._mousedrag = True
                self._popup.ondragstart(context, x, y)
            else:
                self._popup.onmousemove(context, x, y)

        elif code & 0x3 == 0x3: # mouse up
            self._mousedown = False
            if self._mousedrag:
                self._mousedrag = False
                self._popup.ondragend(context, x, y)
            elif x == self._x and y == self._y:
                now = time.time()
                if now - self._lastclick < 0.1:
                    self._popup.ondoubleclick(context, x, y)
                else:
                    self._popup.onclick(context, x, y)
                self._lastclick = now
            else:
                self._popup.onmouseup(context, x, y)

        elif code & 64: # mouse scroll
            if code & 0x1:
                self._popup.onscrollup(context, x, y)
            else:
                self._popup.onscrolldown(context, x, y)
        else: # mouse down
            self._x = x
            self._y = y
            self._mousedown = True
            self._mousedrag = False

class IListboxImpl(IListbox):

    _style_active   = { 'selected'  : u'\x1b[0;1;37;42m',
                        'unselected': u'\x1b[0;1;37;41m' }

    _style_inactive = { 'selected'  : u'\x1b[0;1;37;41m',
                        'unselected': u'\x1b[0;1;37;42m' }

    _style = _style_active

    """ IListbox implementation """
    def assign(self, l):
        self._list = l
        self._index = 0
        text, remarks = self._getcurrent()
        self._listener.onselected(self._index, text, remarks)

    def isempty(self):
        return self._list == None

    def reset(self):
        self._width = 8
        self._height = 0
        self._left = None
        self._top = None
        self._offset_left = 0
        self._offset_top = 0
        self._list = None
        self._index = 0

    def movenext(self):
        if self._index < len(self._list) - 1:
            self._index += 1
            if self._index - self._height + 1 > self._scrollpos:
                self._scrollpos = self._index - self._height + 1 
            text, remarks = self._getcurrent()
            self._listener.onselected(self._index, text, remarks)
            return True
        return False

    def moveprev(self):
        if self._index > 0:
            self._index -= 1
            if self._index < self._scrollpos:
                self._scrollpos = self._index
            text, remarks = self._getcurrent()
            self._listener.onselected(self._index, text, remarks)

    def draw(self, s):
        if self._list:
            l, pos, left, top, width, height = self._getdisplayinfo()
                
            self._left = left 
            self._top = top 
            self._width = width
            self._height = height

            if self._show:
                if self._left < left:
                    self._screen.copyrect(s, self._left, top, left - self._left, height)
                if self._left + self._width > left + width:
                    self._screen.copyrect(s, left + width, top, self._left + self._width - (left + width), height)
            elif not self._mouse_mode is None:
                self._mouse_mode.setenabled(self._output, True)

            left += self._offset_left
            top += self._offset_top

            style_selected = self._style['selected']
            style_unselected = self._style['unselected']

            for i, value in enumerate(l):
                if i == pos: # selected line 
                    s.write(style_selected)
                else: # unselected lines 
                    s.write(style_unselected)
                s.write(u'\x1b[%d;%dH' % (top + 1 + i, left + 1))
                s.write(u' ' * width)
                if i == pos: s.write(u'\x1b[1m')
                s.write(u'\x1b[%d;%dH' % (top + 1 + i, left + 1))
                s.write(value)
                s.write(u'\x1b[m')

            y, x = self._screen.getyx()
            s.write(u'\x1b[%d;%dH' % (y + 1, x + 1))
            self._show = True
            return True
        return False

    def hide(self, s):
        if self.isshown(): 
            y, x = self._screen.getyx()
            s.write(u"\x1b[%d;%dH" % (y + 1, x + 1))
            self._show = False
            self._screen.copyrect(s,
                                  self._left + self._offset_left,
                                  self._top + self._offset_top,
                                  self._width,
                                  self._height)
            s.write(u"\x1b[%d;%dH" % (y + 1, x + 1))
            if not self._mouse_mode is None:
                self._mouse_mode.setenabled(self._output, False)
        self.reset()
 
    def isshown(self):
        return self._show

#    def learn(self):
#        self._list.insert(0, self._list.pop(self._index))

    def _truncate_str(self, s, length):
        if self._termprop.wcswidth(s) > length:
            return s[:length] + u"..."
        return s

    def _getcurrent(self):
        value = self._list[self._index]

        # 補足説明
        index = value.find(u";")
        if index >= 0:
            result = value[:index]
            remarks = value[index:]
        else:
            result = value
            remarks = None
        return result, remarks 

    def _getdisplayinfo(self):
        width = 0
        l = [self._truncate_str(s, _POPUP_WIDTH_MAX) for s in self._list]

        y, x = self._screen.getyx()

        vdirection = self._getdirection(y)
        if vdirection == _POPUP_DIR_NORMAL:
            height = self._screen.height - (y + 1) 
        else:
            height = y 

        height = min(height, _POPUP_HEIGHT_MAX)

        if len(l) > height:
            l = l[self._scrollpos:self._scrollpos + height]
            pos = self._index - self._scrollpos
        else:
            pos = self._index

        for value in l:
            width = max(width, self._termprop.wcswidth(value) + 6)

        height = min(height, len(l))

        if x + width > self._screen.width:
            offset = x + width - self._screen.width + 1
        else:
            offset = 0

        if vdirection == _POPUP_DIR_NORMAL:
            top = y + 1
        else:
            top = y - height

        if offset > 0:
            left = x - offset
        else:
            left = x

        return l, pos, left, top, width, height

    def _getdirection(self, row):
        screen = self._screen
        if row * 2 > screen.height:
            vdirection = _POPUP_DIR_REVERSE
        else:            
            vdirection = _POPUP_DIR_NORMAL 
        return vdirection

class IFocusListenerImpl(IFocusListener):

    """ IFocusListener implementation """
    def onfocusin(self):
        self._style = self._style_active

    def onfocusout(self):
        self._style = self._style_inactive

class IMouseListenerImpl(IMouseListener):

    """ IMouseListener implementation """

    def onmouseup(self, context, x, y):
        pass

    def onclick(self, context, x, y):
        if self._includes(x, y):
            if self._scrollpos + y - self._top == self._index:
                self._listener.onsettled(context)
            else:
                x -= self._offset_left
                y -= self._offset_top
                n = y - self._top
                while self._scrollpos + n < self._index:
                    self.moveprev()
                while self._scrollpos + n > self._index:
                    self.movenext()
        elif self.isshown():
            self.hide(self._output)

    def ondoubleclick(self, context, x, y):
        self._listener.onsettled(context)

    def onmousemove(self, context, x, y):
        if self.isshown() and self._includes(x, y):
            x -= self._offset_left
            y -= self._offset_top
            n = y - self._top
            while self._scrollpos + n < self._index:
                self.moveprev()
            while self._scrollpos + n > self._index:
                self.movenext()

    """ scroll """
    def onscrolldown(self, context, x, y):
        self.movenext()

    def onscrollup(self, context, x, y):
        self.moveprev()

    """ drag and drop """
    def ondragstart(self, s, x, y):
        if self._includes(x, y):
            x -= self._offset_left
            y -= self._offset_top
            self._dragpos = (x, y)

    def ondragend(self, s, x, y):
        self._dragpos = None

    def ondragmove(self, context, x, y):
        if self._dragpos:
            origin_x, origin_y = self._dragpos
            offset_x = x - origin_x
            offset_y = y - origin_y

            screen = self._screen
            if self._left + offset_x < 0:
                offset_x = 0 - self._left
            elif self._left + self._width + offset_x > screen.width:
                offset_x = screen.width - self._left - self._width
            if self._top + offset_y < 0:
                offset_y = 0 - self._top
            elif self._top + self._height + offset_y > screen.height:
                offset_y = screen.height - self._top - self._height

            s = self._output
            self._clearDeltaX(s, offset_x)
            self._clearDeltaY(s, offset_y)

            self._offset_left = offset_x
            self._offset_top = offset_y 

    def _includes(self, x, y):
        x -= self._offset_left
        y -= self._offset_top
        if not self.isshown():
            return False
        elif x < self._left:
            return False
        elif x >= self._left + self._width:
            return False
        elif y < self._top:
            return False
        elif y >= self._top + self._height:
            return False
        return True

    def _clearDeltaX(self, s, offset_x):
        screen = self._screen
        if self._offset_left < offset_x:
            screen.copyrect(s,
                            self._left + self._offset_left,
                            self._top + self._offset_top,
                            offset_x - self._offset_left,
                            self._height)
        elif self._offset_left > offset_x:
            screen.copyrect(s,
                            self._left + self._width + offset_x,
                            self._top + self._offset_top,
                            self._offset_left - offset_x,
                            self._height)

    def _clearDeltaY(self, s, offset_y):
        screen = self._screen
        if self._offset_top < offset_y:
            screen.copyrect(s,
                            self._left + self._offset_left,
                            self._top + self._offset_top,
                            self._width,
                            offset_y - self._offset_top)
        elif self._offset_top > offset_y:
            screen.copyrect(s,
                            self._left + self._offset_left,
                            self._top + self._height + offset_y,
                            self._width,
                            self._offset_top - offset_y)

class Listbox(tff.DefaultHandler,
              IListboxImpl,
              IFocusListenerImpl,
              IMouseListenerImpl):

    _left = None
    _top = None
    _width = 10
    _height = _POPUP_HEIGHT_MAX
    _offset_left = 0
    _offset_top = 0

    _output = None

    _show = False 
    _mouse_mode = None
    _dragpos = None

    _list = None
    _index = 0
    _scrollpos = 0

    _listener = None

    def __init__(self, listener, screen, termprop, mouse_mode, output):
        self._mouse_decoder = MouseDecoder(self, termprop, mouse_mode)
        self._screen = screen
        self._listener = listener
        self._termprop = termprop
        self._mouse_mode = mouse_mode
        self._output = output

    def set_offset(self, offset_x, offset_y):

        l, pos, left, top, width, height = self._getdisplayinfo()

        screen = self._screen

        if left + offset_x < 0:
            offset_x = 0 - self._left
        elif left + width + offset_x > screen.width - 1:
            offset_x = screen.width - left - width

        self._offset_left = offset_x
        self._offset_top = offset_y

    """ tff.EventObserver override """
    def handle_char(self, context, c):
        if self.isshown():
            if self._mouse_decoder.handle_char(context, c):
                pass
            elif c == 0x0d: # CR C-m
                self._listener.onsettled(context)
            elif c == 0x0a: # LF C-j
                self._listener.onsettled(context)
            elif c == 0x07: # BEL C-g
                self.hide(self._output)
            elif c == 0x08 or c == 0x7f: # BS or DEL
                self._listener.onsettled(context)
                context.write(c)
            elif c == 0x09: # TAB C-i
                self.movenext()
            elif c == 0x0e: # C-n
                self.movenext()
            elif c == 0x10: # C-p
                self.moveprev()
            elif c == 0x1b: # ESC C-[ 
                self.hide(self._output)
            elif c == 0x02: # C-b 
                return False
            elif c == 0x06: # C-f 
                return False
            elif c < 0x20: # other control chars 
                self._listener.onsettled(context)
                context.write(c)
            elif c == 0x20: # SP 
                self.movenext()
            elif c == 0x71: # q
                self._listener.onsettled(context)
                return False
            elif c == 0x78: # x
                self.moveprev()
            elif 0x40 < c and c <= 0x7e:
                self._listener.onsettled(context)
                return False
            #elif 0x41 <= c and c <= 0x5a: # A - Z
            #    self._listener.onsettled(context)
            #    return False
            #elif 0x61 <= c and c <= 0x7a: # a - z
            #    self._listener.onsettled(context)
            #    return False
            return True
        return False

    def handle_csi(self, context, parameter, intermediate, final):
        if self.isshown():
            if self._handle_csi_cursor(context, parameter, intermediate, final):
                return True
            if self._mouse_decoder.handle_csi(context, parameter, intermediate, final):
                return True
        return False

    def handle_ss3(self, context, final):
        if self.isshown():
            if self._handle_ss3_cursor(context, final):
                return True
        return False

    def _handle_csi_cursor(self, context, parameter, intermediate, final):
        if len(intermediate) == 0:
            if final == 0x41: # A
                self.moveprev()
                return True
            elif final == 0x42: # B
                self.movenext()
                return True
        return False

    def _handle_ss3_cursor(self, context, final):
        if final == 0x41: # A
            self.moveprev()
            return True
        elif final == 0x42: # B
            self.movenext()
            return True
        return False

class IMouseModeImpl(IMouseMode):
    """
    >>> import StringIO
    >>> s = StringIO.StringIO()
    >>> mouse_mode = IMouseModeImpl()
    >>> mouse_mode.setenabled(s, True)
    >>> print s.getvalue().replace("\x1b", "<ESC>")
    <ESC>[?1000h<ESC>[?1002h<ESC>[?1003h<ESC>[?1004h<ESC>[?1015h<ESC>[?1006h
    >>> s.truncate(0)
    >>> mouse_mode.setenabled(s, False)
    >>> print s.getvalue().replace("\x1b", "<ESC>")
    <ESC>[?1000l<ESC>[?1004l
    >>> s.truncate(0)
    """

    _protocol = 0
    _encoding = 0
    _focusmode = 0

    def setenabled(self, s, value):

        if value:
            s.write(u"\x1b[?1000h")
            s.write(u"\x1b[?1002h")
            s.write(u"\x1b[?1003h")
            s.write(u"\x1b[?1004h")
            s.write(u"\x1b[?1015h")
            s.write(u"\x1b[?1006h")
            #s.write(u"\x1b[?30s\x1b[?30l") # hide scroll bar (rxvt)
            #s.write(u"\x1b[?7766s\x1b[?7766l") # hide scroll bar (MinTTY)
        else:
            if self._protocol == 0:
                s.write(u"\x1b[?1000l")
            else:
                s.write(u"\x1b[?%dl" % self._protocol)
                if self._encoding != 0:
                    s.write(u"\x1b[?%dl" % self._encoding)
            if self._focusmode == 0:
                s.write(u"\x1b[?1004l")
            #s.write(u"\x1b[?30r") # restore scroll bar state (rxvt)
            #s.write(u"\x1b[?7766r") # restore scroll bar state (MinTTY)

    def getprotocol(self):
        return self._protocol

    def setprotocol(self, protocol):
        self._protocol = protocol

    def getencoding(self):
        return self._encoding

    def setencoding(self, encoding):
        self._encoding = encoding

    def getfocusmode(self):
        return self._focusmode

    def setfocusmode(self, mode):
        self._focusmode = mode

def _parse_params(params, minimum=0, offset=0, minarg=1):
    param = 0
    for c in params:
        if c < 0x3a:
            param = param * 10 + c - 0x30
        elif c < 0x3c:
            param += offset 
            if minimum > param:
                yield minimum
            else:
                yield param
            minarg -= 1
            param = 0
    param += offset 
    if minimum > param:
        yield minimum
    else:
        yield param
    minarg -= 1
    yield param 
    if minarg > 0:
        yield minimum

class ModeHandler(tff.DefaultHandler, IMouseModeImpl):

    def __init__(self, listener):
        self._listener = listener

    def handle_esc(self, context, intermediate, final):
        if final == 0x63 and len(intermediate) == 0: # RIS
            self.setprotocol(0)
            self.setencoding(0)
            self.setfocusmode(0)
        return False

    def handle_csi(self, context, parameter, intermediate, final):
        if self._handle_mode(context, parameter, intermediate, final):
            return True
        return False

    def _handle_mode(self, context, parameter, intermediate, final):
        if len(parameter) >= 5:
            if parameter[0] == 0x3f and len(intermediate) == 0:
                params = _parse_params(parameter[1:])
                if final == 0x68: # 'h'
                    modes = self._set_modes(params)
                    if len(modes) > 0:
                        context.puts("\x1b[?%sh" % ";".join(modes))
                    return True
                elif final == 0x6c: # 'l'
                    modes = self._reset_modes(params)
                    if len(modes) > 0:
                        context.puts("\x1b[?%sl" % ";".join(modes))
                    return True
        return False

    def _set_modes(self, params):
        modes = []
        for param in params:
            if param >= 100:
                if param == _MOUSE_PROTOCOL_NORMAL:
                    self.setprotocol(_MOUSE_PROTOCOL_NORMAL)
                    modes.append(str(param))
                elif param == _MOUSE_PROTOCOL_HIGHLIGHT:
                    self.setprotocol(_MOUSE_PROTOCOL_HIGHLIGHT)
                    modes.append(str(param))
                elif param == _MOUSE_PROTOCOL_BUTTON_EVENT:
                    self.setprotocol(_MOUSE_PROTOCOL_BUTTON_EVENT)
                    modes.append(str(param))
                elif param == _MOUSE_PROTOCOL_ALL_EVENT:
                    self.setprotocol(_MOUSE_PROTOCOL_ALL_EVENT)
                    modes.append(str(param))
                elif param == _FOCUS_EVENT_TRACKING:
                    self.setfocusmode(_FOCUS_EVENT_TRACKING)
                elif param == _MOUSE_ENCODING_UTF8:
                    self.setencoding(_MOUSE_ENCODING_UTF8)
                elif param == _MOUSE_ENCODING_URXVT:
                    self.setencoding(_MOUSE_ENCODING_URXVT)
                elif param == _MOUSE_ENCODING_SGR:
                    self.setencoding(_MOUSE_ENCODING_SGR)
                elif param >= 8860 and param < 8870:
                    if not self._listener.notifyenabled(param):
                        modes.append(str(param))
                else:
                    modes.append(str(param))
            else:
                modes.append(str(param))
        return modes

    def _reset_modes(self, params):
        modes = []
        for param in params:
            if param >= 1000:
                if param == _MOUSE_PROTOCOL_NORMAL:
                    self.setprotocol(0)
                    modes.append(str(param))
                elif param == _MOUSE_PROTOCOL_HIGHLIGHT:
                    self.setprotocol(0)
                    modes.append(str(param))
                elif param == _MOUSE_PROTOCOL_BUTTON_EVENT:
                    self.setprotocol(0)
                    modes.append(str(param))
                elif param == _MOUSE_PROTOCOL_ALL_EVENT:
                    self.setprotocol(0)
                    modes.append(str(param))
                elif param == _FOCUS_EVENT_TRACKING:
                    self.setfocusmode(0)
                elif param == _MOUSE_ENCODING_UTF8:
                    self.setencoding(0)
                elif param == _MOUSE_ENCODING_URXVT:
                    self.setencoding(0)
                elif param == _MOUSE_ENCODING_SGR:
                    self.setencoding(0)
                elif param >= 8860 and param < 8870:
                    if not self._listener.notifydisabled(param):
                        modes.append(str(param))
                else:
                    modes.append(str(param))
            else:
                modes.append(str(param))
        return modes

def test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test()

