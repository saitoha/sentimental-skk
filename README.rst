Sentimental SKK
===============

What is this?
-------------

    This program provides Simple Kana Kanji conversion (SKK) input method service to your terminal.
    It depends on Canossa(https://github.com/saitoha/canossa), which is an off-screen terminal emulation service,
    Canossa makes application enable to restore specified screen region on demand!!
    So this SKK service can provide cool popup feature.

.. image:: http://zuse.jp/misc/canossa.png 
   :width: 640


Install
-------

via github ::

    $ git clone --recursive https://github.com/saitoha/sentimental-skk.git sentimental-skk
    $ cd sentimental-skk
    $ python setup.py install

or via pip ::

    $ pip install sentimental-skk


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

- PTY and Normal Terminal/Application::

       +---------------------------------------------+                           
       |                  Terminal                   |                           
       +---------+-----------------------------------+                           
                 |                                    
       +---------|-----------------------------------+
       |  +------+-------+        +---------------+  |
       |  |    Master    |========|     Slave     |  |
       |  +--------------+        +-------+-------+  |
       +----------------------------------|----------+
                                          |           
       +----------------------------------+----------+ 
       |                Application                  |
       +---------------------------------------------+


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
- sskk ::

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
    [ sskk ]     |                        |                        
    +------------|------------------------|---------------+        
    |            |                        |               |        
    |            |                        |<--------------------------+
    |            |                        |               |           |
    |            v                        |               |           |
    |   +-----------------+       +-------+--------+      |    +------+------+
    |   |                 |       |                |      |    |             |
    |   |                 |       |                |      |    |             |
    |   |  InputHandler   |       |  OutputHandler |      |    |   Canossa   |
    |   |                 |       |                |      |    |             |
    |   |                 |       |                |      |    |             |
    |   +--------+--------+       +----------------+      |    +-------------+
    |            |                        ^               |           ^
    |            |                        |               |           |
    |            |                        |               |           |
    |            |              +-------------------+     |           |
    |            |              |                   |     |           |
    |            |              |  TFF Multiplexer  +-----------------+
    |            |              |                   |     |        
    |            |              +---------+---------+     |        
    |            |                        |               |
    +------------|------------------------|---------------+
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
                < input >                   < output > 
                    |                           |
                    v                           |
   +----------------+---------------------------------------------+
   |                                                              |
   |                        Application Process                   |
   |                                                              |
   +--------------------------------------------------------------+
 

Dependency
----------
 - Masahiko Sato et al./SKK Development Team's SKK-JISYO.L

   This package includes the large SKK dictionary, SKK-JISYO.L.
   http://openlab.jp/skk/skk/dic/SKK-JISYO.L

 - wcwidth.py
   https://svn.wso2.org/repos/wso2/carbon/platform/trunk/dependencies/cassandra/pylib/cqlshlib/wcwidth.py
   (Licensed under Apache License 2.0)

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
 - Unicode Text Editor MinEd http://towo.net/mined/


