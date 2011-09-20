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

import os

from rospkg.os_detect import OS_GENTOO

from .source import SOURCE_INSTALLER
from ..installers import PackageManagerInstaller
from ..shell_utils import create_tempfile_from_string_and_execute, read_stdout

EQUERY_INSTALLER = 'equery'

def register_installers(context):
    context.set_installer(EQUERY_INSTALLER, EqueryInstaller())

def register_platforms(context):
    context.add_os_installer_key(OS_GENTOO, EQUERY_INSTALLER)
    context.add_os_installer_key(OS_GENTOO, SOURCE_INSTALLER)
    context.set_default_os_installer_key(OS_GENTOO, EQUERY_INSTALLER)

# Determine whether package p needs to be installed
def equery_detect_single(p):
    std_out = read_stdout(['equery', '-q', 'l', p])
    return std_out.count("") == 1

def equery_detect(packages):
    return [p for p in packages if equery_detect_single(p)]

# Check equery for existence and compatibility (gentoolkit 0.3)
def equery_available():
    if not os.path.exists("/usr/bin/equery"):
        return False
    std_out = read_stdout(['equery', '-V'])
    return "0.3." == stdout[8:12]

class EqueryInstaller(PackageManagerInstaller):

    def __init__(self):
        super(EqueryInstaller, self).__init__(equery_detect)
        
    def get_install_command(self, resolved, interactive=True, reinstall=False):
        packages = self.get_packages_to_install(resolved, reinstall=reinstall)        
        #TODO: interactive
        if not packages:
            return []
        elif equery_available():
            return [['sudo', 'emerge', p] for p in packages]
        else:
            return [['sudo', 'emerge', '-u', p] for p in packages]
