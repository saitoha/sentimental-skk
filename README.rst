Sentimental SKK
===============

Provides Japanese Input Method SKK (Simple Kana to Kanji conversion) on your terminal.

Install
-------

via github ::

    $ git clone https://github.com/saitoha/sentimental-skk.git
    $ cd sentimental-skk
    $ python setup.py install

or via pip ::

    $ pip install sentimental-skk


Usage
-----

::

    $ sskk [options] [command | -]


* Options::

    -h, --help                  show this help message and exit
    --version                   show version
    -t TERM, --term=TERM        override TERM environment variable
    -l LANG, --lang=LANG        override LANG environment variable
    -o ENC, --outenc=ENC        set output encoding

Dependency
----------
 - Masahiko Sato et al./SKK Development Team's SKK-JISYO.L

   This package includes the large SKK dictionary, SKK-JISYO.L.
   http://openlab.jp/skk/skk/dic/SKK-JISYO.L

 - Hayaki Saito's TFF, Terminal Filter Framework
   https://github.com/saitoha/tff

Reference
---------
 - Daredevil SKK (DDSKK) http://openlab.ring.gr.jp/skk/ddskk-ja.html
 - libfep https://github.com/ueno/libfep
 - uim https://code.google.com/p/uim/
 - Unicode Text Editor MinEd http://towo.net/mined/


