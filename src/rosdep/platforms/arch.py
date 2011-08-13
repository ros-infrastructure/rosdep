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

from ..installers import PackageManagerInstaller, SOURCE_INSTALLER

ARCH_OS_NAME = 'arch'
PACMAN_INSTALLER = 'pacman'

def register_installers(context):
    context.register_installer(PACMAN_INSTALLER, PacmanInstaller)
    
def register_cygwin(context):
    context.register_os_installer(ARCH_OS_NAME, SOURCE_INSTALLER)
    context.register_os_installer(ARCH_OS_NAME, PACMAN_INSTALLER)
    context.set_default_os_installer(ARCH_OS_NAME, PACMAN_INSTALLER)

def pacman_detect(p):
    return subprocess.call(['pacman', '-Q', p], stdout=subprocess.PIPE, stderr=subprocess.PIPE)    

class Pacman(PackageManagerInstaller):

    def __init__(self):
        #TODO: need to pull out package list from rule
        super(Pacman, self).__init__(packages, pacman_detect)

    def generate_package_install_command(self, default_yes=False, execute=True, display=True):
        packages_to_install = self.get_packages_to_install()
        return "#Packages\nsudo pacman -Sy --needed " + ' '.join(packages_to_install)
