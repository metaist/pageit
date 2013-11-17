pageit: a static html generator |build-status|
==============================================
.. |build-status| image:: https://secure.travis-ci.org/metaist/pageit.png
   :target: http://travis-ci.org/metaist/pageit

pageit is a python tool for generating static website using `Mako Templates`_
similar to Jekyll_ and Hyde_.

.. _Mako Templates: http://www.makotemplates.org
.. _Jekyll: https://github.com/mojombo/jekyll
.. _Hyde: https://github.com/lakshmivyas/hyde

Quick Links
-----------
* Code_ & Issues_ (GitHub)
* Documentation_ (Read the Docs)
* Package_ (PyPI)

.. _code: https://github.com/metaist/pageit
.. _issues: https://github.com/metaist/pageit/issues
.. _documentation: http://pageit.readthedocs.org
.. _package: http://pypi.python.org/pypi/pageit

Getting Started
---------------
1. Install the package:

.. code-block:: bash

    $ pip install pageit

2. Create a directory called `site` where you will put your html files:

.. code-block:: bash

    $ mkdir site
    $ cd site

3. Run ``pageit`` to generate the html files:

.. code-block:: bash

    $ pageit


* Directories with names that end with ``.mako`` will be ignored. This is
  a good way to prevent your mako layouts from getting rendered.

* Files that end with ``.mako`` will be rendered using ``mako``; the
  generated file will have the ``.mako`` extension removed.

Contribute
----------
If you want to play around with the latest code, start by cloning
the repository, installing the dependencies, and building using Paver_:

.. code-block:: bash

    $ git clone git://github.com/metaist/pageit.git
    $ pip install -r requirements.txt --use-mirrors
    $ paver test

.. _Paver: https://github.com/paver/paver

License
-------
Licensed under the `MIT License`_.

.. _MIT License: http://opensource.org/licenses/MIT
