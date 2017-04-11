Contributing rosdep rules
=========================

In order to contribute rosdep rules, you should first make sure that
you are familiar with the :ref:`rosdep.yaml format <rosdep_yaml>`.


Summary
'''''''

There are several steps to contributing rosdep rules.  You will create
a copy of the database on GitHub, point your own rosdep to use it,
make some changes, and then ask that they be included back in the main
database.

In short:

 1. Fork https://github.com/ros/rosdistro
 2. Update your ``/etc/ros/rosdep/sources.list.d`` to use this fork
 3. Modify your fork to have new rules
 4. Test your changes
 5. Send a pull request to have your changes included in the main database

Fork the rosdistro GitHub repository
------------------------------------

The main rosdep database is stored in files in the "rosdistro"
repository in the "ros" project on GitHub:

`https://github.com/ros/rosdistro <https://github.com/ros/rosdistro>`_

Start by forking this repository so you have your own copy of the
database to work with.  Next, you'll point your local rosdep to use
this database instead.

Point your sources.list.d at your forked repository
---------------------------------------------------

The default sources list for rosdep uses the following files::

    yaml https://github.com/ros/rosdistro/raw/master/rosdep/base.yaml
    yaml https://github.com/ros/rosdistro/raw/master/rosdep/python.yaml
    yaml https://github.com/ros/rosdistro/raw/master/rosdep/osx-homebrew.yaml osx

Create a new file in ``/etc/ros/rosdep/sources.list.d/`` that points
at your forked repository instead.  The filename should use a lower
number so it is processed first.

Now that your rosdep is using the new database, you're ready to make
and test your changes.

Make your changes to your forked repository
-------------------------------------------

The repository contains the following files:

- ``rosdep/osx-homebrew.yaml``: Rules for OS X Homebrew
- ``rosdep/python.yaml``: Python-specific dependencies
- ``rosdep/base.yaml``: Everything else

Edit the appropriate file(s) for your change, i.e., if you are
contributing a Homebrew rule, only edit ``osx-homebrew.yaml``, if you
are contributing a rule for a Python library, only edit
``python.yaml``, and, otherwise, put your rule in ``base.yaml``. 
To edit, change the ``https://`` url to a local path using the format 
``file:///abs/path``.

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

There are guidelines for submitting pull requests at: https://github.com/ros/rosdistro/blob/master/CONTRIBUTING.md
And include instructions how to prevalidate your changes using the unit tests.

After your request has been accepted, you can undo your changes to
``/etc/ros/rosdep/sources.list.d``.
