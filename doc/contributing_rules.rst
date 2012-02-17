Contributing rosdep rules
=========================

In order to contribute rosdep rules, you should first make sure that
you are familiar with the :ref:`rosdep.yaml format <rosdep_yaml>`.

Fork the rosdistro GitHub repository
------------------------------------

The main rosdep database is stored in files in the "rosdistro"
repository in the "ros" project on GitHub:

`https://github.com/ros/rosdistro <https://github.com/ros/rosdistro>`_

Fork this repository to begin making your changes.

Point your sources.list.d at your forked repository
---------------------------------------------------

The default sources list for rosdep uses the following files::

    yaml https://github.com/ros/rosdistro/raw/master/rosdep/base.yaml
    yaml https://github.com/ros/rosdistro/raw/master/rosdep/python.yaml
    yaml https://github.com/ros/rosdistro/raw/master/rosdep/osx-homebrew.yaml osx
    
Create a new file in ``/etc/ros/rosdep/sources.list.d/`` that points
at your forked repository instead.  The filename should use a lower
number so it is processed first.

Make your changes to your forked repository
-------------------------------------------

The repository contains the following files:

- ``rosdep/osx-homebrew.yaml``: Rules for OS X Homebrew
- ``rosdep/python.yaml``: Python-specific dependencies
- ``rosdep/base.yaml``: Everything else

Edit the appropriate file(s) for your change. 


Make sure that your rules work
------------------------------

Update your local index::

    rosdep update

Test your new rules::

     rosdep resolve <key-name>

Test with different OS rules::

     rosdep resolve <key-name> --os=OS_NAME:OS_VERSION


Submit a pull request with your updated rules
---------------------------------------------

Use GitHub's pull request mechanism to request that your updates get
included in the main databases.

After your request has been accepted, you can undo your changes to
``/etc/ros/rosdep/sources.list.d``.
