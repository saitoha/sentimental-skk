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
    import skk

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
      　　／   ／
      　／^o^／ エッスカレーター
      ／　 ／

sskk %s 
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
    if options.lang:
        lang = options.term
    elif not os.getenv('LANG') is None:
        lang = os.getenv('LANG')
    else:
        import locale
        lang = '%s.%s' % locale.getdefaultlocale()

    # retrive terminal encoding setting
    if options.enc:
        termenc = options.enc
    else:
        import locale
        language, encoding = locale.getdefaultlocale()
        termenc = encoding

    # retrive skk setting
    inputhandler = skk.InputHandler(sys.stdout, termenc)
    outputhandler = skk.OutputHandler()

    inputscanner = tff.DefaultScanner()

    outputscanner = tff.DefaultScanner()

    startmessage = u'\x1b]0;sskk\x07'
    sys.stdout.write(startmessage)

    settings = tff.Settings(command=command,
                            term=term,
                            lang=lang,
                            termenc=termenc,
                            stdin=sys.stdin,
                            stdout=sys.stdout,
                            inputscanner=inputscanner,
                            inputparser=tff.DefaultParser(),
                            inputhandler=inputhandler,
                            outputscanner=outputscanner,
                            outputparser=tff.DefaultParser(),
                            outputhandler=outputhandler)
    session = tff.Session()
    session.start(settings)

    endmessage = u'\x1b]0;三 ┏( ^o^)┛ ＜ sskkを使ってくれてありがとう\x07'
    sys.stdout.write(endmessage)

''' main '''
if __name__ == '__main__':    
    main()

