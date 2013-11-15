Script API
==========
It's easy to include :py:class:`~pageit.pageit.Pageit` in your own scripts:

.. code-block:: python

    from pageit.pageit import Pageit
    def main():
        Pageit(path='.').clean().run()

Watching for File Changes
-------------------------
Use the :py:class:`~pageit.pageit.Watcher` (based on `watchdog`_) to call a
callback function when files change:

.. code-block:: python

    from pageit.pageit import Watcher
    def my_func(path):
        print path, 'has changed'

    with Watcher(path='.', callback=my_func) as watcher:
        watcher.loop()  # wait for CTRL+C

.. _watchdog: http://pythonhosted.org/watchdog/

Basic HTTP Server
-----------------
pageit uses the `SimpleHTTPServer`_ to serve up files on a given port:

.. code-block:: python

    from pageit import pageit
    pageit.serve(path='.', port=80)  # will wait until CTRL+C

.. _SimpleHTTPServer: http://docs.python.org/2/library/simplehttpserver.html

Watching & Serving
------------------
If you want to watch and serve a path:

.. code-block:: python

    from pageit.pageit import Watcher, serve
    with Watcher(path, callback) as watcher:
        serve(path, port)  # wait for CTRL+C

Python Modules
--------------
.. toctree::
  :maxdepth: 2

  api-pageit
  api-lib
