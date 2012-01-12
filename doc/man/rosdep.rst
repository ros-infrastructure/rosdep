:orphan:

rosdep manual page
==================

Synopsis
--------

**rosdep** <*command*> [*options*] [*args*]

Description
-----------

The **rosdep** command helps you install external dependencies in an
OS-independent manner.  For example, what Debian packages do you need
in order to get the OpenGL headers on Ubuntu? How about OS X? Fedora?
rosdep can answer this question for your platform and install the
necessary package(s).

For more information on rosdep, see http://ros.org/wiki/rosdep.

Run "rosdep -h" or "rosdep <command> -h" to access the built-in tool
documentation.
 
Commands
--------

**check <packages>...**

  Check if the dependencies of ROS package(s) have been met.

**install <packages>...**

  Install dependencies for specified ROS packages.

**db <packages>...**

  Display the dependency database for package(s).

**keys <packages>...**

  List the rosdep keys that the ROS packages depend on.

**what-needs <rosdeps>...**

  Print a list of packages that declare a rosdep on (at least
  one of) <rosdeps>

**where-defined <rosdeps>...**

  Print a list of YAML files that declare a rosdep on (at least
  one of) <rosdeps>

Options
-------

**--os=OS_NAME:OS_VERSION**

  Override OS name and version (colon-separated), e.g. ubuntu:lucid
  
**-i, --include_duplicates**

  Do not deduplicate

**-a, --all**

  Select all ROS packages.  Only valid for commands that take <packages> as arguments.

**-h, --help**

  Show usage information

**-v, --verbose**

  Enable verbose output

Install Options
---------------

**--reinstall**

  (re)install all dependencies, even if already installed

**-y, --default-yes**

  Tell the package manager to default to y or fail when installing

**-s, --simulate**

  Simulate install

**-r**

  Continue installing despite errors.
