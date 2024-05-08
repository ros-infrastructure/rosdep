0.24.0 (2024-05-07)
-------------------
- Reapply "fix: pkg_resources deprecated warning"
  - https://github.com/ros-infrastructure/rosdep/issues/968
- Drop support for Python 2
  - https://github.com/ros-infrastructure/rosdep/issues/968

0.23.1 (2024-05-07)
-------------------
- Revert "fix: pkg_resources deprecated warning"
  - https://github.com/ros-infrastructure/rosdep/issues/968
- Add Windows-specific ENOENT error message to test
  - https://github.com/ros-infrastructure/rosdep/pull/961
- Skip a test rather than passing when not on Ubuntu
  - https://github.com/ros-infrastructure/rosdep/pull/962
- Fix some platform-specific path assumptions in tests
  - https://github.com/ros-infrastructure/rosdep/pull/960
- Fix shell-specific test assumptions
  - https://github.com/ros-infrastructure/rosdep/pull/959
- Prevent git from adding CR to certain test artifacts
  - https://github.com/ros-infrastructure/rosdep/pull/958
- Fix several tests which require os.geteuid
  - https://github.com/ros-infrastructure/rosdep/pull/957

0.23.0 (2024-04-19)
-------------------
- Use setup.cfg to configure flake8, instead of in the ci code
  - https://github.com/ros-infrastructure/rosdep/pull/930
- Fix makefile target test (``make test``) failing due to "cd test"
  - https://github.com/ros-infrastructure/rosdep/pull/951
- Implement test fixture for faking the rosdistro repo
  - https://github.com/ros-infrastructure/rosdep/pull/949
- Return non-zero if ``rosdep check`` cannot locate dependent
  - https://github.com/ros-infrastructure/rosdep/pull/948
- Fix potential bug in test_rosdep_sources_list.py
  - https://github.com/ros-infrastructure/rosdep/pull/952
- Fix pkg_resources deprecated warning
  - https://github.com/ros-infrastructure/rosdep/pull/926
- Print exception if it's of type URLError
  - https://github.com/ros-infrastructure/rosdep/pull/946
- Teach rosdep to use ROS_VERSION when resolving conditionals
  - https://github.com/ros-infrastructure/rosdep/pull/941
- Resolve flake8-comprehensions violations
  - https://github.com/ros-infrastructure/rosdep/pull/943

0.22.2 (2023-03-20)
-------------------
- Enable rosdep init to work with non-extant ROSDEP_SOURCE_PATH
  - https://github.com/ros-infrastructure/rosdep/pull/911
- Require flake8 < 6 for linting
  - https://github.com/ros-infrastructure/rosdep/pull/913
- Fix a flake8 violation in tests
  - https://github.com/ros-infrastructure/rosdep/pull/893

0.22.1 (2022-06-24)
-------------------
- Drop ROS Python package dependencies in debs
  - https://github.com/ros-infrastructure/rosdep/pull/887
- Drop some over-agressive asserts from test_rosdep_main
  - https://github.com/ros-infrastructure/rosdep/pull/888

0.22.0 (2022-06-24)
-------------------
- Fix support for rosdep on Windows.
  - https://github.com/ros-infrastructure/rosdep/pull/811
- Fix homebrew listing to show only formula.
  - https://github.com/ros-infrastructure/rosdep/pull/792
- Correctly detect when pip is not available.
  - https://github.com/ros-infrastructure/rosdep/pull/822
- Correctly detect when gem is not available.
  - https://github.com/ros-infrastructure/rosdep/pull/823
- Update target package for tests.
  - https://github.com/ros-infrastructure/rosdep/pull/835
- Drop support for EOL Ubuntu distros and add Focal.
  - https://github.com/ros-infrastructure/rosdep/pull/829
- Remove references to Travis CI.
  - https://github.com/ros-infrastructure/rosdep/pull/836
- Add support for wildcard OS name.
  - https://github.com/ros-infrastructure/rosdep/pull/838
- Refactor CI platforms.
  - https://github.com/ros-infrastructure/rosdep/pull/843
- Update release distributions.
  - https://github.com/ros-infrastructure/rosdep/pull/842
- Use unittest.mock where possible.
  - https://github.com/ros-infrastructure/rosdep/pull/850
- Support RosdepLookup overrides for several commands.
  - https://github.com/ros-infrastructure/rosdep/pull/847
- Detect Alpine package name with alias.
  - https://github.com/ros-infrastructure/rosdep/pull/848
- Run tests with pytest instead of nose.
  - https://github.com/ros-infrastructure/rosdep/pull/863
- Alias Raspbian to Debian.
  - https://github.com/ros-infrastructure/rosdep/pull/867
