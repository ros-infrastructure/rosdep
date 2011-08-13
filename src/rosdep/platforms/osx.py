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

# Author Tully Foote/tfoote@willowgarage.com, Ken Conley

import os

from .pip import PIP_INSTALLER
from ..installers import Installer, SOURCE_INSTALLER
from ..shell_utils import create_tempfile_from_string_and_execute, read_stdout

OSX_OS_NAME = 'osx'
OSXBREW_OS_NAME = 'osxbrew'

BREW_INSTALLER = 'brew'
MACPORTS_INSTALLER = 'macports'

def port_detect(p):
    std_out = read_stdout(['port', 'installed', p])
    return std_out.count("(active)") > 0

def register_installers(context):
    context.register_installer(MACPORTS_INSTALLER, MacPortsInstaller)

def register_osx(context):
    context.register_os_installer(OSX_OS_NAME, MACPORTS_INSTALLER)
    context.register_os_installer(OSX_OS_NAME, PIP_INSTALLER)
    context.register_os_installer(OSX_OS_NAME, SOURCE_INSTALLER)
    context.set_default_os_installer(OSX_OS_NAME, MACPORTS_INSTALLER)

def register_osxbrew(context):
    context.register_os_installer(OSXBREW_OS_NAME, PIP_INSTALLER)
    context.register_os_installer(OSXBREW_OS_NAME, SOURCE_INSTALLER)
    context.set_default_os_installer(OSXBREW_OS_NAME, BREW_INSTALLER)
    raise NotImplemented

class MacportsInstaller(Installer):
    """ 
    An implementation of the InstallerAPI for use on macports systems.
    """
    def __init__(self, arg_dict):
        packages = arg_dict.get("packages", "")
        if type(packages) == type("string"):
            packages = packages.split()

        self.packages = packages

    def get_packages_to_install(self):
         return list(set(self.packages) - set(self.port_detect(self.packages)))

    def check_presence(self):
        return len(self.get_packages_to_install()) == 0

    def generate_package_install_command(self, default_yes = False, execute = True, display = True):
        script = '!#/bin/bash\n#no script'
        packages_to_install = self.get_packages_to_install()
        if not packages_to_install:
            script =  "#!/bin/bash\n#No Packages to install"
        script = "#!/bin/bash\n#Packages %s\nsudo port install "%packages_to_install + ' '.join(packages_to_install)        

        if execute:
            return rosdep.core.create_tempfile_from_string_and_execute(script)
        elif display:
            print "To install packages: %s would have executed script\n{{{\n%s\n}}}"%(packages_to_install, script)
        return False


class Osx(roslib.os_detect.Osx, rosdep.base_rosdep.RosdepBaseOS):

    def strip_detected_packages(self, packages):
        return [p for p in packages if not port_detect(p)] 

