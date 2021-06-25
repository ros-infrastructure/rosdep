# Copyright (c) 2009, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the Willow Garage, Inc. nor the names of its
#       contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# Author Tully Foote/tfoote@willowgarage.com

"""
Command-line interface to rosdep library
"""

from __future__ import print_function

import errno
import os
import sys
import traceback
try:
    from urllib.error import URLError
    from urllib.request import build_opener
    from urllib.request import HTTPBasicAuthHandler
    from urllib.request import HTTPHandler
    from urllib.request import install_opener
    from urllib.request import ProxyHandler
except ImportError:
    from urllib2 import build_opener
    from urllib2 import HTTPBasicAuthHandler
    from urllib2 import HTTPHandler
    from urllib2 import install_opener
    from urllib2 import ProxyHandler
    from urllib2 import URLError
import warnings

from optparse import OptionParser

import rospkg

from . import create_default_installer_context, get_default_installer
from . import __version__
from .core import RosdepInternalError, InstallFailed, UnsupportedOs, InvalidData, CachePermissionError, DownloadFailure
from .installers import normalize_uninstalled_to_list
from .installers import RosdepInstaller
from .lookup import RosdepLookup, ResolutionError, prune_catkin_packages
from .meta import MetaDatabase
from .rospkg_loader import DEFAULT_VIEW_KEY
from .sources_list import update_sources_list, get_sources_cache_dir,\
    download_default_sources_list, SourcesListLoader, CACHE_INDEX,\
    get_sources_list_dir, get_default_sources_list_file,\
    DEFAULT_SOURCES_LIST_URL
from .rosdistrohelper import PreRep137Warning

from .ament_packages import AMENT_PREFIX_PATH_ENV_VAR
from .ament_packages import get_packages_with_prefixes

from .catkin_packages import find_catkin_packages_in
from .catkin_packages import set_workspace_packages
from .catkin_packages import get_workspace_packages
from .catkin_packages import VALID_DEPENDENCY_TYPES
from catkin_pkg.package import InvalidPackage


class UsageError(Exception):
    pass


_usage = """usage: rosdep [options] <command> <args>

Commands:

rosdep check <stacks-and-packages>...
  check if the dependencies of package(s) have been met.

rosdep install <stacks-and-packages>...
  download and install the dependencies of a given package or packages.

rosdep db
  generate the dependency database and print it to the console.

rosdep init
  initialize rosdep sources in /etc/ros/rosdep.  May require sudo.

rosdep keys <stacks-and-packages>...
  list the rosdep keys that the packages depend on.

rosdep resolve <rosdeps>
  resolve <rosdeps> to system dependencies

rosdep update
  update the local rosdep database based on the rosdep sources.

rosdep what-needs <rosdeps>...
  print a list of packages that declare a rosdep on (at least
  one of) <rosdeps>

rosdep where-defined <rosdeps>...
  print a list of yaml files that declare a rosdep on (at least
  one of) <rosdeps>

rosdep fix-permissions
  Recursively change the permissions of the user's ros home directory.
  May require sudo.  Can be useful to fix permissions after calling
  "rosdep update" with sudo accidentally.
"""


def _get_default_RosdepLookup(options):
    """
    Helper routine for converting command-line options into
    appropriate RosdepLookup instance.
    """
    os_override = convert_os_override_option(options.os_override)
    sources_loader = SourcesListLoader.create_default(sources_cache_dir=options.sources_cache_dir,
                                                      os_override=os_override,
                                                      verbose=options.verbose)
    lookup = RosdepLookup.create_from_rospkg(sources_loader=sources_loader, dependency_types=options.dependency_types)
    lookup.verbose = options.verbose
    return lookup