- Support PEP 338 invocation of rosdep2 module.
  - https://github.com/ros-infrastructure/rosdep/pull/862
- Improve consistency of stderr usage.
  - https://github.com/ros-infrastructure/rosdep/pull/846
- Make -q (quiet) work for update verb.
  - https://github.com/ros-infrastructure/rosdep/pull/844
- Pass with flake8_comprehensions.
  - https://github.com/ros-infrastructure/rosdep/pull/861
- Add pip installer to arch linux platform.
  - https://github.com/ros-infrastructure/rosdep/pull/865
- Compress HTTP with GZip where available.
  - https://github.com/ros-infrastructure/rosdep/pull/837
- If Manjaro is detected override to Arch Linux.
  - https://github.com/ros-infrastructure/rosdep/pull/866
- Clean up some C417 flake8 violations.
  - https://github.com/ros-infrastructure/rosdep/pull/876
- List 'ROS Infrastructure Team' as the package maintainer.
  - https://github.com/ros-infrastructure/rosdep/pull/859
- Require setuptools, src/rosdep2/platforms/pip.py imports pkg_resources.
  - https://github.com/ros-infrastructure/rosdep/pull/809
- Bump minimum Python 3 version in stdeb to 3.6.
  - https://github.com/ros-infrastructure/rosdep/pull/879
- Update developer documentation to reflect mock dependency.
  - https://github.com/ros-infrastructure/rosdep/pull/880
- Run tests against Python 3.10.
  - https://github.com/ros-infrastructure/rosdep/pull/883
- Ignore rosdep's own deprecations when running rosdep tests.
  - https://github.com/ros-infrastructure/rosdep/pull/882
- Declare test dependencies in [test] extra.
  - https://github.com/ros-infrastructure/rosdep/pull/881
- Mark linter tests and tests which require network.
  - https://github.com/ros-infrastructure/rosdep/pull/884

0.21.0 (2021-06-25)
-------------------
- Add command line option to select which dependency types to install.
  - https://github.com/ros-infrastructure/rosdep/pull/789
  - https://github.com/ros-infrastructure/rosdep/pull/727
- Fix output formatting for npm installer when running ``rosdep --all-versions``.
  - https://github.com/ros-infrastructure/rosdep/pull/814
- Fix exception running ``rosdep --all-versions`` when some installers are missing.
  - https://github.com/ros-infrastructure/rosdep/pull/815
- Display advice for fixing permissions when rosdep cache is not readable.
  - https://github.com/ros-infrastructure/rosdep/pull/787

0.20.1 (2021-04-16)
-------------------
- Fix a typo in the ament_packages README
  - https://github.com/ros-infrastructure/rosdep/pull/796
- Add support for a few RHEL clones
  - https://github.com/ros-infrastructure/rosdep/pull/802

0.20.0 (2020-11-12)
-------------------
- Install packages in buildtool_export_depends.
  - https://github.com/ros-infrastructure/rosdep/pull/753
- Remove shebang from a non-executable file.
  - https://github.com/ros-infrastructure/rosdep/pull/755
- Add alias for Pop! OS
  - https://github.com/ros-infrastructure/rosdep/pull/757
- Use tool-specific user-agent to retrieve custom rules from websites.
  - https://github.com/ros-infrastructure/rosdep/pull/775
  - https://github.com/ros-infrastructure/rosdep/issues/774
- Update catkin-sphinx link in documentation.
  - https://github.com/ros-infrastructure/rosdep/pull/783
- Add ZorinOS detection support.
  - https://github.com/ros-infrastructure/rosdep/pull/712
- Fix handling of installer version strings in Python 3.
  - https://github.com/ros-infrastructure/rosdep/pull/776
- Use GitHub Actions for CI.
  - https://github.com/ros-infrastructure/rosdep/pull/751
  - https://github.com/ros-infrastructure/rosdep/pull/785
- Add npm installer support.
  - https://github.com/ros-infrastructure/rosdep/pull/692
- Set Python2-Depends-Name option to allow releasing from Ubuntu Focal.
  - https://github.com/ros-infrastructure/rosdep/pull/766

0.19.0 (2020-04-03)
-------------------
- Only release for Python3 into focal
  - https://github.com/ros-infrastructure/rosdep/pull/734
- Added --rosdistro argument to rosdep-update to scope update to one rosdistro
  - https://github.com/ros-infrastructure/rosdep/pull/738
  - Fixes https://github.com/ros-infrastructure/rosdep/pull/723
- Fix CI for Python 3.4 and run slower CI jobs first
  - https://github.com/ros-infrastructure/rosdep/pull/739
- Strip Alpine's patch version from OS codename
  - https://github.com/ros-infrastructure/rosdep/pull/716
  - Fixes https://github.com/ros-infrastructure/rosdep/issues/715
