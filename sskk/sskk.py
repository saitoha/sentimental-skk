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


def main():
    import sys, os, optparse, select
    import tff

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

    parser.add_option('-u', '--use-titlebar', dest='titlebar',
                      action="store_true", default=False,
                      help='use title bar manipulation feature')

    parser.add_option('-m', '--use-mouse', dest='mouse',
                      action="store_true", default=False,
                      help='use mouse selection feature')

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

    sys.stdout.write("\x1b[22;0t")
    sys.stdout.write("\x1b[22;0t")
    sys.stdout.flush()

    from termprop import Termprop
    termprop = Termprop()

    tty = tff.DefaultPTY(term, lang, command, sys.stdin)
    row, col = tty.fitsize()

    use_title = options.titlebar
    use_mouse = options.mouse

    if not "xterm" in term:
        use_title = False

    if not termprop.has_mb_title:
        use_title = False

    import title
    import mouse
    import canossa as cano

    title.setenabled(use_title)

    if use_mouse:
        mouse_mode = mouse.MouseMode()
    else:
        mouse_mode = None

    if termprop.has_cpr:
        y, x = termprop.getyx()
    else:
        sys.stdout.write("\x1b[1;1H\x1bJ")
        x, y = 1, 1

    canossa = cano.create(row=row,
                          col=col,
                          y=y - 1,
                          x=x - 1,
                          termenc=termenc,
                          termprop=termprop,
                          visibility=False)

    from input import InputHandler
    from output import OutputHandler


    sys.stdout.flush()
    sys.stdout.write("\x1b[23;0t")

    try:
        inputhandler = InputHandler(screen=canossa.screen,
                                    stdout=sys.stdout,
                                    termenc=termenc,
                                    termprop=termprop,
                                    use_title=use_title,
                                    mouse_mode=mouse_mode)

        outputhandler = OutputHandler(use_title=use_title,
                                      mouse_mode=mouse_mode)

        multiplexer = tff.FilterMultiplexer(canossa, outputhandler)

        session = tff.Session(tty)
        session.start(termenc=termenc,
                      stdin=sys.stdin,
                      stdout=sys.stdout,
                      inputhandler=inputhandler,
                      outputhandler=multiplexer)
    finally: 
        sys.stdout.flush()
        sys.stdout.write("\x1b[23;0t")
       
''' main '''
if __name__ == '__main__':    
    main()

