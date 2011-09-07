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

_usage = """usage: rosdep [options] <command> <args>

Commands:

rosdep generate_bash  <packages>...
rosdep satisfy <packages>...
  will try to generate a bash script which will satisfy the 
  dependencies of package(s) on your operating system.

rosdep install <packages>...
  will generate a bash script and then execute it.

rosdep depdb <packages>...
  will generate the dependency database for package(s) and print
  it to the console (note that the database will change depending
  on which package(s) you query.

rosdep what_needs <rosdeps>...
  will print a list of packages that declare a rosdep on (at least
  one of) ROSDEP_NAME[S]

rosdep where_defined <rosdeps>...
  will print a list of yaml files that declare a rosdep on (at least
  one of) ROSDEP_NAME[S]

rosdep check <packages>...
  will check if the dependencies of package(s) have been met.
"""

def rosdep_main():
    try:
        _rosdep_main()
    except Exception as e:
        print("ERROR: %s"%e, file=sys.stderr)
        return 1
        
def _rosdep_main():
    from optparse import OptionParser
    parser = OptionParser(usage=_usage, prog='rosdep')
    parser.add_option("--verbose", "-v", dest="verbose", default=False, 
                      action="store_true", help="verbose display")
    parser.add_option("--include_duplicates", "-i", dest="include_duplicates", default=False, 
                      action="store_true", help="do not deduplicate")
    parser.add_option("--default-yes", "-y", dest="default_yes", default=False, 
                      action="store_true", help="Tell the package manager to default to y or fail when installing")
    parser.add_option("-r", dest="robust", default=False, 
                      action="store_true", help="Continue installing despite errors.")
    parser.add_option("-a", "--all", dest="rosdep_all", default=False, 
                      action="store_true", help="select all packages")

    options, args = parser.parse_args()

    if len(args) == 0:
        parser.error("Please enter a command")
    command = args[0]
    if not command in _commands:
        parser.error("Unsupported command %s."%command)
    if len(args) < 2 and not options.rosdep_all:
        parser.error("Please enter arguments for '%s'"%command)
    args = args[1:]

    if command in _command_rosdep_args: # rosdep keys as args
        if options.rosdep_all:
            parser.error("-a, --all is not a valid option for this command")
        return command_handlers[command](args, options)
    else:
        # package names as args
        if options.rosdep_all:
            args = loader.get_loadable_packages()
        
        verified_packages, rejected_packages = roslib.stacks.expand_to_packages(args)
        valid_stacks = [s for s in roslib.stacks.list_stacks() if s in args]
    
        if len(rejected_packages) > 0:
            print("Warning: could not identify %s as a package"%rejected_packages, file=sys.stderr)
        if len(verified_packages) == 0 and len(valid_stacks) == 0:
            parser.error("No Valid Packages or stacks listed as arguments")
                
        return command_handlers[command](args, verified_packages, options)

def _get_default_RosdepLookup():
    from .lookup import RosdepLookup
    return RosdepLookup.create_from_rospkg()

def _compute_depdb_output(args, options):
    lookup = _get_default_RosdepLookup()

    # detect OS
    # TODO: allow command-line override of os name and version
    os_name = os_version = "TODO"
    
    
    output = "Rosdep dependencies for operating system %s version %s "%(os_name, os_version)
    for stack_name in stacks:
        output += "\nSTACK: %s\n"%(stack_name)
        view = lookup.get_rosdep_view(stack_name)
        for rosdep in view.keys():
            definition = view.lookup(rosdep)
            resolved = resolve_definition(definition, os_name, os_version)
            output = output + "<<<< %s -> %s >>>>\n"%(rosdep, resolved)
    return output
    
def command_depdb(r, args, options):
    #TODO: get verified_packages from r
    print(_compute_depdb_output(r, args, options))
    return 0

def command_what_needs(args, options):
    lookup = _get_default_RosdepLookup()
    packages = []
    for rosdep_name in args:
        packages.extend(lookup.what_needs(rosdep_name))

    for error in lookup.get_errors():
        print("WARNING: %s"%(str(error)), file=sys.stderr)

    print('\n'.join(set(packages)))
    
def command_where_defined(args, options):
    lookup = _get_default_RosdepLookup()
    locations = []
    for rosdep_name in args:
        locations.extend(lookup.where_defined(rosdep_name))

    for error in lookup.get_errors():
        print("WARNING: %s"%(str(error)), file=sys.stderr)

    for location in locations:
        origin = location[1]
        print(origin)

def command_check(r, args, options):
    missing_packages = r.check()
    if len(rejected_packages) > 0:
        print("Arguments %s are not packages"%rejected_packages, file=sys.stderr)
        return  1
    if len(missing_packages) == 0:
        print("All required rosdeps are installed")
        return 0
    else:
        print("The following rosdeps were not installed", missing_packages)
        return 1

def command_install(r, args, verified_packages, options):
    error = r.install(options.include_duplicates, options.default_yes)
    if error:
        print("rosdep install ERROR:\n%s"%error, file=sys.stderr)
        return 1
    else:
        print("All required rosdeps installed successfully")
        return 0
    
def command_generate_bash(r, options):
    missing_packages = r.satisfy()
    if not missing_packages:
        return 0
    else:
        print("The following rosdeps are not installed but are required", missing_packages)
        return 1
        
command_handlers = {
    'debdb': command_depdb,
    'check': command_check,
    'install': command_install,
    'generate_bash': command_generate_bash,
    'satisfy': command_generate_bash,
    'what_needs': command_what_needs,
    'where_defined': command_where_defined,
    }

# commands that accept rosdep names as args
_command_rosdep_args = ['what_needs', 'where_defined']

_commands = command_handlers.keys()



