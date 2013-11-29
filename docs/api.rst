Script API v |version|
======================

Cleaning & Rendering
--------------------
It's easy to include :py:class:`~pageit.render.Pageit` in your own scripts:

.. code-block:: python

    from pageit.render import Pageit
    Pageit(path='.').clean().run()

Watching for File Changes
-------------------------
Use :py:func:`~pageit.tools.watch` to call a
callback function when files change:

.. code-block:: python

    from pageit.tools import watch
    def my_func(path):
        print path, 'has changed'

    with watch(path='.', callback=my_func) as watcher:
        watcher.loop()  # wait for CTRL+C

.. seealso:: `watchdog`_ for the cross-platform directory-watching library

.. _watchdog: http://pythonhosted.org/watchdog/

Basic HTTP Server
-----------------
Use :py:func:`~pageit.tools.serve` to serve up files on a given port:

.. code-block:: python

    from pageit.tools import serve
    serve(path='.', port=80)  # will wait until CTRL+C

.. seealso:: Python's built-in `SimpleHTTPServer`_ for serving directories

.. _SimpleHTTPServer: http://docs.python.org/2/library/simplehttpserver.html

Watching & Serving
------------------
If you want to watch and serve a path:

.. code-block:: python

    from pageit.tools import watch, serve
    with watch(path, callback) as watcher:
        serve(path, port)  # wait for CTRL+C

Python Modules
--------------
.. toctree::
  :maxdepth: 2

  api/render
  api/tools
  api/namespace