- Raise a clear and specific error message for null entries
  - https://github.com/ros-infrastructure/rosdep/pull/726
- Use DNF as the default installer on RHEL 8 and newer
  - https://github.com/ros-infrastructure/rosdep/pull/713
- Updates to YUM and DNF handling
  - https://github.com/ros-infrastructure/rosdep/pull/640
- Fix tests so they don't assume euid != 0
  - https://github.com/ros-infrastructure/rosdep/pull/703
- Update openSUSE package query function and enable pip installer
  - https://github.com/ros-infrastructure/rosdep/pull/729
- Fix conditional dependencies when one package uses manifest.xml
  - https://github.com/ros-infrastructure/rosdep/pull/737
- Handle StopIteration when querying in debian platform
  - https://github.com/ros-infrastructure/rosdep/pull/701
- Use entry points rather than console scripts to enable usage on Windows
  - https://github.com/ros-infrastructure/rosdep/pull/656
- Depend on modules packages only to allow modules packages to be co-installable.
  - https://github.com/ros-infrastructure/rosdep/pull/750


0.18.0 (2019-11-20)
-------------------
- split -modules into separate Debian package
  - https://github.com/ros-infrastructure/rosdep/pull/731
- fix macOS CI
  - https://github.com/ros-infrastructure/rosdep/pull/730

0.17.0 (2019-10-18)
-------------------
- Fix TypeError on ROS Kinetic.
  - https://github.com/ros-infrastructure/rosdep/issues/721
- Pip installer uses ROS_PYTHON_VERSION
  - https://github.com/ros-infrastructure/rosdep/issues/709

0.16.2 (2019-10-18)
-------------------
- Bump rospkg dependency to guarantee all platforms are available..
  - https://github.com/ros-infrastructure/rosdep/issues/717
- Set ROS_PYTHON_VERSION if unset.
  - https://github.com/ros-infrastructure/rosdep/issues/708

0.16.1 (2019-09-19)
-------------------

- Fix problem with release uploaded to PyPI.
  - https://github.com/ros-infrastructure/rosdep/issues/705

0.16.0 (2019-09-19)
-------------------
- Add support for Nix/NixOS.
  - https://github.com/ros-infrastructure/rosdep/pull/697
- Update supported platforms.
  - Dropped platforms older than Xenial.
  - Added Ubuntu Cosmic, Disco, and Eoan.
  - https://github.com/ros-infrastructure/rosdep/pull/700
- Add sudo dependency in debian packages.
  - https://github.com/ros-infrastructure/rosdep/pull/680
- Improve support for AMENT_PREFIX_PATH used in ROS 2.
  - https://github.com/ros-infrastructure/rosdep/pull/699
- Add support for the --ignore-src argument for the keys verb.
  - https://github.com/ros-infrastructure/rosdep/pull/686

0.15.2 (2019-05-17)
-------------------
- Migrate to yaml.safe_load to avoid yaml.load vulnerabilities.
  - https://github.com/ros-infrastructure/rosdep/pull/675
- Improve text feeback and prompts
  - https://github.com/ros-infrastructure/rosdep/pull/675
  - https://github.com/ros-infrastructure/rosdep/pull/670
  - https://github.com/ros-infrastructure/rosdep/pull/665
- Add support for MX Linux
  - https://github.com/ros-infrastructure/rosdep/pull/674
- Add support for OpenEmbedded
  - https://github.com/ros-infrastructure/rosdep/pull/673
- Add support for Alpine
  - https://github.com/ros-infrastructure/rosdep/pull/673
- Add support for CentOS and improve RHEL
  - https://github.com/ros-infrastructure/rosdep/pull/668
  - https://github.com/ros-infrastructure/rosdep/pull/667

0.15.1 (2019-02-19)
-------------------
- Change GitHub url's which no longer work.
  - https://github.com/ros-infrastructure/rosdep/pull/663
- Fixed a flake8 warning.
  - https://github.com/ros-infrastructure/rosdep/pull/659
- Reduced number of supported platforms, e.g. trusty and newer only now.
  - https://github.com/ros-infrastructure/rosdep/pull/657

0.15.0 (2019-01-24)
-------------------
- Use yaml.safe_load for untrusted yaml input.
  - https://github.com/ros-infrastructure/rosdep/pull/651
- Evaluate conditions before collecting dependencies.
  - https://github.com/ros-infrastructure/rosdep/pull/655
  - Fixes https://github.com/ros-infrastructure/rosdep/pull/653
- Filter ROS 2 distros out of ROS 1 test results.
  - https://github.com/ros-infrastructure/rosdep/pull/652

0.14.0 (2019-01-14)
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