def rosdep_main(args=None):
    if args is None:
        args = sys.argv[1:]
    try:
        exit_code = _rosdep_main(args)
        if exit_code not in [0, None]:
            sys.exit(exit_code)
    except rospkg.ResourceNotFound as e:
        print("""
ERROR: Rosdep cannot find all required resources to answer your query
%s
""" % (error_to_human_readable(e)), file=sys.stderr)
        sys.exit(1)
    except UsageError as e:
        print(_usage, file=sys.stderr)
        print('ERROR: %s' % (str(e)), file=sys.stderr)
        sys.exit(os.EX_USAGE)
    except RosdepInternalError as e:
        print("""
ERROR: Rosdep experienced an internal error.
Please go to the rosdep page [1] and file a bug report with the message below.
[1] : http://www.ros.org/wiki/rosdep

rosdep version: %s

%s
""" % (__version__, e.message), file=sys.stderr)
        sys.exit(1)
    except ResolutionError as e:
        print("""
ERROR: %s

%s
""" % (e.args[0], e), file=sys.stderr)
        sys.exit(1)
    except CachePermissionError as e:
        print(str(e))
        print("Try running 'sudo rosdep fix-permissions'")
        sys.exit(1)
    except UnsupportedOs as e:
        print('Unsupported OS: %s\nSupported OSes are [%s]' % (e.args[0], ', '.join(e.args[1])), file=sys.stderr)
        sys.exit(1)
    except InvalidPackage as e:
        print(str(e))
        sys.exit(1)
    except Exception as e:
        print("""
ERROR: Rosdep experienced an error: %s
Please go to the rosdep page [1] and file a bug report with the stack trace below.
[1] : http://www.ros.org/wiki/rosdep

rosdep version: %s

%s
""" % (e, __version__, traceback.format_exc()), file=sys.stderr)
        sys.exit(1)


def check_for_sources_list_init(sources_cache_dir):
    """
    Check to see if sources list and cache are present.
    *sources_cache_dir* alone is enough to pass as the user has the
    option of passing in a cache dir.

    If check fails, tell user how to resolve and sys exit.
    """
    commands = []
    filename = os.path.join(sources_cache_dir, CACHE_INDEX)
    if os.path.exists(filename):
        return
    else:
        commands.append('rosdep update')

    sources_list_dir = get_sources_list_dir()
    if not os.path.exists(sources_list_dir):
        commands.insert(0, 'sudo rosdep init')
    else:
        filelist = [f for f in os.listdir(sources_list_dir) if f.endswith('.list')]
        if not filelist:
            commands.insert(0, 'sudo rosdep init')

    if commands:
        commands = '\n'.join(['    %s' % c for c in commands])
        print("""
ERROR: your rosdep installation has not been initialized yet.  Please run:

%s
""" % (commands), file=sys.stderr)
        sys.exit(1)
    else:
        return True


def key_list_to_dict(key_list):
    """
    Convert a list of strings of the form 'foo:bar' to a dictionary.

    Splits strings of the form 'foo:bar quux:quax' into separate entries.
    """
    try:
        key_list = [key for s in key_list for key in s.split(' ')]
        return dict(map(lambda s: [t.strip() for t in s.split(':')], key_list))
    except ValueError as e:
        raise UsageError("Invalid 'key:value' list: '%s'" % ' '.join(key_list))


def str_to_bool(s):
    """Maps a string to bool. Supports true/false, and yes/no, and is case-insensitive"""
    s = s.lower()
    if s in ['yes', 'true']:
        return True
    elif s in ['no', 'false']:
        return False
    else:
        raise UsageError("Cannot parse '%s' as boolean" % s)


def setup_proxy_opener():
    # check for http[s]?_proxy user
    for scheme in ['http', 'https']:
        key = scheme + '_proxy'
        if key in os.environ:
            proxy = ProxyHandler({scheme: os.environ[key]})
            auth = HTTPBasicAuthHandler()
            opener = build_opener(proxy, auth, HTTPHandler)
            install_opener(opener)


def setup_environment_variables(ros_distro):
    """
    Set environment variables needed to find ROS packages and evaluate conditional dependencies.

    :param ros_distro: The requested ROS distro passed on the CLI, or None
    """
    if ros_distro is not None:
        if 'ROS_DISTRO' in os.environ and os.environ['ROS_DISTRO'] != ros_distro:
            # user has a different workspace sourced, use --rosdistro
            print('WARNING: given --rosdistro {} but ROS_DISTRO is "{}". Ignoring environment.'.format(
                ros_distro, os.environ['ROS_DISTRO']))
            # Use python version from --rosdistro
            if 'ROS_PYTHON_VERSION' in os.environ:
                del os.environ['ROS_PYTHON_VERSION']
        os.environ['ROS_DISTRO'] = ros_distro

    if 'ROS_PYTHON_VERSION' not in os.environ and 'ROS_DISTRO' in os.environ:
        # Set python version to version used by ROS distro
        python_versions = MetaDatabase().get('ROS_PYTHON_VERSION', default=[])
        if os.environ['ROS_DISTRO'] in python_versions:
            os.environ['ROS_PYTHON_VERSION'] = str(python_versions[os.environ['ROS_DISTRO']])

    if 'ROS_PYTHON_VERSION' not in os.environ:
        # Default to same python version used to invoke rosdep
        print('WARNING: ROS_PYTHON_VERSION is unset. Defaulting to {}'.format(sys.version[0]), file=sys.stderr)
        os.environ['ROS_PYTHON_VERSION'] = sys.version[0]


