Overview
========

Installing rosdep
-----------------

rosdep2 is available using pip or easy_install::

    sudo pip install -U rosdep

or::

    sudo easy_install -U rosdep rospkg



Setting up rosdep
-----------------

rosdep needs to be initialized and updated to use::

    sudo rosdep init
    rosdep update

``sudo rosdep init`` will create a `sources list <sources_list>`_
directory in ``/etc/ros/rosdep/sources.list.d`` that controls where
rosdep gets its data from.

``rosdep update`` reads through this sources list to initialize your
local database.

You can override the location by setting environment variable
``ROSDEP_SOURCE_PATH``. The custom path has to exist prior to calling
``rosdep init``, otherwise the default one will be used.

Please note that when using ``sudo``, environment
variables from the user are not passed to the command. To specify the variable
for initializing the database, call::

    sudo mkdir -p /usr/rosdep.sources
    sudo env ROSDEP_SOURCE_PATH=/usr/rosdep.sources rosdep init

Updating rosdep
---------------

You can update your rosdep database by running::

    rosdep update

If you have specified a custom ``ROSDEP_SOURCE_PATH``, do not forget to set it
also for this command.

Default location of the local rosdep database is in ``$HOME/.ros/rosdep``.
To change it, set environment variable ``ROSDEP_CACHE_PATH``, or pass
command-line arguments ``--sources-cache-dir`` and ``--meta-cache-dir``.

Installating rosdeps
--------------------

rosdep takes in the name of a ROS stack or package that you wish to
install the system dependencies for.

Common installation workflow::

    $ rosdep check ros_comm
    All system dependencies have been satisfied
    $ rosdep install geometry

If you're worried about ``rosdep install`` bringing in system
dependencies you don't want, you can run ``rosdep install -s <args>``
instead to "simulate" the installation.  You will be able to see the
commands that rosdep would have run.

Example::

    $ rosdep install -s ros_comm
    #[apt] Installation commands:
      sudo apt-get install libapr1-dev
      sudo apt-get install libaprutil1-dev
      sudo apt-get install libbz2-dev
      sudo apt-get install liblog4cxx10-dev
      sudo apt-get install pkg-config
      sudo apt-get install python-imaging
      sudo apt-get install python-numpy
      sudo apt-get install python-paramiko
      sudo apt-get install python-yaml

You can also query rosdep to find out more information about specific
dependencies::

    $ rosdep keys roscpp
    pkg-config

    $ rosdep resolve pkg-config
    pkg-config

    $ rosdep keys geometry
    eigen
    apr
    glut
    python-sip
    python-numpy
    graphviz
    paramiko
    cppunit
    libxext
    log4cxx
    pkg-config

    $ rosdep resolve eigen
    libeigen3-dev



If you specified a custom ``ROSDEP_CACHE_PATH`` or used command-line arguments
``--sources-cache-dir`` and ``--meta-cache-dir``, you have to pass these to
all rosdep commands used afterwards, including ``rosdep install``.

For more information, please see the :ref:`command reference <rosdep_usage>`.

