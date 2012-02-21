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
#
# Author Murph Finnicum/murph@murph.cc

import os

from rospkg.os_detect import OS_GENTOO

from .source import SOURCE_INSTALLER
from ..model import InvalidData
from ..installers import PackageManagerInstaller
from ..shell_utils import create_tempfile_from_string_and_execute, read_stdout

from types import ListType

PORTAGE_INSTALLER = 'portage'

def register_installers(context):
    context.set_installer(PORTAGE_INSTALLER, PortageInstaller())

def register_platforms(context):
    context.add_os_installer_key(OS_GENTOO, PORTAGE_INSTALLER)
    context.add_os_installer_key(OS_GENTOO, SOURCE_INSTALLER)
    context.set_default_os_installer_key(OS_GENTOO, PORTAGE_INSTALLER)

# Determine whether package p with USE flags u needs to be installed
def portage_detect_single(package, use_flags, exec_fn = read_stdout ):
    """ 
    Check if a given package is installed with satisfactory use_flags
    
    :param exec_fn: function to execute Popen and read stdout (for testing)
    """

    atom = package
    if use_flags:
        atom = atom + "[" + ",".join(use_flags) + "]"

    std_out = exec_fn(['portageq', 'match', '/', atom])

    # TODO consdier checking the name of the package returned
    # Also, todo, figure out if just returning true if two packages are returned is cool..
    return len(std_out) >= 1

def portage_detect(packages, use_flags, exec_fn = read_stdout):
    """
    Given a list of packages, return the list of installed packages.

    :param exec_fn: function to execute Popen and read stdout (for testing)
    """

    # This is for testing, to make sure they're always checked in the same order
    if isinstance(packages, ListType):
        packages.sort()
    
    return [p for p in packages if portage_detect_single(p, use_flags, exec_fn)]

# Check portage and needed tools for existence and compatibility
def portage_available():
    if not os.path.exists("/usr/bin/portageq"):
        return False

    if not os.path.exists("/usr/bin/emerge"):
        return False

    # We only use standard, defined portage features.
    # They work in all released versions of portage, and should work in
    # future versionf for a long time to come.
    # but .. TODO: Check versions

    return True

class PortageInstaller(PackageManagerInstaller):

    def __init__(self):
        super(PortageInstaller, self).__init__(portage_detect)
        
        
    def get_install_command(self, resolved, interactive=True, reinstall=False):
        packages = self.get_packages_to_install(resolved, reinstall=reinstall)      

        #TODO: interactive
        if not packages:
            return []
        elif interactive:
            return [['sudo', 'emerge', '-a', p] for p in packages]
        else:
            return [['sudo', 'emerge', p] for p in packages]


    def resolve_use_flags(self, rosdep_args): 
        """ 
        :returns: list of use flags that are required
        """

        if type(rosdep_args) == dict:
            use_flags = rosdep_args.get("use", None)

            if type(use_flags) == type("string"):
                use_flags = [use_flags]
            elif type(use_flags) == type([]):
                use_flags = use_flags
            elif type(use_flags) == type(None):
                use_flags = use_flags
            else:
                print("Invalid 'use' argument in rosdep file.")
                use_flags = None
                raise InvalidData("Invalid 'use' in rosdep args: %s"%(rosdep_args))
        else:
            use_flags = None;

        self.use_flags = use_flags
        

    def resolve(self, rosdep_args):
        self.resolve_use_flags(rosdep_args)
        return PackageManagerInstaller.resolve(self, rosdep_args)

    def get_packages_to_install(self, resolved, reinstall=False):
        if reinstall:
            return resolved
        if not resolved:
            return []
        else:
            return list(set(resolved) - set(self.detect_fn(resolved, self.use_flags)))
