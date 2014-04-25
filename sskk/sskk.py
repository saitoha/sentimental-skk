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

def _parseopt():

    import optparse

    # parse options and arguments
    usage = 'usage: %prog [options] [command | - ]'
    parser = optparse.OptionParser(usage=usage)

    parser.add_option('--version', dest='version',
                      action='store_true', default=False,
                      help='show version')

    parser.add_option('-t', '--term', dest='term',
                      help='override TERM environment variable')

    parser.add_option('-l', '--lang', dest='lang',
                      help='override LANG environment variable')

    parser.add_option('-o', '--outenc', dest='enc',
                      help='set output encoding')

    parser.add_option('-u', '--use-titlebar', dest='titlebar',
                      action='store_true', default=False,
                      help='use title bar manipulation feature')

    return parser.parse_args()


def _showversion():

    import __init__
    version = __init__.__version__

    template = """

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
        """
    print(template % version)


def _showsplash(output):

    import __init__
    from canossa import termprop

    output.write(u'\x1b[22;0t')
    output.flush()

#    output.write(u'\x1b[>2t')
    version = __init__.__version__

    output.write(u'\x1b[1;1H\x1b[J'
                 u'\x1b[5;5H'
                 u'      ＼ Sentimental-SKK %s ／\n'
                 u'\x1b[7;5H'
                 u'               三 ( ´_ゝ`）\n'
                 u'\x1b[1;1H' % version)

    termprop = termprop.Termprop()

    output.write(u'\x1b]0;\x1b\\')
    output.write(u'\x1b[22;0t')
    output.flush()

    return termprop


def _start_logging():
    import os
    import logging
    import logging.handlers

    homedir = os.path.expanduser('~')
    rcdir = os.path.join(homedir, '.sskk')

    confdir = os.path.join(rcdir, 'conf')
    if not os.path.exists(confdir):
        os.makedirs(confdir)

    logdir = os.path.join(rcdir, 'log')
    if not os.path.exists(logdir):
        os.makedirs(logdir)

    logfile = os.path.join(logdir, 'log.txt')

    import datetime
    today = datetime.datetime.today()
    timestamp = today.strftime("%Y-%m-%d %H:%M:%S")

    logging.basicConfig(filename=logfile, level=logging.DEBUG)

    # Add the log message handler to the logger
    handler = logging.handlers.RotatingFileHandler(logfile, maxBytes=100000, backupCount=100)
    logging.getLogger().addHandler(handler)

    logging.info("\n\n"
                 "-----------------------------------------------------\n"
                 "               %s\n"
                 "-----------------------------------------------------\n" % timestamp)


def _mainimpl(options, args, env_shell='', env_term='', env_lang=''):
    import sys
    import os
    import codecs
    import logging
    import __init__
    import settings
    import dictionary

    dictionary.initialize()

    # retrive starting command
    if args:
        command = args[0]
    elif env_shell:
        command = env_shell
    else:
        command = '/bin/sh'

    # retrive TERM setting
    if options.term:
        term = options.term
    elif env_term:
        term = env_term
    else:
        term = 'xterm'

    # retrive LANG setting
    if not options.lang is None:
        lang = options.lang
    elif env_lang:
        lang = env_lang
    else:
        import locale
        try:
            language, encoding = locale.getdefaultlocale()
        except ValueError, e:
            logging.exception(e)
            language = 'Ja_JP'
            encoding = 'utf-8'
        lang = '%s.%s' % (language, encoding)

    # retrive terminal encoding setting
    if options.enc:
        termenc = options.enc
    else:
        import locale
        try:
            language, encoding = locale.getdefaultlocale()
        except ValueError, e:
            logging.exception(e)
            encoding = 'utf-8'

        termenc = encoding

    if not termenc:
        termenc = 'utf-8'

    # fix for cygwin environment, such as utf_8_cjknarrow
    if termenc.lower().startswith("utf_8_"):
        termenc = "UTF-8"

    output = codecs.getwriter(termenc)(sys.stdout, errors='ignore')

    termprop = _showsplash(output)

    os.environ['__SSKK_VERSION'] = __init__.__version__
    if settings.get('use_title'):
        use_title = True
    else:
        use_title = False

    if options.titlebar:
        use_title = True

    # TODO: see terminfo
    if not 'xterm' in term:
        use_title = False
        logging.warning('use_title flag is disabled by '
                        'checking $TERM.')

    if not termprop.has_mb_title:
        use_title = False
        logging.warning('use_title flag is disabled by '
                        'checking termprop.has_mb_title.')

    import title
    title.setenabled(use_title)

    try:
        _mainloop(termenc, termprop, command, term, lang)
    except Exception, e:
        output.write(u'\x1bc')
        logging.exception(e)
        logging.exception('Aborted by exception.')
        print('sskk aborted by an uncaught exception.'
              ' see $HOME/.sskk/log/log.txt.')
    finally:
        output.write(u'\x1b[?1006l')
        output.write(u'\x1b[?1003l')
        output.write(u'\x1b[?1002l')
        output.write(u'\x1b[?1000l')
        output.write(u'\x1b]0;\x1b\\')
        output.flush()

        # pop title
        output.write(u'\x1b[23;0t')


def _mainloop(termenc, termprop, command, term, lang):

    from canossa import tff
    import sys

    tty = tff.DefaultPTY(term, lang, command, sys.stdin)
    row, col = tty.fitsize()

    session = tff.Session(tty)

    try:
        from canossa import Screen
        screen = Screen(row, col, 0, 0, termenc, termprop)

        from mode import InputMode
        from canossa import ModeHandler
        from input import InputHandler
        inputmode = InputMode(session)
        mode_handler = ModeHandler(inputmode, termprop)
        inputhandler = InputHandler(session=session,
                                    screen=screen,
                                    termenc=termenc,
                                    termprop=termprop,
                                    mousemode=mode_handler,
                                    inputmode=inputmode)

        from canossa import Canossa
        from output import OutputHandler
        canossahandler = Canossa(screen, visibility=False)
        outputhandler = OutputHandler(screen, mode_handler)

        multiplexer = tff.FilterMultiplexer(canossahandler,
                                            outputhandler)
        session.start(termenc=termenc,
                      stdin=sys.stdin,
                      stdout=sys.stdout,
                      inputhandler=inputhandler,
                      outputhandler=multiplexer)
    finally:
        tty.restore_term()


def test_terminal():
    from canossa import termprop
    termprop = termprop.test()


def main():

    import os

    if os.getenv('__SSKK_VERTION'):
        print('\n＼SSKK process is already running！！！／\n')
        print('       三 ( ´_ゝ`）三 ( ´_ゝ`）\n')
        return

    _start_logging()

    options, args = _parseopt()

    if options.version:
        _showversion()
        return

    _mainimpl(options, args,
              env_shell=os.getenv('SHELL'),
              env_term=os.getenv('TERM'),
              env_lang=os.getenv('LANG'))


''' main '''
if __name__ == '__main__':
    """
    >>> main()
    """
    main()
