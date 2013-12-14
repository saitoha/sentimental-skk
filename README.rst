Sentimental SKK
===============

What is this?
-------------

    This program provides Simple Kana Kanji conversion (SKK) input method service to your terminal.
    It depends on "Canossa"(https://github.com/saitoha/canossa), which is an off-screen terminal emulation service,
    "Canossa" makes application enable to restore specified screen region on demand!!
    So this SKK service can provide cool popup feature.

.. image:: http://zuse.jp/misc/canossa.png
   :width: 640

SKK Shell
---------

    You can enter SKK-shell mode by "C-j / $".

.. image:: http://zuse.jp/misc/skkshell.png
   :width: 800

When you launch console applications in SKK-shell, they run in floating windows. 
Each programs managed by "Canossa" works asyncronously in every windows.
You can resize and move each windows with mouse operations.
"Canossa" includes terminal multiplexer / task switching engine.

.. image:: http://zuse.jp/misc/windows.png
   :width: 800

Consult Wikipedia
-----------------

    You can consult Wikipedia by pressing C-w.

.. image:: http://zuse.jp/misc/sskk_wikipedia.png
   :width: 640

Settings
--------

    You can enter configuration mode by "C-j / @".

.. image:: http://zuse.jp/misc/settings.png

Requirements
------------
Python 2.5/2.6/2.7 unix/linux/cygwin version


Install
-------

via github ::

    $ git clone --recursive https://github.com/saitoha/sentimental-skk.git sentimental-skk
    $ cd sentimental-skk
    $ python setup.py install

or via pip ::

    $ pip install sentimental-skk

upgrade install via pip ::

    $ pip install sentimental-skk --upgrade

Usage
-----

::

    $ sskk [options]


* Options::

    -h, --help                  show this help message and exit
    --version                   show version
    -t TERM, --term=TERM        override TERM environment variable
    -l LANG, --lang=LANG        override LANG environment variable
    -o ENC, --outenc=ENC        set output encoding
    -u, --use-titlebar          use title bar manipulation feature

How It Works
------------
This program works as a terminal filter application and
creates some PTYs. It hooks I/O stream between terminal and applications
running on it.

The output stream which is recognized as STDOUT handle for applications,
is duplicated and processed with the terminal emulation engine called as
"Canossa". Canossa has a virtual terminal screen buffer which consists with a
couple of character cell objects, and behave as another terminal emulator.

- ::

    +---------------------------------------------+
    |                                             |
    |                  Terminal                   |
    |                                             |
    +---------------------------------------------+
           |                       ^
           |                       |
       < input >               < output >
           |                       |
           |      +----------------+
           |      |                      [ PTY 1 ]
    +------|------|-------------------------------+
    |      v      |                               |
    |  +----------+---+       +----------------+  |
    |  |    Master    |=======|      Slave     |  |
    |  +--------------+       +--+-------------+  |
    |                            |        ^       |
    +----------------------------|--------|-------+
                                 |        |
                             < input >    |
                                 |        |
                 +---------------+    < output >
                 |                        |
    [ sskk ]     |                        |               [ canossa ]
    +------------|------------------------|------------+----------------------+
    |            |                        |            |                      |
    |            |                        |<------------------------+         |
    |            v                        |            |            |         |
    |   +-----------------+     +---------+------+     |  +---------+------+  |
    |   |                 |     |                |     |  |                |  |
    |   |                 |     |                |     |  |                |  |
    |   |  InputHandler   |     |  OutputHandler |     |  |    Canossa     |  |
    |   |                 |     |                |     |  |                |  |
    |   |                 |     |                |     |  |                |  |
    |   +--------+---+----+     +----------------+     |  +----------------+  |
    |            |   |                    ^            |      ^       ^       |
    |            |   |                    |            |      |       |       |
    |            |   |                    |            |      |       |       |
    |            |   |        +-------------------+    |      |  +----+----+  |
    |            |   |        |                   |    |      |  |         |  |
    |            |   |        |  TFF Multiplexer  +-----------+  | widgets |  |
    |            |   |        |                   |    |         |         |  |
    |            |   |        +-----------+-------+    |         +---------+  |
    |            |   |                    |            |              ^       |
    |            |   |                    |            |              |       |
    |            |   +------------------------------------------------+       |
    |            |                        |            |                      |
    +------------|------------------------|------------+----------------------+
                 |                        |
             < input >                < output >
                 |                        |
                 |       +----------------+
                 |       |
                 |       | [ PTY 2 ]
         +-------|-------|-----------------------------+
         |       v       |                             |
         |  +------------+--+       +---------------+  |
         |  |    Master     |=======|     Slave     |  |
         |  +---------------+       +----+----------+  |
         |                               |      ^      |
         +-------------------------------|------|------+
                                         |      |
                    +--------------------+      |
                    |                           |
    +---------------+----------------------------------------------+
    |                                                              |
    |                        Application Process                   |
    |                                                              |
    +--------------------------------------------------------------+


Components represented by above diagram, such as InputHandler, OutputHandler,
Canossa, Multiplexer are based on TFF.

- TFF (Terminal Filter Framework)::

                        Scanner                    Event Driven Parser         Event Dispatcher
                        +-----+                         +-----+                     +-----+
      << I/O Stream >>  |     | << CodePoint Stream >>  |     | << Event Stream >>  |     |      << I/O Stream >>
    ------------------->|     |------------------------>|     |-------------------->|     |---||-------------------->
      (Raw Sequences)   |     |    (Unicode Points)     |     |   (Function Call)   |     |       (Raw Sequences)
                        +-----+                         +-----+                     +--+--+
                                                   ISO-2022 ISO-6429                   |
                                                   Compatible Parsing                  |
                                                                                       v
                                                                                    +-----+
                                                                     Event Observer |     |      << I/O Stream >>
                                                                      (I/O Handler) |     |---||-------------------->
                                                                                    |     |       (Raw Sequences)
                                                                                    +-----+

Dependency
----------
 - Masahiko Sato et al./SKK Development Team's SKK dictionaries
   http://openlab.jp/skk/skk/dic

 - Hayaki Saito's Canossa
   https://github.com/saitoha/canossa

 - Hayaki Saito's TFF, Terminal Filter Framework
   https://github.com/saitoha/tff

 - Hayaki Saito's termprop
   https://github.com/saitoha/tff

Reference
---------
 - Daredevil SKK (DDSKK) http://openlab.ring.gr.jp/skk/ddskk-ja.html
 - libfep https://github.com/ueno/libfep
 - uim https://code.google.com/p/uim/
 - uobikiemukot / yaskk https://github.com/uobikiemukot/yaskk
 - Unicode Text Editor MinEd http://towo.net/mined/

