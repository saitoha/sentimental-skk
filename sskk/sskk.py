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


def main():
    import sys
    import os
    import optparse
    import codecs
    import logging
    import __init__

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

    (options, args) = parser.parse_args()

    if options.version:
        print '''

      三o-( ^o^)-o-( ^o^)-o-( ^o^)-o

sentimental-skk %s
Copyright (C) 2012-2013 Hayaki Saito <user@zuse.jp>.

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

    if os.getenv("__SSKK_VERTION"):
        print "\n＼SSKK process is already running！！！／\n"
        print "       三 -( ^o^)-  三 -( ^o^)-\n"
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

    output = codecs.getwriter(termenc)(sys.stdout, errors='ignore')
    output.write(u"\x1b[22;0t")
    output.flush()

#    output.write(u"\x1b[>2t")
    output.write(u"\x1b[1;1H\x1b[J")
    output.write(u"\x1b[5;5H")
    output.write(u"      ＼ Sentimental-SKK %s ／\n" % __init__.__version__)
    output.write(u"\x1b[7;5H")
    output.write(u"       三( ^o^) 三( ^o^) 三( ^o^)\n")
    output.write(u"\x1b[1;1H")

    from canossa import termprop
    termprop = termprop.Termprop()

    output.write(u"\x1b]0;\x1b\\")
    output.write(u"\x1b[22;0t")
    output.flush()

    homedir = os.path.expanduser("~")
    rcdir = os.path.join(homedir, ".sskk")

    confdir = os.path.join(rcdir, "conf")
    if not os.path.exists(confdir):
        os.makedirs(confdir)

    logdir = os.path.join(rcdir, "log")
    if not os.path.exists(logdir):
        os.makedirs(logdir)

    logfile = os.path.join(logdir, "log.txt")
    logging.basicConfig(filename=logfile, filemode="w")

    os.environ["__SSKK_VERTION"] = __init__.__version__

    from canossa import tff
    tty = tff.DefaultPTY(term, lang, command, sys.stdin)

    row, col = tty.fitsize()

    import settings
    if settings.get("use_title"):
        use_title = True
    else:
        use_title = False

    if options.titlebar:
        use_title = True

    # TODO: see terminfo
    if not "xterm" in term:
        use_title = False
        logging.warning("use_title flag is disabled by checking $TERM.")

    if not termprop.has_mb_title:
        use_title = False
        logging.warning("use_title flag is disabled by checking termprop.has_mb_title.")

    import title
    import canossa as cano

    title.setenabled(use_title)

    canossa = cano.create(row=row, col=col, y=0, x=0,
                          termenc=termenc,
                          termprop=termprop,
                          visibility=False)

    from input import InputHandler

    output.flush()

    # push title
    output.write(u"\x1b[23;0t")

    output.write(u"\x1b[1;1H\x1b[J")

    session = tff.Session(tty)

    try:
        from mode import InputMode
        inputmode = InputMode(tty)
        mode_handler = cano.ModeHandler(inputmode, termprop)
        inputhandler = InputHandler(session=session,
                                    screen=canossa.screen,
                                    termenc=termenc,
                                    termprop=termprop,
                                    mousemode=mode_handler,
                                    inputmode=inputmode)

        multiplexer = tff.FilterMultiplexer(canossa, tff.DefaultHandler())
        session.start(termenc=termenc,
                      stdin=sys.stdin,
                      stdout=sys.stdout,
                      inputhandler=inputhandler,
                      outputhandler=multiplexer)
    except:
        output.write(u"\x1b[?1006l")
        output.write(u"\x1b[?1003l")
        output.write(u"\x1b[?1002l")
        output.write(u"\x1b[?1000l")
        logging.exception("Aborted by exception.")
        print ("sskk aborted by an uncaught exception."
               " see $HOME/.sskk/log/log.txt.")
    finally:
        tty.restore_term()
        output.write(u"\x1b]0;\x1b\\")
        output.flush()

        # pop title
        output.write(u"\x1b[23;0t")

''' main '''
if __name__ == '__main__':
    main()
