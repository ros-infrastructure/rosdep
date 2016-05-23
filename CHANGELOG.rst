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