def _rosdep_main(args):
    # sources cache dir is our local database.
    default_sources_cache = get_sources_cache_dir()

    parser = OptionParser(usage=_usage, prog='rosdep')
    parser.add_option('--os', dest='os_override', default=None,
                      metavar='OS_NAME:OS_VERSION', help='Override OS name and version (colon-separated), e.g. ubuntu:lucid')
    parser.add_option('-c', '--sources-cache-dir', dest='sources_cache_dir', default=default_sources_cache,
                      metavar='SOURCES_CACHE_DIR', help='Override %s' % (default_sources_cache))
    parser.add_option('--verbose', '-v', dest='verbose', default=False,
                      action='store_true', help='verbose display')
    parser.add_option('--version', dest='print_version', default=False,
                      action='store_true', help='print just the rosdep version, then exit')
    parser.add_option('--all-versions', dest='print_all_versions', default=False,
                      action='store_true', help='print rosdep version and version of installers, then exit')
    parser.add_option('--reinstall', dest='reinstall', default=False,
                      action='store_true', help='(re)install all dependencies, even if already installed')
    parser.add_option('--default-yes', '-y', dest='default_yes', default=False,
                      action='store_true', help='Tell the package manager to default to y or fail when installing')
    parser.add_option('--simulate', '-s', dest='simulate', default=False,
                      action='store_true', help='Simulate install')
    parser.add_option('-r', dest='robust', default=False,
                      action='store_true', help='Continue installing despite errors.')
    parser.add_option('-q', dest='quiet', default=False,
                      action='store_true', help='Quiet. Suppress output except for errors.')
    parser.add_option('-a', '--all', dest='rosdep_all', default=False,
                      action='store_true', help='select all packages')
    parser.add_option('-n', dest='recursive', default=True,
                      action='store_false', help="Do not consider implicit/recursive dependencies.  Only valid with 'keys', 'check', and 'install' commands.")
    parser.add_option('--ignore-packages-from-source', '--ignore-src', '-i',
                      dest='ignore_src', default=False, action='store_true',
                      help="Affects the 'check', 'install', and 'keys' verbs. "
                           'If specified then rosdep will ignore keys that '
                           'are found to be catkin or ament packages anywhere in the '
                           'ROS_PACKAGE_PATH, AMENT_PREFIX_PATH or in any of the directories '
                           'given by the --from-paths option.')
    parser.add_option('--skip-keys',
                      dest='skip_keys', action='append', default=[],
                      help="Affects the 'check' and 'install' verbs. The "
                           'specified rosdep keys will be ignored, i.e. not '
                           'resolved and not installed. The option can be supplied multiple '
                           'times. A space separated list of rosdep keys can also '
                           'be passed as a string. A more permanent solution to '
                           'locally ignore a rosdep key is creating a local rosdep rule '
                           'with an empty list of packages (include it in '
                           '/etc/ros/rosdep/sources.list.d/ before the defaults).')
    parser.add_option('--filter-for-installers',
                      action='append', default=[],
                      help="Affects the 'db' verb. If supplied, the output of the 'db' "
                           'command is filtered to only list packages whose installer '
                           'is in the provided list. The option can be supplied '
                           'multiple times. A space separated list of installers can also '
                           'be passed as a string. Example: `--filter-for-installers "apt pip"`')
    parser.add_option('--from-paths', dest='from_paths',
                      default=False, action='store_true',
                      help="Affects the 'check', 'keys', and 'install' verbs. "
                           'If specified the arguments to those verbs will be '
                           'considered paths to be searched, acting on all '
                           'catkin packages found there in.')
    parser.add_option('--rosdistro', dest='ros_distro', default=None,
                      help='Explicitly sets the ROS distro to use, overriding '
                           'the normal method of detecting the ROS distro '
                           'using the ROS_DISTRO environment variable. '
                           "When used with the 'update' verb, "
                           'only the specified distro will be updated.')
    parser.add_option('--as-root', default=[], action='append',
                      metavar='INSTALLER_KEY:<bool>', help='Override '
                      'whether sudo is used for a specific installer, '
                      "e.g. '--as-root pip:false' or '--as-root \"pip:no homebrew:yes\"'. "
                      'Can be specified multiple times.')
    parser.add_option('--include-eol-distros', dest='include_eol_distros',
                      default=False, action='store_true',
                      help="Affects the 'update' verb. "
                           'If specified end-of-life distros are being '
                           'fetched too.')
    parser.add_option('-t', '--dependency-types', dest='dependency_types',
                      type="choice", choices=list(VALID_DEPENDENCY_TYPES),
                      default=[], action='append',
                      help='Dependency types to install, can be given multiple times. '
                           'Choose from {}. Default: all except doc.'.format(VALID_DEPENDENCY_TYPES))

    options, args = parser.parse_args(args)
    if options.print_version or options.print_all_versions:
        # First print the rosdep version.
        print('{}'.format(__version__))
        # If not printing versions of all installers, exit.
        if not options.print_all_versions:
            sys.exit(0)
        # Otherwise, Then collect the versions of the installers and print them.
        installers = create_default_installer_context().installers
        installer_keys = get_default_installer()[1]
        version_strings = []
        for key in installer_keys:
            if key == 'source':
                # Explicitly skip the source installer.
                continue
            installer = installers[key]
            try:
                installer_version_strings = installer.get_version_strings()
                assert isinstance(installer_version_strings, list), installer_version_strings
                version_strings.extend(installer_version_strings)
            except NotImplementedError:
                version_strings.append('{} unknown'.format(key))
                continue
            except EnvironmentError as e:
                if e.errno != errno.ENOENT:
                    raise
                version_strings.append('{} not installed'.format(key))
                continue
        if version_strings:
            print()
            print('Versions of installers:')
            print('\n'.join(['  ' + x for x in version_strings if x]))
        else:
            print()
            print('No installers with versions available found.')
        sys.exit(0)

    # flatten list of skipped keys, filter-for-installers, and dependency types
    options.skip_keys = [key for s in options.skip_keys for key in s.split(' ')]
    options.filter_for_installers = [inst for s in options.filter_for_installers for inst in s.split(' ')]
    options.dependency_types = [dep for s in options.dependency_types for dep in s.split(' ')]

    if len(args) == 0:
        parser.error('Please enter a command')
    command = args[0]
    if command not in _commands:
        parser.error('Unsupported command %s.' % command)
    args = args[1:]

    # Convert list of keys to dictionary
    options.as_root = dict((k, str_to_bool(v)) for k, v in key_list_to_dict(options.as_root).items())

    if command not in ['init', 'update', 'fix-permissions']:
        check_for_sources_list_init(options.sources_cache_dir)
        # _package_args_handler uses `ROS_DISTRO`, so environment variables must be set before
        setup_environment_variables(options.ros_distro)
    elif command not in ['fix-permissions']:
        setup_proxy_opener()

    if command in _command_rosdep_args:
        return _rosdep_args_handler(command, parser, options, args)
    elif command in _command_no_args:
        return _no_args_handler(command, parser, options, args)
    else:
        return _package_args_handler(command, parser, options, args)


