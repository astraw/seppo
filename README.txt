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

  seppo.map_parallel( function, [1,2,3,4] )

In this case, each iteration may evaluate the function in a different
process, possibly in a different computer.  The idea is a simple
concept and is hopefully natural transition for Python programmers to
use the power of multi-processor computers and clusters.

.. _seppo: http://www.its.caltech.edu/~astraw/seppo.html

An example
----------

The following example is included with seppo.

The main program (``simple.py``)::

  import seppo
  import example_module

  results = seppo.map_parallel(example_module.hello_world, [1,2,3,4,5],debug=1)
  print 'results:',results

The function that does the work (``example_module.py``)::

  def hello_world( value ):
      result = value*value
      print 'hello world (input %f, output %f)'%(value,result)
      return result

And to start a server (``serv_a_process.py``)::

  import seppo
  seppo.start_seppo_enslaved_server(debug=1)

The sequence to run this example:

 * Start a Pyro_ name server
 * Run the server(s) (``python serv_a_process.py``)
 * Run the client (``python simple.py``)

Download
--------

Grab it from the `download directory`_.

.. _`download directory`: http://www.its.caltech.edu/~astraw/seppo

Under the hood
--------------

seppo is currently based on the mobile code part of the networking
library Pyro_, (Python Remote Objects).

.. _Pyro: http://pyro.sourceforge.net/

Status
------

Seppo works as described above, but hasn't yet seen much use.
Anything could happen.

Release 20051107
````````````````

First public release. Basic functionality works.


License
-------

BSD license. See the file LICENSE.txt distributed with the source code.

Copyright owner and author: `Andrew Straw`_

.. _`Andrew Straw`: http://www.its.caltech.edu/~astraw