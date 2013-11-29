Running pageit
==============

pageit is designed for developers who need to quickly generate a standalone
static website. There are several command-line options that may be useful
for development.

Basic Example
-------------
The most common thing you want pageit to do is to process the files in the
current directory:

.. code-block:: bash

    $ pageit

Sometimes you want to run pageit on a different directory:

.. code-block:: bash

    $ pageit some/other/path

Most often, you'll want to run pageit, have it automatically re-run when
files change, and serve it out for testing:

.. code-block:: bash

    $ pageit --watch --serve


Command-Line Options
--------------------
All command-line options are optional and default to ``False`` or ignored
unless inidicated otherwise.

``-n``, ``--dry-run``
    Do not perform destructive operations such as generating output or deleting
    files.
``-c``, ``--clean``
    Remove generated output. See: :py:meth:`~pageit.render.Pageit.clean`
``-r``, ``--render``
    Render templates after a ``--clean`` operation.
``-w``, ``--watch``
    Watch the path using watchdog_ and re-run pageit when files change.
    See: :py:func:`~pageit.tools.watch`
``-s [PORT=80]``, ``--serve [PORT=80]``
    Serve the path using the SimpleHTTPServer_. This is not recommended for
    production environments.
    See: :py:func:`~pageit.tools.serve`
``-f PATH``, ``--config PATH``
    Path to YAML configuration file (default: ``pageit.yml``) containing a
    dictionary of environment names mapped to environment values (key/value
    pairs). The environment values are passed to ``mako`` templates during
    rendering via the special ``site`` variable. The configuration file is
    first searched for in the current working directory and then in the
    ``pageit`` directory.
.. versionadded:: 0.2.1
``-e``, ``--env``
    Name of the configuration environment to load (default: ``default). The
    special ``default`` environment values are always loaded first and then
    extended with the values from the environment named by ``--env``.
.. versionadded:: 0.2.1
``--tmp``
    Directory in which to store generated ``mako`` templates. By default,
    generated templates are not stored.
``--ignore-mtime``
    Render all the templates rather than only those that have changed (or
    whose dependencies have changed). For templates that have complicated
    inheritance rules, this flag may have to be set to get templates to render.
    See: :py:meth:`~pageit.render.Pageit.mako_mtime`
``--noerr``
    Do not alter the template output to be an HTML error page if an error
    arises during rendering.
``--ext``
    Extension for mako templates (default: ``.mako``). Directory names ending
    with this string be ignored.

.. _watchdog: http://pythonhosted.org/watchdog/
.. _SimpleHTTPServer: http://docs.python.org/2/library/simplehttpserver.html