def _no_args_handler(command, parser, options, args):
    if args:
        parser.error('command [%s] takes no arguments' % (command))
    else:
        return command_handlers[command](options)


def _rosdep_args_handler(command, parser, options, args):

    # rosdep keys as args
    if options.rosdep_all:
        parser.error('-a, --all is not a valid option for this command')
    elif len(args) < 1:
        parser.error("Please enter arguments for '%s'" % command)
    else:
        return command_handlers[command](args, options)


def _package_args_handler(command, parser, options, args):
    if options.rosdep_all:
        if args:
            parser.error('cannot specify additional arguments with -a')
        else:
            # let the loader filter the -a. This will take out some
            # packages that are catkinized (for now).
            lookup = _get_default_RosdepLookup(options)
            loader = lookup.get_loader()
            args = loader.get_loadable_resources()
            not_found = []
    elif not args:
        parser.error('no packages or stacks specified')

    # package or stack names as args.  have to convert stack names to packages.
    # - overrides to enable testing
    packages = []
    not_found = []
    if options.from_paths:
        for path in args:
            if options.verbose:
                print("Using argument '{0}' as a path to search.".format(path))
            if not os.path.exists(path):
                print("given path '{0}' does not exist".format(path))
                return 1
            path = os.path.abspath(path)
            if 'ROS_PACKAGE_PATH' not in os.environ:
                os.environ['ROS_PACKAGE_PATH'] = '{0}'.format(path)
            else:
                os.environ['ROS_PACKAGE_PATH'] = '{0}{1}{2}'.format(
                    path,
                    os.pathsep,
                    os.environ['ROS_PACKAGE_PATH']
                )
            pkgs = find_catkin_packages_in(path, options.verbose)
            packages.extend(pkgs)
        # Make packages list unique
        packages = list(set(packages))
    else:
        rospack = rospkg.RosPack()
        rosstack = rospkg.RosStack()
        val = rospkg.expand_to_packages(args, rospack, rosstack)
        packages = val[0]
        not_found = val[1]
    if not_found:
        raise rospkg.ResourceNotFound(not_found[0], rospack.get_ros_paths())

    # Handle the --ignore-src option
    if command in ['install', 'check', 'keys'] and options.ignore_src:
        if options.verbose:
            print('Searching ROS_PACKAGE_PATH for '
                  'sources: ' + str(os.environ['ROS_PACKAGE_PATH'].split(':')))
        ws_pkgs = get_workspace_packages()
        for path in os.environ['ROS_PACKAGE_PATH'].split(':'):
            path = os.path.abspath(path.strip())
            if os.path.exists(path):
                pkgs = find_catkin_packages_in(path, options.verbose)
                ws_pkgs.extend(pkgs)
            elif options.verbose:
                print('Skipping non-existent path ' + path)
        set_workspace_packages(ws_pkgs)

        # Lookup package names from ament index.
        if AMENT_PREFIX_PATH_ENV_VAR in os.environ:
            if options.verbose:
                print(
                    'Searching ' + AMENT_PREFIX_PATH_ENV_VAR + ' for '
                    'sources: ' + str(os.environ[AMENT_PREFIX_PATH_ENV_VAR].split(':')))
            ws_pkgs = get_workspace_packages()
            pkgs = get_packages_with_prefixes().keys()
            ws_pkgs.extend(pkgs)
            # Make packages list unique
            ws_pkgs = list(set(ws_pkgs))
            set_workspace_packages(ws_pkgs)

    lookup = _get_default_RosdepLookup(options)

    # Handle the --skip-keys option by pretending that they are packages in the catkin workspace
    if command in ['install', 'check'] and options.skip_keys:
        if options.verbose:
            print('Skipping the specified rosdep keys:\n- ' + '\n- '.join(options.skip_keys))
        lookup.skipped_keys = options.skip_keys

    if 0 and not packages:  # disable, let individual handlers specify behavior
        # possible with empty stacks
        print('No packages in arguments, aborting')
        return

    return command_handlers[command](lookup, packages, options)


