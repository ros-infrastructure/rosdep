#!/usr/bin/env python
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

import os
import sys
import traceback

from optparse import OptionParser

import rospkg

from . import create_default_installer_context
from .core import RosdepInternalError, InstallFailed
from .installers import RosdepInstaller
from .lookup import RosdepLookup, ResolutionError

class UsageError(Exception):
    pass

_usage = """usage: rosdep [options] <command> <args>

Commands:

rosdep check <packages>...
  will check if the dependencies of package(s) have been met.

rosdep install <packages>...
  will generate a bash script and then execute it.

rosdep db <packages>...
  will generate the dependency database for package(s) and print
  it to the console (note that the database will change depending
  on which package(s) you query.

rosdep keys <packages>...
  will list the rosdep keys that the packages depend on.

rosdep what-needs <rosdeps>...
  will print a list of packages that declare a rosdep on (at least
  one of) <rosdeps>

rosdep where-defined <rosdeps>...
  will print a list of yaml files that declare a rosdep on (at least
  one of) <rosdeps>
"""

def _get_default_RosdepLookup():
    return RosdepLookup.create_from_rospkg()

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
Missing resource: %s
"""%(e.args[0]))
        sys.exit(1)
    except UsageError as e:
        print(_usage, file=sys.stderr)
        print("ERROR: %s"%(str(e)), file=sys.stderr)
        sys.exit(os.EX_USAGE)
    except RosdepInternalError as e:
        print("""
ERROR: Rosdep experienced an internal error.
Please go to the rosdep page [1] and file a bug report with the message below.
[1] : http://www.ros.org/wiki/rosdep

%s
"""%(e.message), file=sys.stderr)
        sys.exit(1)
    except ResolutionError as e:
        print("""
ERROR: %s

%s
"""%(e.message, e), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print("""
ERROR: Rosdep experienced an internal error: %s
Please go to the rosdep page [1] and file a bug report with the stack trace below.
[1] : http://www.ros.org/wiki/rosdep

