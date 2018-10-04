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

Updating rosdep
---------------

You can update your rosdep database by running::

    rosdep update


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



For more information, please see the :ref:`command reference <rosdep_usage>`.

