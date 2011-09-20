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

from rospkg.os_detect import OS_RHEL, OS_FEDORA

from .source import SOURCE_INSTALLER
from ..installers import PackageManagerInstaller

# yum package manager key
YUM_INSTALLER='yum'

def register_installers(context):
    context.set_installer(YUM_INSTALLER, YumInstaller())

def register_platforms(context):
    register_fedora(context)
    register_rhel(context)
    
def register_fedora(context):
    context.add_os_installer_key(OS_FEDORA, YUM_INSTALLER)
    context.add_os_installer_key(OS_FEDORA, SOURCE_INSTALLER)
    context.set_default_os_installer_key(OS_FEDORA, YUM_INSTALLER)

def register_rhel(context):
    context.add_os_installer_key(OS_RHEL, YUM_INSTALLER)
    context.add_os_installer_key(OS_RHEL, SOURCE_INSTALLER)
    context.set_default_os_installer_key(OS_RHEL, YUM_INSTALLER)

def rpm_detect(packages):
    return subprocess.call(['rpm', '-q', packages], stdout=subprocess.PIPE, stderr=subprocess.PIPE)    

class YumInstaller(PackageManagerInstaller):
    """
    This class provides the functions for installing using yum
    it's methods partially implement the Rosdep OS api to complement 
    the roslib.OSDetect API.
    """

    def __init__(self):
        super(YumInstaller, self).__init__(rpm_detect)

    def get_install_command(self, resolved, interactive=True, reinstall=False):
        packages = self.get_packages_to_install(resolved, reinstall=reinstall)
        if not packages:
            return []
        elif not interactive:
            return [['sudo', 'yum', '-y', 'install', p] for p in packages]
        else:
            return [['sudo', 'yum', 'install', p] for p in packages]

