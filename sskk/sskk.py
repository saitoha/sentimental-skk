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

def _getpos(stdin, stdout):
    import os, termios, select
    
    stdin_fileno = stdin.fileno()
    vdisable = os.fpathconf(stdin_fileno, 'PC_VDISABLE')
    backup = termios.tcgetattr(stdin_fileno)
    new = termios.tcgetattr(stdin_fileno)
    new[3] &= ~(termios.ECHO | termios.ICANON)
    new[6][termios.VMIN] = 6
    new[6][termios.VTIME] = 0
    termios.tcsetattr(stdin_fileno, termios.TCSANOW, new)
    try:
        stdout.write("\x1b[6n")
        stdout.flush()
        
        rfd, wfd, xfd = select.select([stdin_fileno], [], [], 0.5)
        if rfd:
            data = os.read(stdin_fileno, 1024)
            assert data[:2] == '\x1b['
            assert data[-1] == 'R'
            pos = [int(n) - 1 for n in data[2:-1].split(';')]
            assert len(pos) == 2
            return pos
    finally:
        termios.tcsetattr(stdin_fileno, termios.TCSANOW, backup)


def _get_da2(stdin, stdout):
    import os, termios, select
    
    stdin_fileno = stdin.fileno()
    vdisable = os.fpathconf(stdin_fileno, 'PC_VDISABLE')
    backup = termios.tcgetattr(stdin_fileno)
    new = termios.tcgetattr(stdin_fileno)
    new[3] &= ~(termios.ECHO | termios.ICANON)
    new[6][termios.VMIN] = 3
    new[6][termios.VTIME] = 0
    termios.tcsetattr(stdin_fileno, termios.TCSANOW, new)
    try:
        stdout.write("\x1b[>0c")
        stdout.flush()
        
        rfd, wfd, xfd = select.select([stdin_fileno], [], [], 0.5)
        if rfd:
            data = os.read(stdin_fileno, 1024)
            assert data[:2] == '\x1b['
            assert data[-1] == 'c'
            return data[2:-1].split(';')
    finally:
        termios.tcsetattr(stdin_fileno, termios.TCSANOW, backup)

def main():
    import sys, os, optparse, select
    import tff
    import skk
    import canossa

    # parse options and arguments
    usage = 'usage: %prog [options] [command | - ]'
    parser = optparse.OptionParser(usage=usage)

    parser.add_option('--version', dest='version',
                      action="store_true", default=False,
                      help='show version')

    parser.add_option('-t', '--term', dest='term',
                      help='override TERM environment variable')

    parser.add_option('-l', '--lang', dest='lang',
                      help='override LANG environment variable')

    parser.add_option('-o', '--outenc', dest='enc',
                      help='set output encoding')

    (options, args) = parser.parse_args()

    if options.version:
        import __init__
        print '''

      ＼＾o＾＼ｴｯｽｶﾚｰﾀｰ

sentimental-skk %s 
Copyright (C) 2012 Hayaki Saito <user@zuse.jp>. 

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see http://www.gnu.org/licenses/.
        ''' % __init__.__version__
        return

    # retrive starting command
    if len(args) > 0:
        command = args[0]
    elif not os.getenv('SHELL') is None:
        command = os.getenv('SHELL')
    else:
        command = '/bin/sh'

    # retrive TERM setting
    if options.term:
        term = options.term
    elif not os.getenv('TERM') is None:
        term = os.getenv('TERM')
    else:
        term = 'xterm'

    # retrive LANG setting
    if not options.lang is None:
        lang = options.lang
    elif not os.getenv('LANG') is None:
        lang = os.getenv('LANG')
    else:
        import locale
        lang = '%s.%s' % locale.getdefaultlocale()

    # retrive terminal encoding setting
    if options.enc is not None:
        termenc = options.enc
    else:
        import locale
        language, encoding = locale.getdefaultlocale()
        termenc = encoding
    if termenc is None:
        raise Exception(
            'Invalid TERM environment is detected: "%s"' % termenc)

    # make skk setting
    sys.stdout.write("\x1b7")
    y, x = _getpos(sys.stdin, sys.stdout)
    sys.stdout.write("ω")
    y2, x2 = _getpos(sys.stdin, sys.stdout)
    size = x2 - x
    sys.stdout.write("\x1b8")
    sys.stdout.write("\x1b7")
    sys.stdout.write(" " * size)
    sys.stdout.write("\x1b8")
    if size == 2:
        is_cjk = True 
    else:
        is_cjk = False 
    tty = tff.DefaultPTY(term, lang, command, sys.stdin)
    row, col = tty.fitsize()
    screen = canossa.Screen(row, col, y, x, is_cjk)

    canossahandler = canossa.OutputHandler(screen, visibility=False)

    inputhandler = skk.InputHandler(screen, sys.stdout, termenc, is_cjk)

    outputhandler = skk.OutputHandler()

    use_title = True
    if not "xterm" in term:
        use_title = False

    try:
        da2 = _get_da2(sys.stdin, sys.stdout)
        if len(da2) == 3 and da2[0] == '>32' and len(da2[1]) == 3: # Tera Term
            use_title = False
    except:
        pass

    if use_title:
        multiplexer = tff.FilterMultiplexer(canossahandler, outputhandler)
    else:
        multiplexer = tff.FilterMultiplexer(canossahandler, tff.DefaultHandler())

    session = tff.Session(tty)
    session.start(termenc=termenc,
                  stdin=sys.stdin,
                  stdout=sys.stdout,
                  inputhandler=inputhandler,
                  outputhandler=multiplexer)

''' main '''
if __name__ == '__main__':    
    main()

