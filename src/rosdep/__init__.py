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

ENABLE_CYGWIN = False
ENABLE_OSX    = False
ENABLE_PIP    = False

from .installers import InstallerContext

def create_default_installer_context():
    if ENABLE_CYGWIN:
        from .platforms import cygwin
    from .platforms import debian
    if ENABLE_OSX:
        from .platforms import osx
    if ENABLE_PIP:
        from .platforms import pip    

    context = InstallerContext()

    # setup installers
    if ENABLE_CYGWIN:
        cygwin.register_installers(context)
    debian.register_installers(context)
    if ENABLE_OSX:
        osx.register_installers(context)
    if ENABLE_PIP:        
        pip.register_installers(context)

    # setup platforms
    debian.register_debian(context)
    debian.register_ubuntu(context)
    debian.register_mint(context)

    if ENABLE_CYGWIN:
        cygwin.register_cygwin(context)
    if ENABLE_OSX:
        osx.register_osx(context)
        #TODO: register brew
        
    return context

