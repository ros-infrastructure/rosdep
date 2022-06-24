.. _dev_guide:

Developer's Guide
=================

Python API reference
--------------------

In progress, please see :ref:`Python API <python_api>`.

REP 114: rospkg standalone library
----------------------------------

The rosdep library is being developed using the ROS REP process.  It
is necessary to be familiar with these REPs in order to make sure
that rosdep continues to follow the relevant specifications.

- `REP 111: Multiple Package Manager Support for Rosdep <http://ros.org/reps/rep-0111.html>`_.
- `REP 112: Source Package Manager for Rosdep <http://ros.org/reps/rep-0112.html>`_.
- `REP 125: rosdep 2 <http://ros.org/reps/rep-0125.html>`_.

Bug reports and feature requests
--------------------------------

- `Submit a bug report <https://code.ros.org/trac/ros/newticket?component=rospkg&type=defect&&rospkg>`_
- `Submit a feature request <https://code.ros.org/trac/ros/newticket?component=rospkg&type=enhancement&rospkg>`_

Getting the code
----------------

The rosdep codebase is hosted on GitHub.  To get started contributing patches, please create a fork:

https://github.com/ros-infrastructure/rosdep

Supporting a new OS/package manager
-----------------------------------

Adding new platforms to rosdep can be separated into two steps: adding
support for a new package manager, and adding support for a new OS.

NOTE: There are numerous examples in :mod:`rosdep2.platforms` that you
can follow.

Declaring a new OS
''''''''''''''''''

Adding support for a new OS is fairly straightforward: you just
have to provide rosdep2 the keys that are associated with your OS and the
keys of the installers that your OS supports.

Implementations must provide a ``register_platforms(context)`` call
which sets up the keys used for the OS and package managers.  The
registration only sets up associated keys -- it does not specify the
implementation.  OS keys should be pulled from ``rospkg.os_detect`` if
they are available.

This example registers the ``gentoo`` OS and adds support for the
``equery`` and ``source`` package managers.  It then sets the default
package manager to ``equery``::

    from rospkg.os_detect import OS_GENTOO
    def register_platforms(context):
        context.add_os_installer_key(OS_GENTOO, EQUERY_INSTALLER)
        context.add_os_installer_key(OS_GENTOO, SOURCE_INSTALLER)
        context.set_default_os_installer_key(OS_GENTOO, EQUERY_INSTALLER)

Declaring a new installer
'''''''''''''''''''''''''

A new installer is registered with the system using a
``register_installers(context)`` call.  This call aqssociates the
installer key with an implementation.

This example declares that ``pip`` is implemented using the
``PipInstaller()`` class.  We also declare the ``PIP_INSTALLER``
variable so that other code can use it symbolically.::

    PIP_INSTALLER = 'pip'
    def register_installers(context):
        context.set_installer(PIP_INSTALLER, PipInstaller())

Most installers are implemented using the the
:class:`PackageManagerInstaller` API.  The following is the implementation
of the ``PipInstaller``::

    class PipInstaller(PackageManagerInstaller):

        def __init__(self):
            super(PipInstaller, self).__init__(pip_detect, supports_depends=True)

        def get_install_command(self, resolved, interactive=True, reinstall=False):
            if not is_pip_installed():
                raise InstallFailed((PIP_INSTALLER, "pip is not installed"))
            # convenience function that calls outs to our detect function
            packages = self.get_packages_to_install(resolved, reinstall=reinstall)
            if not packages:
                return []
            else:
                return [['sudo', 'pip', 'install', '-U', p] for p in packages]


The pattern is fairly simple to implement for other package managers.
You must provide a ``detect_function(package_names)``
(e.g. ``pip_detect()``) that returns a list of package names that are
already installed.  You must also implement ``get_install_command()``
which must return a *list* of commands to execute in order to install
the relevant packages.


Testing
-------

If you contribute a support for a new OS/package manager, you *must*
provide complete unit test coverage.  For example, if your detector
relies on parsing the output of a package manager, you must submit
example output along with tests that parse them correctly.

Test files for os detection should be placed in ``test/os_name``.

Setup

::

    pip install pytest
    pip install mock


rosdep2 uses `pytest <http://docs.pytest.org>`_
for testing, which is a fairly simple and straightfoward test
framework.  You just have to write a function start with the name
``test`` and use normal ``assert`` statements for your tests.

rosdep2 also uses `mock <http://www.voidspace.org.uk/python/mock/>`_ to
create mocks for testing on Python versions prior to 3.3.

You can run the tests, including coverage, as follows:

::

    cd rosdep2/test
    pytest


Documentation
-------------

Sphinx is used to provide API documentation for rospkg.  The documents
are stored in the ``doc`` subdirectory.

In order to build the docs, you need the 'ros-theme', which should be stored
in `~/sphinx/ros-theme`.  You can get a copy of ros-theme from:

https://github.com/ros-infrastructure/catkin-sphinx/tree/master/src/catkin_sphinx/theme
