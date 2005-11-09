=============================================
seppo - simple embarrassingly parallel python
=============================================

.. contents::

Overview
--------

The ``map`` function is well-known in Python, allowing a single
function to be called on each member of an iterable sequence::

  map( function, [1,2,3,4] )

The seppo_ module allows the same functionality, but distributed over
several processes::

  seppo.map_parallel( some_module.function, [1,2,3,4] )

In this case, each iteration may evaluate the function in a different
process, possibly in a different computer.  The idea is a simple
concept and is hopefully natural transition for Python programmers to
use the power of multi-processor computers and clusters.

Currently, seppo is based on Pyro_ mobile code and is subject to the
same caveats. To understand these issues, please read about `Pyro
mobile code`_.

.. _seppo: http://www.its.caltech.edu/~astraw/seppo.html
.. _Pyro: http://pyro.sourceforge.net/
.. _`Pyro mobile code`: http://pyro.sourceforge.net/manual/7-features.html#mobile

An example
----------

The following example is included with seppo.

The main program (``simple.py``)::

  import seppo
  import example_module

  results = seppo.map_parallel(example_module.hello_world, [1,2,3,4,5])

  for result in results:
      print result

Here is the function that does the work. Note, this function must be
in a separate module, due to a limitation of `Pyro mobile
code`_. (``example_module.py``)::

  import socket, os

  def hello_world( value ):
      value2 = value*value
      fqdn = socket.getfqdn()
      pid = os.getpid()
      host_str = "%s, process %d"%(fqdn,pid)
      result = 'hello world from %s (input=%f, value*value=%f)'%(host_str,value,value2)
      return result

And to start a server (``serv_a_process.py``)::

  import seppo
  seppo.start_seppo_enslaved_server()

The sequence to run this example:

 * Start a Pyro_ name server
 * Run the server(s) (``python serv_a_process.py``)
 * Run the client (``python simple.py``)

The above should produce output something like the following if there
are 2 servers running::

  $ python simple.py

  hello world from host1, process 23759 (input=1.000000, value*value=1.000000)
  hello world from host1, process 23759 (input=2.000000, value*value=4.000000)
  hello world from host1, process 23759 (input=3.000000, value*value=9.000000)
  hello world from host2, process 9832 (input=4.000000, value*value=16.000000)
  hello world from host2, process 9832 (input=5.000000, value*value=25.000000)


Warning - run only on a secure network
--------------------------------------

Because seppo works by allowing arbitrary Python code on your machine
via an open network port, **you must make absolutely sure your network
is secure**. Seppo does absolutely nothing in terms of security.

Download
--------

Grab it from the `download directory`_.

.. _`download directory`: http://www.its.caltech.edu/~astraw/seppo-download/

There is an `online changelog`_ and CHANGELOG.txt in the source
distribution describing each release.

.. _`online changelog`: http://www.its.caltech.edu/~astraw/seppo-changes.html

Seppo works as described above, but hasn't yet seen much use.  This
should be considered a very alpha version, and was released to the
public to gauge interest/reaction.

License
-------

BSD license. See the file LICENSE.txt distributed with the source code.

Copyright owner and author: `Andrew Straw`_

.. _`Andrew Straw`: http://www.its.caltech.edu/~astraw