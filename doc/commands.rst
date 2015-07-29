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

  Initialize /etc/ros/rosdep/sources.list.d/ configuration.  May require sudo.

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

**-q**

  Suppress output except for errors

**-n**

  Do not consider implicit/recursive dependencies.  Only valid with ``keys``, ``check``, and ``install`` commands.

**-i, --ignore-packages-from-source, --ignore-src**

  Affects the ``check`` and ``install`` verbs. If specified then rosdep will not install keys that are found to be catkin packages anywhere in the ROS_PACKAGE_PATH or in any of the directories given by the ``--from-paths`` option.
  
**--skip-keys=SKIP_KEYS**

  Affects the ``check`` and ``install`` verbs. The specified rosdep keys will be ignored, i.e. not resolved and not installed. The option can be supplied multiple times. A space separated list of rosdep keys can also be passed as a string. A more permanent solution to locally ignore a rosdep key is creating a local rosdep rule with an empty list of packages (include it in ``/etc/ros/rosdep/sources.list.d/`` before the defaults).

**--from-paths**

  Affects the ``check``, ``keys``, and ``install`` verbs. If specified the arugments to those verbs will be considered paths to be searched, acting on all catkin packages found there in.
 
**--rosdistro=ROS_DISTRO**

  Explicitly sets the ROS distro to use, overriding the normal method of detecting the ROS distro using the ROS_DISTRO environment variable.

**--as-root=INSTALLER_KEY:<bool>**

  Override whether sudo is used for a specific installer, e.g. ``--as-root pip:false`` or ``--as-root "pip:no homebrew:yes"``. Can be specified multiple times.


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

