0.11.6 (2017-08-01)
-------------------
- Changed the way virtual packages are checked in apt to use ``apt-cache``
  - https://github.com/ros-infrastructure/rosdep/pull/533
- Fixed a bug where the dependencies of metapackages were not being installed
  - https://github.com/ros-infrastructure/rosdep/pull/531
- Improved error handling of failed downloads or invalid source files
  - https://github.com/ros-infrastructure/rosdep/pull/523

0.11.6 (2017-07-27)
-------------------

- Added resinstall option for ``pip`` installer
  - https://github.com/ros-infrastructure/rosdep/pull/450
- Fixed detection and handling of virtual packages in ``apt`` (more changes to follow)
  - https://github.com/ros-infrastructure/rosdep/pull/468
  - https://github.com/ros-infrastructure/rosdep/pull/515
- Added support for Slackware
  - https://github.com/ros-infrastructure/rosdep/pull/469
- Fixed flags being passed to pacman on Arch Linux
  - https://github.com/ros-infrastructure/rosdep/pull/472
  - https://github.com/ros-infrastructure/rosdep/pull/476
- No longer uses ``sudo`` when already root
  - https://github.com/ros-infrastructure/rosdep/pull/474
- Added more information to ``rosdep --version``
  - https://github.com/ros-infrastructure/rosdep/pull/481
  - https://github.com/ros-infrastructure/rosdep/pull/499
- Fixed bug when using ``--verbose`` with ``rosdep install`` on macOS with Homebrew
  - https://github.com/ros-infrastructure/rosdep/pull/525
- Fixed bug with the ``depends:`` part of a stanze not being used to ordered installations correctly
  - https://github.com/ros-infrastructure/rosdep/pull/529
- Fixed Python3 bug on macOS
  - https://github.com/ros-infrastructure/rosdep/pull/441

0.11.5 (2016-05-23)
-------------------

- add ca-certificates as a dependency to support https urls
- add quiet option for ``pip``
- Documentation updates
- Elementary support improvements

0.11.4 (2015-09-25)
-------------------

- Fix bug in `pip` package detection code.

0.11.3 (2015-09-24)
-------------------

- Added an option to print out only apt and pip installable packages as commands.
- Added warning when neither the ``ROS_DISTRO`` environment variable is set nor the ``--rosdistro`` option is used.
- Fixed a bug related to group id resolution.
- Switched to using DNF instead of YUM for Fedora 22+.
- Fixed a bug where pip packages were not detected for older versions of ``pip``.
- Fixed a bug where dependencies of packages were gotten from the wrong ``package.xml`` when that package was being overlaid with local packages.
