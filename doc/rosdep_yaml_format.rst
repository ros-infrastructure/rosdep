.. _rosdep_yaml:

rosdep YAML format
''''''''''''''''''

The current rosdep YAML format specification was introduced in `REP 111 <http://ros.org/reps/rep-0111.html>`_.  


Specification
=============

rosdep supports both a *simple* and *versioned* syntax.


 * Simple 
    ::

        ROSDEP_NAME:
          OS_NAME1: 
            PACKAGE_MANAGER1:
              PACKAGE_ARGUMENTS_A
          OS_NAME2: 
            PACKAGE_MANAGER2:
              PACKAGE_ARGUMENTS_A

 * Versioned
    ::

        ROSDEP_NAME:
          OS_NAME1:
            OS_VERSION1:  
              PACKAGE_MANAGER1:
                PACKAGE_ARGUMENTS_A
            OS_VERSION2:  
              PACKAGE_MANAGER2:
                PACKAGE_ARGUMENTS_A2

The names above resolve as follows:

 * ``ROSDEP_NAME`` is the name referred to by manifest files. Examples: ``log4cxx`` or ``gtest``.
 * ``OS_NAME`` is the name of an OS.  Examples: ``ubuntu``, ``osx``, ``fedora``, ``debian``, ``openembedded``, or ``windows``.
 * ``OS_VERSION`` (*optional*) is the name of specific versions in the OS. Examples: ``lucid`` or ``squeeze``. If no ``OS_VERSION`` is specified, the rule is assumed to apply to all versions.
 * ``PACKAGE_MANAGER`` (*optional in ROS Electric, required in ROS Fuerte*) is a key to select which package manager to use for this rosdep.  Examples: ``apt``, ``pip``, ``macports``.  
 * ``PACKAGE_ARGUMENT`` is free-form YAML that is be passed to the handler for the specified ``PACKAGE_MANAGER``.


Example
-------

For Ubuntu the default package manager is apt.  An example for the simple syntax is:

::
    
    rosdep_name:
      ubuntu: 
        apt:
          packages: [ debian-package-name, other-debian-package-name]

or versioned as follows: 

::
    
    rosdep_name:
      ubuntu: 
        lucid:
          apt:
            packages: [debian-package-name, other-debian-package-name]
    

OS name identifiers and supported package managers
--------------------------------------------------

 * ``arch``: Arch Linux

   * ``pacman`` (default)
   * ``source``

 * ``cygwin``: Cygwin 

   * ``apt-cyg``
   * ``source``

 * ``debian``: Debian GNU/Linux

   * ``apt`` (default)
   * ``source``

 * ``fedora``: Fedora Project

   * ``dnf`` (default)
   * ``yum``
   * ``source``

 * ``freebsd``: FreeBSD

   * ``pkg_add`` (default)
   * ``source``
   
 * ``gentoo``: Gentoo Linux

   * ``portage`` (default)
   * ``source``

 * ``openembedded`` : OpenEmbedded

   * TODO: define a remote installation method for cross compiled packages

 * ``osx`` : Apple OS X

   * TODO: special notes on macports vs. homebrew

 * ``opensuse``: OpenSUSE

   * ``zypper`` (default)
   * ``source``

 * ``rhel`` : Red Hat Enterprise Linux

   * ``yum`` (default)
   * ``source``

 * ``ubuntu``: Ubuntu

   * ``apt`` (default)
   * ``pip``
   * ``source``

For backwards compatibility, ``macports`` is supported as an alias of ``osx``.

OS version identifiers
----------------------

OS version identifiers use one-word codenames that refer to particular releases.

Examples:

 * debian: ``squeeze``
 * ubuntu: ``lucid``, ``maverick``, ``natty``, ``oneiric``, ``precise``
 * osx: ``snow``, ``lion``



Disambiguation of OS_VERSION and PACKAGE_MANAGER
------------------------------------------------

For backwards compatibility, the ``PACKAGE_MANAGER`` is allowed to be
optional in the ROS Electric case.  As both ``PACKAGE_MANAGER`` and
``OS_VERSION`` are optional, this creates an ambiguious case where
either ``OS_VERSION`` or ``PACKAGE_MANAGER`` is specified, but not
both.  

In this ambiguous case, rosdep first interprets the key as a
``PACKAGE_MANAGER``.  If this test fails, it will be interpreted as an
``OS_VERSION``.  Developers should exercise caution in keeping
``OS_VERSION`` and ``PACKAGE_MANAGER`` keys globally distinct.
