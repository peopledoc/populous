Populous - *populate your database with god-like powers*
========================================================

Populous is a tool for fast and rich data generation. From a description
of your schema say how many objects you want, what they should look
like, and populous will create them for you!

Current state
-------------

The project is in a very early stage and proof-of-concept state. Please
be patient, but don't hesitate to share your thoughts and desires with
us in the issues.

Documentation
-------------

**Sorry, but the documentation is not ready yet :( .**

However, if you are very eager to try it, here is what you can do:

-  Install populous: ``pip install populous``
-  Have a PostgreSQL database at hand
-  Find some blueprints (YAML files describing what you want to
   generate) or create some. This is the tricky part, but you can find
   some examples in the ``demo/blueprints/`` directory.
-  Launch populous with those blueprints:
   ``populous run postgres demo/blueprints/*.yml`` (you can pass your
   postgres instance either via ``PG*`` environment variables or via
   arguments)
-  Gaze at your freshly generated data via ``psql`` or any other tool!

Troubleshooting
---------------

OSX compilation problems
~~~~~~~~~~~~~~~~~~~~~~~~

There's currently no pre-compiled package for the
``peloton_bloomfilters`` library, which is a current requirement for
populous. To correctly install it in your environment, you're going to:

-  install ``gcc`` (via homebrew, for example),
-  install the package using the following flags
   ``ARCHFLAGS="-arch x86_64" CC=/usr/bin/gcc``.

For example, to install locally:

::

    ARCHFLAGS="-arch x86_64" CC=/usr/bin/gcc pip install peloton_bloomfilters

Or if you want to run the test suite via tox:

::

    ARCHFLAGS="-arch x86_64" CC=/usr/bin/gcc tox
