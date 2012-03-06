rosdep command reference
========================

.. _rosdep_usage:

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

Run ``rosdep -h`` or ``rosdep <command> -h`` to access the built-in tool
documentation.
 
Commands
--------

**check <stacks-and-packages>...**

  Check if the dependencies of ROS package(s) have been met.

**db**

  Display the local rosdep database.

**init**

  Initialize /etc/ros/sources.list.d/ configuration.  May require sudo.

**install <stacks-and-packages>...**

  Install dependencies for specified ROS packages.

**keys <stacks-and-packages>...**

  List the rosdep keys that the ROS packages depend on.

**resolve <rosdeps>...**

  Resolve <rosdeps> to system dependencies

**update**

  Update the local rosdep database based on the rosdep sources.

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
  
**-c SOURCES_CACHE_DIR, --sources-cache-dir=SOURCES_CACHE_DIR**

  Override default sources cache directory (local rosdep database).
  
**-a, --all**

  Select all ROS packages.  Only valid for commands that take <stacks-and-packages> as arguments.

**-h, --help**

  Show usage information

**-v, --verbose**

  Enable verbose output

**--version**

  Print version and exit.

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

**-R**

  Install implicit/recursive dependencies.