def convert_os_override_option(options_os_override):
    """
    Convert os_override option flag to ``(os_name, os_version)`` tuple, or
    ``None`` if not set

    :returns: ``(os_name, os_version)`` tuple if option is set, ``None`` otherwise
    :raises: :exc:`UsageError` if option is not set properly
    """
    if not options_os_override:
        return None
    val = options_os_override
    if ':' not in val:
        raise UsageError('OS override must be colon-separated OS_NAME:OS_VERSION, e.g. ubuntu:maverick')
    os_name = val[:val.find(':')]
    os_version = val[val.find(':') + 1:]
    return os_name, os_version


def configure_installer_context(installer_context, options):
    """
    Configure the *installer_context* from *options*.

    - Override the OS detector in *installer_context* if necessary.
    - Set *as_root* for installers if specified.

    :raises: :exc:`UsageError` If user input options incorrectly
    """
    os_override = convert_os_override_option(options.os_override)
    if os_override is not None:
        installer_context.set_os_override(*os_override)
    for k, v in options.as_root.items():
        try:
            installer_context.get_installer(k).as_root = v
        except KeyError:
            raise UsageError("Installer '%s' not defined." % k)


def command_init(options):
    try:
        data = download_default_sources_list()
    except URLError as e:
        print('ERROR: cannot download default sources list from:\n%s\nWebsite may be down.' % (DEFAULT_SOURCES_LIST_URL))
        return 4
    except DownloadFailure as e:
        print('ERROR: cannot download default sources list from:\n%s\nWebsite may be down.' % (DEFAULT_SOURCES_LIST_URL))
        print(e)
        return 4
    # reuse path variable for error message
    path = get_sources_list_dir()
    old_umask = os.umask(0o022)
    try:
        if not os.path.exists(path):
            os.makedirs(path)
        path = get_default_sources_list_file()
        if os.path.exists(path):
            print('ERROR: default sources list file already exists:\n\t%s\nPlease delete if you wish to re-initialize' % (path))
            return 1
        with open(path, 'w') as f:
            f.write(data)
        print('Wrote %s' % (path))
        print('Recommended: please run\n\n\trosdep update\n')
    except IOError as e:
        print('ERROR: cannot create %s:\n\t%s' % (path, e), file=sys.stderr)
        return 2
    except OSError as e:
        print("ERROR: cannot create %s:\n\t%s\nPerhaps you need to run 'sudo rosdep init' instead" % (path, e), file=sys.stderr)
        return 3
    finally:
        os.umask(old_umask)


