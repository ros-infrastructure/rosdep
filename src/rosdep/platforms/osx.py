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

from rospkg.os_detect import OS_OSX

from .pip import PIP_INSTALLER
from .source import SOURCE_INSTALLER
from ..installers import Installer, PackageManagerInstaller
from ..shell_utils import create_tempfile_from_string_and_execute, read_stdout

# add additional os names for brew, macports (TODO)
OSXBREW_OS_NAME = 'osxbrew'

BREW_INSTALLER = 'brew'
MACPORTS_INSTALLER = 'macports'

def port_detect(p):
    std_out = read_stdout(['port', 'installed', p])
    return std_out.count("(active)") > 0

def register_installers(context):
    context.set_installer(MACPORTS_INSTALLER, MacportsInstaller)

def register_platforms(context):
    register_osx(context)
    #register_osxbrew(context)
    
def register_osx(context):
    context.add_os_installer_key(OS_OSX, MACPORTS_INSTALLER)
    context.add_os_installer_key(OS_OSX, PIP_INSTALLER)
    context.add_os_installer_key(OS_OSX, SOURCE_INSTALLER)
    context.set_default_os_installer_key(OS_OSX, MACPORTS_INSTALLER)

def register_osxbrew(context):
    context.add_os_installer_key(OSXBREW_OS_NAME, PIP_INSTALLER)
    context.add_os_installer_key(OSXBREW_OS_NAME, SOURCE_INSTALLER)
    context.set_default_os_installer_key(OSXBREW_OS_NAME, BREW_INSTALLER)
    raise NotImplemented

class MacportsInstaller(PackageManagerInstaller):
    """ 
    An implementation of the :class:`Installer` API for use on
    macports systems.
    """
    def __init__(self):
        super(MacPortsInstaller, self).__init__(port_detect)

    def get_install_command(self, resolved, interactive=True):
        packages = self.get_packages_to_install(resolved)
        if not packages:
            return "#!/bin/bash\n#No Packages to install"
        else:
            #TODO: interactive
            return "#!/bin/bash\n#Packages %s\nsudo port install %s"%(packages, ' '.join(packages))
