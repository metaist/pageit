pageit: a static html generator |build-status|
==============================================
.. |build-status| image:: https://secure.travis-ci.org/metaist/pageit.png
   :target: http://travis-ci.org/metaist/pageit

pageit is a python tool for generating static website using `Mako Templates`_
similar to `Jekyll`_ and `Hyde`_.

.. _Mako Templates: http://www.makotemplates.org
.. _Jekyll: https://github.com/mojombo/jekyll
.. _Hyde: https://github.com/lakshmivyas/hyde

Quick Links
-----------
* `Code`_ & `Issues`_ (GitHub)
* `Documentation`_ (Read the Docs)
* `Package`_ (PyPI)

.. _code: https://github.com/metaist/pageit
.. _issues: https://github.com/metaist/pageit/issues
.. _documentation: http://pageit.readthedocs.org
.. _package: http://pypi.python.org/pypi/pageit

Getting Started
---------------
1. Install the package::

    $ pip install pageit

2. Create a directory called `site` where you will put your html files::

    $ mkdir site

3. Run pageit above `site` to copy the files into the `output` directory::

    $ pageit

   pageit will iterate over the `site` directory and copy files into `output`
   following these basic rules:

    * Directories with names that start with `mako.` will be ignored. This is
      handy for storing your base layouts in a directory like `mako.layouts`.
    * Files that start with `mako.` will be rendered using `mako`; the
      generated file will have the `mako.` prefixed removed.
    * All other files will be copied exactly.

Contribute
----------
If you want to play around with the latest code, start by cloning
the repository, installing the dependencies, and building using `Paver`_::

    $ git clone git://github.com/metaist/pageit.git
    $ pip install -r requirements.txt --use-mirrors
    $ paver test

.. _Paver: https://github.com/paver/paver

License
-------
Licensed under the `MIT License`_.

.. _MIT License: http://opensource.org/licenses/MIT