def command_update(options):
    error_occured = []

    def update_success_handler(data_source):
        print('Hit %s' % (data_source.url))

    def update_error_handler(data_source, exc):
        error_string = 'ERROR: unable to process source [%s]:\n\t%s' % (data_source.url, exc)
        print(error_string, file=sys.stderr)
        error_occured.append(error_string)
    sources_list_dir = get_sources_list_dir()

    # disable deprecation warnings when using the command-line tool
    warnings.filterwarnings('ignore', category=PreRep137Warning)

    if not os.path.exists(sources_list_dir):
        print('ERROR: no sources directory exists on the system meaning rosdep has not yet been initialized.\n\nPlease initialize your rosdep with\n\n\tsudo rosdep init\n')
        return 1

    filelist = [f for f in os.listdir(sources_list_dir) if f.endswith('.list')]
    if not filelist:
        print('ERROR: no data sources in %s\n\nPlease initialize your rosdep with\n\n\tsudo rosdep init\n' % sources_list_dir, file=sys.stderr)
        return 1
    try:
        print('reading in sources list data from %s' % (sources_list_dir))
        sources_cache_dir = get_sources_cache_dir()
        try:
            if os.geteuid() == 0:
                print("Warning: running 'rosdep update' as root is not recommended.", file=sys.stderr)
                print("  You should run 'sudo rosdep fix-permissions' and invoke 'rosdep update' again without sudo.", file=sys.stderr)
        except AttributeError:
            # nothing we wanna do under Windows
            pass
        update_sources_list(success_handler=update_success_handler,
                            error_handler=update_error_handler,
                            skip_eol_distros=not options.include_eol_distros,
                            ros_distro=options.ros_distro)
        print('updated cache in %s' % (sources_cache_dir))
    except InvalidData as e:
        print('ERROR: invalid sources list file:\n\t%s' % (e), file=sys.stderr)
        return 1
    except IOError as e:
        print('ERROR: error loading sources list:\n\t%s' % (e), file=sys.stderr)
        return 1
    except ValueError as e:
        print('ERROR: invalid argument value provided:\n\t%s' % (e), file=sys.stderr)
        return 1
    if error_occured:
        print('ERROR: Not all sources were able to be updated.\n[[[')
        for e in error_occured:
            print(e)
        print(']]]')
        return 1


def command_keys(lookup, packages, options):
    lookup = _get_default_RosdepLookup(options)
    rosdep_keys = get_keys(lookup, packages, options.recursive)
    prune_catkin_packages(rosdep_keys, options.verbose)
    _print_lookup_errors(lookup)
    print('\n'.join(rosdep_keys))


def get_keys(lookup, packages, recursive):
    rosdep_keys = set()  # using a set to ensure uniqueness
    for package_name in packages:
        deps = lookup.get_rosdeps(package_name, implicit=recursive)
        rosdep_keys.update(deps)
    return list(rosdep_keys)


def command_check(lookup, packages, options):
    verbose = options.verbose

    installer_context = create_default_installer_context(verbose=verbose)
    configure_installer_context(installer_context, options)
    installer = RosdepInstaller(installer_context, lookup)

    uninstalled, errors = installer.get_uninstalled(packages, implicit=options.recursive, verbose=verbose)

    # pretty print the result
    if [v for k, v in uninstalled if v]:
        print('System dependencies have not been satisfied:')
        for installer_key, resolved in uninstalled:
            if resolved:
                for r in resolved:
                    print('%s\t%s' % (installer_key, r))
    else:
        print('All system dependencies have been satisfied')
    if errors:
        for package_name, ex in errors.items():
            if isinstance(ex, rospkg.ResourceNotFound):
                print('ERROR[%s]: resource not found [%s]' % (package_name, ex.args[0]), file=sys.stderr)
            else:
                print('ERROR[%s]: %s' % (package_name, ex), file=sys.stderr)
    if uninstalled:
        return 1
    else:
        return 0


