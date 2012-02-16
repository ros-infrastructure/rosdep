.. _python_api:

rosdep2 Python API
==================

.. module:: rosdep2

**Experimental**: the rosdep2 Python library is still unstable.

The :mod:`rosdep` Python module supports both the `rosdep`
command-line tool as well as libraries that wish to use rosdep data
files to resolve dependencies.

As a developer, you may wish to extend :mod:`rosdep` to add new OS
platforms or package managers.  Platforms are specified by registering
information on the :class:`InstallerContext`.  Package managers
generally extend the :class:`PackageManagerInstaller` implementation.

The :mod:`rospkg` library is used for OS detection.

Please consult the :ref:`Developers Guide <dev_guide>` for more
information on developing with the Python API.


.. contents:: Table of Contents
   :depth: 2

Exceptions
----------

.. autoclass:: InvalidData

Database Model
--------------

.. autoclass:: RosdepDatabase
   :members:

.. autoclass:: RosdepDatabaseEntry
   :members:

View Model
----------

.. autoclass:: RosdepDefinition
   :members:

.. autoclass:: RosdepView
   :members:

.. autoclass:: RosdepLookup
   :members:

Loaders
-------

.. autoclass:: RosdepLoader
   :members:

.. autoclass:: RosPkgLoader
   :members:

Installers
----------

.. autoclass:: InstallerContext
   :members:

.. autoclass:: Installer
   :members:

.. autoclass:: PackageManagerInstaller
   :members:

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