%s
"""%(e, traceback.format_exc(e)), file=sys.stderr)
        sys.exit(1)
        
def _rosdep_main(args):
    parser = OptionParser(usage=_usage, prog='rosdep')
    parser.add_option("--os", dest="os_override", default=None, 
                      metavar="OS_NAME:OS_VERSION", help="Override OS name and version (colon-separated), e.g. ubuntu:lucid")
    parser.add_option("--verbose", "-v", dest="verbose", default=False, 
                      action="store_true", help="verbose display")
    parser.add_option("--reinstall", dest="reinstall", default=False, 
                      action="store_true", help="(re)install all dependencies, even if already installed")
    parser.add_option("--include_duplicates", "-i", dest="include_duplicates", default=False, 
                      action="store_true", help="do not deduplicate")
    parser.add_option("--default-yes", "-y", dest="default_yes", default=False, 
                      action="store_true", help="Tell the package manager to default to y or fail when installing")
    parser.add_option("--simulate", "-s", dest="simulate", default=False, 
                      action="store_true", help="Simulate install")
    parser.add_option("-r", dest="robust", default=False, 
                      action="store_true", help="Continue installing despite errors.")
    parser.add_option("-a", "--all", dest="rosdep_all", default=False, 
                      action="store_true", help="select all packages")

    options, args = parser.parse_args(args)

    if len(args) == 0:
        parser.error("Please enter a command")
    command = args[0]
    if not command in _commands:
        parser.error("Unsupported command %s."%command)
    if len(args) < 2 and not options.rosdep_all:
        parser.error("Please enter arguments for '%s'"%command)
    args = args[1:]

    if command in _command_rosdep_args:
        return _rosdep_args_handler(command, parser, options, args)
    else:
        return _package_args_handler(command, parser, options, args)

def _rosdep_args_handler(command, parser, options, args):
    # rosdep keys as args
    if options.rosdep_all:
        parser.error("-a, --all is not a valid option for this command")
    else:
        return command_handlers[command](args, options)
    
def _package_args_handler(command, parser, options, args, rospack=None, rosstack=None):
    # package names as args
    # - overrides to enable testing
    if rospack is None:
        rospack = rospkg.RosPack()
    if rosstack is None:
        rosstack = rospkg.RosStack()
    lookup = RosdepLookup.create_from_rospkg(rospack=rospack, rosstack=rosstack)
    loader = lookup.get_loader()
    
    if options.rosdep_all:
        if args:
            parser.error("cannot specify additional arguments with -a")
        else:
            # we don't use get_loadable b/c here we know we want all packages
            args = rospack.list()
    if not args:
        parser.error("no packages or stacks specified")

    val = rospkg.expand_to_packages(args, rospack, rosstack)
    packages = val[0]
    not_found = val[1]
    if not_found:
        raise rospkg.ResourceNotFound(not_found[0], rospack.get_ros_paths())

    if not packages:
        # possible with empty stacks
        print("No packages in arguments, aborting")
        return

    return command_handlers[command](lookup, packages, options)

def configure_installer_context_os(installer_context, options):
    """
    Override the OS detector in *installer_context* if necessary.

    :raises: :exc:`UsageError` If user input options incorrectly
    """
    if not options.os_override:
        return
    val = options.os_override
    if not ':' in val:
        raise UsageError("OS override must be colon-separated OS_NAME:OS_VERSION, e.g. ubuntu:maverick")
    os_name = val[:val.find(':')]
    os_version = val[val.find(':')+1:]
    installer_context.set_os_override(os_name, os_version)
    
def command_keys(lookup, packages, options):
    lookup = _get_default_RosdepLookup()
    rosdep_keys = []
    for package_name in packages:
        rosdep_keys.extend(lookup.get_rosdeps(package_name, implicit=True))

    _print_lookup_errors(lookup)
    print('\n'.join(set(rosdep_keys)))

def command_check(lookup, packages, options):
    verbose = options.verbose
    
    installer_context = create_default_installer_context(verbose=verbose)
    configure_installer_context_os(installer_context, options)
    installer = RosdepInstaller(installer_context, lookup)

    uninstalled, errors = installer.get_uninstalled(packages, verbose=verbose)

    # pretty print the result
    if [r for r in uninstalled.values() if r]:
        print("System dependencies have not been satisified:")
        for installer_key, resolved in uninstalled.items():
            if resolved:
                for r in resolved:
                    print("%s\t%s"%(installer_key, r))
    else:
        print("All system dependencies have been satisified")
    if errors:
        for package_name, ex in errors.items():
            if isinstance(ex, rospkg.ResourceNotFound):
                print("ERROR[%s]: resource not found [%s]"%(package_name, ex.args[0]), file=sys.stderr)
            else:
                print("ERROR[%s]: %s"%(package_name, str(ex)), file=sys.stderr)                
    if uninstalled:
        return 1
    else:
        return 0

def command_install(lookup, packages, options):
    # map options
    install_options = dict(interactive=not options.default_yes, verbose=options.verbose,
                           reinstall=options.reinstall,
                           continue_on_error=options.robust, simulate=options.simulate)

    # setup installer
    installer_context = create_default_installer_context(verbose=options.verbose)
    configure_installer_context_os(installer_context, options)
    installer = RosdepInstaller(installer_context, lookup)

    if options.reinstall:
        uninstalled, errors = lookup.resolve_all(packages, installer_context)
    else:
        uninstalled, errors = installer.get_uninstalled(packages, verbose=options.verbose)
    if errors:
        print("TODO: deal with errors in resolution: %s"%(errors), file=sys.stderr)
        raise Exception("TODO")
    try:
        installer.install(uninstalled, **install_options)
        if not options.simulate:
            print("#All required rosdeps installed successfully")
        return 0
    except KeyError as e:
        raise RosdepInternalError(e)
    except InstallFailed as e:
        print("ERROR: the following rosdeps failed to install", file=sys.stderr)
        print('\n'.join(["  [%s]: %s"%f for f in e.failures]), file=sys.stderr)
        return 1

def _compute_depdb_output(lookup, packages, options):
    installer_context = create_default_installer_context(verbose=options.verbose)
    os_name, os_version = _detect_os(installer_context, options)
    
    output = "Rosdep dependencies for operating system %s version %s "%(os_name, os_version)
    for stack_name in stacks:
        output += "\nSTACK: %s\n"%(stack_name)
        view = lookup.get_stack_rosdep_view(stack_name)
        for rosdep in view.keys():
            definition = view.lookup(rosdep)
            resolved = resolve_definition(definition, os_name, os_version)
            output = output + "<<<< %s -> %s >>>>\n"%(rosdep, resolved)
    return output
    
def command_depdb(lookup, packages, options):
    #TODO: get verified_packages from r
    print(_compute_depdb_output(r, args, options))
    return 0

def _print_lookup_errors(lookup):
    for error in lookup.get_errors():
        if isinstance(error, rospkg.ResourceNotFound):
            print("WARNING: unable to locate resource %s"%(str(error.args[0])), file=sys.stderr)
        else:
            print("WARNING: %s"%(str(error)), file=sys.stderr)
            
def command_what_needs(args, options):
    lookup = _get_default_RosdepLookup()
    packages = []
    for rosdep_name in args:
        packages.extend(lookup.get_resources_that_need(rosdep_name))

    _print_lookup_errors(lookup)
    print('\n'.join(set(packages)))
    
def command_where_defined(args, options):
    lookup = _get_default_RosdepLookup()
    locations = []
    for rosdep_name in args:
        locations.extend(lookup.get_views_that_define(rosdep_name))

    _print_lookup_errors(lookup)
    if locations:
        for location in locations:
            origin = location[1]
            print(origin)
    else:
        print("ERROR: cannot find definition(s) for [%s]"%(', '.join(args)), file=sys.stderr)
        sys.exit(1)

def command_resolve(args, options):
    lookup = _get_default_RosdepLookup()


    installer_context = create_default_installer_context(verbose=options.verbose)
    configure_installer_context_os(installer_context, options)
    

    os_name, os_version = installer_context.get_os_name_and_version()

    try:
        installer_keys = installer_context.get_os_installer_keys(os_name)
        default_key = installer_context.get_default_os_installer_key(os_name)
    except KeyError:
        raise ResolutionError(rosdep_key, definition.data, os_name, os_version, "Unsupported OS [%s]"%(os_name))

    installer = installer_context.get_installer(default_key)


    #definition.get_rule_for_platform(os_name, os_version, installer_keys, default_key)

    packages = []
    view_names = []
    for rosdep_name in args:
        view_names = lookup.get_views_that_define(rosdep_name)
        
        if not view_names:
            raise ResolutionError(rosdep_name, None, os_name, os_version, "Could not find definition for rosdep [%s]"%rosdep_name)
        view = lookup.get_rosdep_view_for_resource(view_names[0][0]) # taking the first one #TODO FIXME
        
        d = view.lookup(rosdep_name)

        


        inst_key, rule = d.get_rule_for_platform(os_name, os_version, installer_keys, default_key)

        resolved = installer.resolve(rule)
        print (" ".join(resolved))

        #print("rule is %s"%rule)
    for error in lookup.get_errors():
        print("WARNING: %s"%(str(error)), file=sys.stderr)

    
        
    

command_handlers = {
    'db': command_depdb,
    'check': command_check,
    'keys': command_keys,
    'install': command_install,
    'what-needs': command_what_needs,
    'where-defined': command_where_defined,
    'resolve': command_resolve,

    # backwards compat
    'what_needs': command_what_needs,
    'where_defined': command_where_defined,
    'depdb': command_depdb, 
    }

# commands that accept rosdep names as args
_command_rosdep_args = ['what-needs', 'what_needs', 'where-defined', 'where_defined', 'resolve']

_commands = command_handlers.keys()