def error_to_human_readable(error):
    if isinstance(error, rospkg.ResourceNotFound):
        return 'Missing resource %s' % (error,)
    elif isinstance(error, ResolutionError):
        return '%s' % (error.args[0],)
    else:
        return '%s' % (error,)


def command_install(lookup, packages, options):
    # map options
    install_options = dict(interactive=not options.default_yes, verbose=options.verbose,
                           reinstall=options.reinstall,
                           continue_on_error=options.robust, simulate=options.simulate, quiet=options.quiet)

    # setup installer
    installer_context = create_default_installer_context(verbose=options.verbose)
    configure_installer_context(installer_context, options)
    installer = RosdepInstaller(installer_context, lookup)

    if options.reinstall:
        if options.verbose:
            print('reinstall is true, resolving all dependencies')
        try:
            uninstalled, errors = lookup.resolve_all(packages, installer_context, implicit=options.recursive)
        except InvalidData as e:
            print('ERROR: unable to process all dependencies:\n\t%s' % (e), file=sys.stderr)
            return 1
    else:
        uninstalled, errors = installer.get_uninstalled(packages, implicit=options.recursive, verbose=options.verbose)

    if options.verbose:
        uninstalled_dependencies = normalize_uninstalled_to_list(uninstalled)
        print('uninstalled dependencies are: [%s]' % ', '.join(uninstalled_dependencies))

    if errors:
        err_msg = ('ERROR: the following packages/stacks could not have their '
                   'rosdep keys resolved\nto system dependencies')
        if rospkg.distro.current_distro_codename() is None:
            err_msg += (
                ' (ROS distro is not set. '
                'Make sure `ROS_DISTRO` environment variable is set, or use '
                '`--rosdistro` option to specify the distro, '
                'e.g. `--rosdistro indigo`)'
            )
        print(err_msg + ':', file=sys.stderr)
        for rosdep_key, error in errors.items():
            print('%s: %s' % (rosdep_key, error_to_human_readable(error)), file=sys.stderr)
        if options.robust:
            print('Continuing to install resolvable dependencies...')
        else:
            return 1
    try:
        installer.install(uninstalled, **install_options)
        if not options.simulate:
            print('#All required rosdeps installed successfully')
        return 0
    except KeyError as e:
        raise RosdepInternalError(e)
    except InstallFailed as e:
        print('ERROR: the following rosdeps failed to install', file=sys.stderr)
        print('\n'.join(['  %s: %s' % (k, m) for k, m in e.failures]), file=sys.stderr)
        return 1


def command_db(options):
    # exact same setup logic as command_resolve, should possibly combine
    lookup = _get_default_RosdepLookup(options)
    installer_context = create_default_installer_context(verbose=options.verbose)
    configure_installer_context(installer_context, options)
    os_name, os_version = installer_context.get_os_name_and_version()
    try:
        installer_keys = installer_context.get_os_installer_keys(os_name)
        default_key = installer_context.get_default_os_installer_key(os_name)
    except KeyError:
        raise UnsupportedOs(os_name, installer_context.get_os_keys())
    installer = installer_context.get_installer(default_key)

    print('OS NAME: %s' % os_name)
    print('OS VERSION: %s' % os_version)
    errors = []
    print('DB [key -> resolution]')
    # db does not leverage the resource-based API
    view = lookup.get_rosdep_view(DEFAULT_VIEW_KEY, verbose=options.verbose)
    for rosdep_name in view.keys():
        try:
            d = view.lookup(rosdep_name)
            inst_key, rule = d.get_rule_for_platform(os_name, os_version, installer_keys, default_key)
            if options.filter_for_installers and inst_key not in options.filter_for_installers:
                continue
            resolved = installer.resolve(rule)
            resolved_str = ' '.join([str(r) for r in resolved])
            print('%s -> %s' % (rosdep_name, resolved_str))
        except ResolutionError as e:
            errors.append(e)

    # TODO: add command-line option for users to be able to see this.
    # This is useful for platform bringup, but useless for most users
    # as the rosdep db contains numerous, platform-specific keys.
    if 0:
        for error in errors:
            print('WARNING: %s' % (error_to_human_readable(error)), file=sys.stderr)


