0.14.0 (2018-11-06)
-------------------
- Skip EOL distros by default, add option to include them
  - https://github.com/ros-infrastructure/rosdep/pull/647

0.13.0 (2018-11-06)
-------------------
- Improve error message when a package.xml is malformed
  - https://github.com/ros-infrastructure/rosdep/pull/608
- Enable rosdep db cache from python3 to be used from python2.
  - https://github.com/ros-infrastructure/rosdep/pull/633
  - Reported in https://github.com/ros-infrastructure/rosdep/issues/3791
- Fix DNF installer behavior to match yum and apt.
  - https://github.com/ros-infrastructure/rosdep/pull/638
- Clean up executable permissions and #! lines.
  - https://github.com/ros-infrastructure/rosdep/pull/630
- Fix quiet mode for Debian installer.
  - https://github.com/ros-infrastructure/rosdep/pull/612
- Fix typos in documentation.
  - https://github.com/ros-infrastructure/rosdep/pull/606
  - https://github.com/ros-infrastructure/rosdep/pull/634
- Improve documentation output on Fedora.
  - https://github.com/ros-infrastructure/rosdep/pull/628
- Update CI infrastructure.
  - https://github.com/ros-infrastructure/rosdep/pull/602
  - https://github.com/ros-infrastructure/rosdep/pull/609
  - https://github.com/ros-infrastructure/rosdep/pull/629
  - https://github.com/ros-infrastructure/rosdep/pull/636
- Fix RPM comand tests.
  - https://github.com/ros-infrastructure/rosdep/pull/627
- Update package metadata.
  - https://github.com/ros-infrastructure/rosdep/pull/605

0.12.2 (2018-03-21)
-------------------
- Fix bug introduced in https://github.com/ros-infrastructure/rosdep/pull/521, reported in https://github.com/ros-infrastructure/rosdep/issues/589
  - https://github.com/ros-infrastructure/rosdep/pull/585

0.12.1 (2018-02-08)
-------------------
- Revert "Use ROS_ETC_DIR environment variable" to fix regression introduced in 0.12.0
  - https://github.com/ros-infrastructure/rosdep/pull/584

0.12.0 (2018-02-07)
-------------------
- Support for wildcard OS versions as specified in the updated REP 111
  - https://github.com/ros-infrastructure/rosdep/pull/573
- Add conflict with Debian package python-rosdep2
  - https://github.com/ros-infrastructure/rosdep/pull/579
- Remove redundant dependency checks
  - https://github.com/ros-infrastructure/rosdep/pull/556
- Update the FreeBSD installer
  - https://github.com/ros-infrastructure/rosdep/pull/574
- Fix detection of installed rpms and warn if slow method is being used
  - https://github.com/ros-infrastructure/rosdep/pull/568
- Support for installing virtual packages (Debian)
  - https://github.com/ros-infrastructure/rosdep/pull/521
- Remove non-interactive mode in slackware
  - https://github.com/ros-infrastructure/rosdep/pull/553
- Use ROS_ETC_DIR environment variable
  - https://github.com/ros-infrastructure/rosdep/pull/551
- Add __repr__ for SourceInstall
  - https://github.com/ros-infrastructure/rosdep/pull/543
- Keep dependencies order
  - https://github.com/ros-infrastructure/rosdep/pull/545
- Fix db command on OS X
  - https://github.com/ros-infrastructure/rosdep/pull/541

0.11.8 (2017-08-03)
-------------------
- Fix handling of metapackages
  - https://github.com/ros-infrastructure/rosdep/pull/535
  - regression of https://github.com/ros-infrastructure/rosdep/pull/531

0.11.7 (2017-08-01)
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
