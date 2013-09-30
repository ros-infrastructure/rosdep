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

import os
import subprocess

from ..installers import PackageManagerInstaller
from .source import SOURCE_INSTALLER

ARCH_OS_NAME = 'arch'
PACMAN_INSTALLER = 'pacman'
AUR_INSTALLER = 'aur'

def register_installers(context):
    context.set_installer(PACMAN_INSTALLER, PacmanInstaller())

    # Is this the right place to do this kind of check?
    aur_tool = detect_aur_tool()
    if aur_tool is not None:
        context.set_installer(AUR_INSTALLER, AURInstaller(aur_tool))
    
def register_platforms(context):
    context.add_os_installer_key(ARCH_OS_NAME, SOURCE_INSTALLER)
    context.add_os_installer_key(ARCH_OS_NAME, PACMAN_INSTALLER)
    context.add_os_installer_key(ARCH_OS_NAME, AUR_INSTALLER)
    context.set_default_os_installer_key(ARCH_OS_NAME, PACMAN_INSTALLER)

def pacman_detect_single(p):
    return not subprocess.call(['pacman', '-Q', p], stdout=subprocess.PIPE, stderr=subprocess.PIPE)    

def pacman_detect(packages):
    return [p for p in packages if pacman_detect_single(p)]

class PacmanInstaller(PackageManagerInstaller):

    def __init__(self):
        super(PacmanInstaller, self).__init__(pacman_detect)

    def get_install_command(self, resolved, interactive=True, reinstall=False):
        #TODO: interactive switch
        packages = self.get_packages_to_install(resolved, reinstall=reinstall)        
        if not packages:
            return []
        else:
            return [['sudo', 'pacman', '-Sy', '--needed', p] for p in packages]

def detect_aur_tool():
    tool_names = ['packer', 'yaourt']

    for path in os.environ['PATH'].split(os.pathsep):
        for tool_name in tool_names:
            if os.path.exists(os.path.join(path, tool_name)):
                return tool_name

class AURInstaller(PackageManagerInstaller):

    def __init__(self, aur_tool):
        super(AURInstaller, self).__init__(pacman_detect)
        self.aur_tool = aur_tool

    def get_install_command(self, resolved, interactive=True, reinstall=False):
        #TODO: interactive switch
        packages = self.get_packages_to_install(resolved, reinstall=reinstall)
        if not packages:
            return []
        else:
            if self.aur_tool == 'packer':
                return [['sudo', 'packer', '-S', p] for p in packages]
            elif self.aur_tool == 'yaourt':
                # TODO: Test this...
                return [['sudo', 'yaourt', '-S', p] for p in packages]