def _print_lookup_errors(lookup):
    for error in lookup.get_errors():
        if isinstance(error, rospkg.ResourceNotFound):
            print('WARNING: unable to locate resource %s' % (str(error.args[0])), file=sys.stderr)
        else:
            print('WARNING: %s' % (str(error)), file=sys.stderr)


def command_what_needs(args, options):
    lookup = _get_default_RosdepLookup(options)
    packages = []
    for rosdep_name in args:
        packages.extend(lookup.get_resources_that_need(rosdep_name))

    _print_lookup_errors(lookup)
    print('\n'.join(set(packages)))


def command_where_defined(args, options):
    lookup = _get_default_RosdepLookup(options)
    locations = []
    for rosdep_name in args:
        locations.extend(lookup.get_views_that_define(rosdep_name))

    _print_lookup_errors(lookup)
    if locations:
        for location in locations:
            origin = location[1]
            print(origin)
    else:
        print('ERROR: cannot find definition(s) for [%s]' % (', '.join(args)), file=sys.stderr)
        return 1


def command_resolve(args, options):
    lookup = _get_default_RosdepLookup(options)
    installer_context = create_default_installer_context(verbose=options.verbose)
    configure_installer_context(installer_context, options)

    installer, installer_keys, default_key, \
        os_name, os_version = get_default_installer(installer_context=installer_context,
                                                    verbose=options.verbose)
    invalid_key_errors = []
    for rosdep_name in args:
        if len(args) > 1:
            print('#ROSDEP[%s]' % rosdep_name)

        view = lookup.get_rosdep_view(DEFAULT_VIEW_KEY, verbose=options.verbose)
        try:
            d = view.lookup(rosdep_name)
        except KeyError as e:
            invalid_key_errors.append(e)
            continue
        rule_installer, rule = d.get_rule_for_platform(os_name, os_version, installer_keys, default_key)

        installer = installer_context.get_installer(rule_installer)
        resolved = installer.resolve(rule)
        print('#%s' % (rule_installer))
        print(' '.join([str(r) for r in resolved]))

    for error in invalid_key_errors:
        print('ERROR: no rosdep rule for %s' % (error), file=sys.stderr)

    for error in lookup.get_errors():
        print('WARNING: %s' % (error_to_human_readable(error)), file=sys.stderr)

    if invalid_key_errors:
        return 1  # error exit code


def command_fix_permissions(options):
    import os
    import pwd
    import grp

    stat_info = os.stat(os.path.expanduser('~'))
    uid = stat_info.st_uid
    gid = stat_info.st_gid
    user_name = pwd.getpwuid(uid).pw_name
    try:
        group_name = grp.getgrgid(gid).gr_name
    except KeyError as e:
        group_name = gid
    ros_home = rospkg.get_ros_home()

    print("Recursively changing ownership of ros home directory '{0}' "
          "to '{1}:{2}' (current user)...".format(ros_home, user_name, group_name))
    failed = []
    try:
        for dirpath, dirnames, filenames in os.walk(ros_home):
            try:
                os.lchown(dirpath, uid, gid)
            except Exception as e:
                failed.append((dirpath, str(e)))
            for f in filenames:
                try:
                    path = os.path.join(dirpath, f)
                    os.lchown(path, uid, gid)
                except Exception as e:
                    failed.append((path, str(e)))
    except Exception:
        import traceback
        traceback.print_exc()
        print('Failed to walk directory. Try with sudo?')
    else:
        if failed:
            print('Failed to change ownership for:')
            for p, e in failed:
                print('{0} --> {1}'.format(p, e))
            print('Try with sudo?')
        else:
            print('Done.')


command_handlers = {
    'db': command_db,
    'check': command_check,
    'keys': command_keys,
    'install': command_install,
    'what-needs': command_what_needs,
    'where-defined': command_where_defined,
    'resolve': command_resolve,
    'init': command_init,
    'update': command_update,
    'fix-permissions': command_fix_permissions,

    # backwards compat
    'what_needs': command_what_needs,
    'where_defined': command_where_defined,
    'depdb': command_db,
}

# commands that accept rosdep names as args
_command_rosdep_args = ['what-needs', 'what_needs', 'where-defined', 'where_defined', 'resolve']
# commands that take no args
_command_no_args = ['update', 'init', 'db', 'fix-permissions']

_commands = command_handlers.keys()
