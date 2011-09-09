# Copyright (c) 2011, Willow Garage, Inc.
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

from __future__ import print_function

import os
import sys

def test_InstallerContext_ctor():
    from rosdep.installers import InstallerContext
    from rospkg.os_detect import OsDetect

    context = InstallerContext()
    assert context.get_os_detect() is not None
    assert isinstance(context.get_os_detect(), OsDetect)

    detect = OsDetect()
    context = InstallerContext(detect)
    assert context.get_os_detect() == detect
    assert {} == context.get_installer_keys()
    assert {} == context.get_os_installer_keys()

def test_InstallerContext_installers():
    from rosdep.installers import InstallerContext
    detect = OsDetect()
    context = InstallerContext(detect)
    
    
def register_installers(context):
    context.register_installer(APT_INSTALLER, AptInstaller)

def register_debian(context):
    context.register_os_installer(OS_DEBIAN, APT_INSTALLER)
    context.register_os_installer(OS_DEBIAN, PIP_INSTALLER)
    context.register_os_installer(OS_DEBIAN, SOURCE_INSTALLER)
    context.set_default_os_installer(OS_DEBIAN, APT_INSTALLER)
    
def register_ubuntu(context):
    context.register_os_installer(OS_UBUNTU, APT_INSTALLER)
    context.register_os_installer(OS_UBUNTU, PIP_INSTALLER)
    context.register_os_installer(OS_UBUNTU, SOURCE_INSTALLER)
    context.set_default_os_installer(OS_UBUNTU, APT_INSTALLER)

def register_mint(context):
    # override mint detector with different version info
    detector = OsDetect().get_detector(OS_MINT)
    context.set_os_detector(OS_MINT, MintOsDetect(detector))
    
    context.register_os_installer(OS_MINT, APT_INSTALLER)
    context.register_os_installer(OS_MINT, PIP_INSTALLER)
    context.register_os_installer(OS_MINT, SOURCE_INSTALLER)
    context.set_default_os_installer(OS_MINT, APT_INSTALLER)
    
