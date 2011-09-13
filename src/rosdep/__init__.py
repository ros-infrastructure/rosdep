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

# Author Tully Foote/tfoote@willowgarage.com, Ken Conley/kwc@willowgarage.com

"""
rosdep library and command-line tool
"""

from .installers import InstallerContext, Installer, PackageManagerInstaller

from .model import InvalidRosdepData, RosdepDatabase, RosdepDatabaseEntry
from .lookup import RosdepDefinition, RosdepConflict, RosdepView, RosdepLookup
from .loader import RosdepLoader
from .rospkg_loader import RosPkgLoader

def create_default_installer_context():
    from .platforms import arch
    from .platforms import cygwin
    from .platforms import debian
    from .platforms import gentoo
    from .platforms import opensuse
    from .platforms import osx
    from .platforms import pip
    from .platforms import redhat
    from .platforms import source
    
    platform_mods = [arch, cygwin, debian, gentoo, opensuse, osx]
    installer_mods = [source, pip] + platform_mods

    context = InstallerContext()

    # setup installers
    for m in installer_mods:
        m.register_installers(context)

    # setup platforms
    for m in platform_mods:
        m.register_platforms(context)

    return context

