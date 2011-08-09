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

"""
rosdep command-line tool
"""
from rosdep.main import main


ENABLE_CYGWIN = False
ENABLE_DEBIAN = True
ENABLE_OSX    = True
ENABLE_PIPE   = True

def default_init():
    if ENABLE_CYGWIN:
        import .platforms.cygwin
    if ENABLE_DEBIAN:
        import .platforms.debian
    if ENABLE_OSX:
        import .platforms.osx
    if ENABLE_PIP:
        import .platforms.pip    

    context = RosdepContext()

    # setup installers
    if ENABLE_CYGWIN:
        .platforms.cygwin.register_installers(context)
    if ENABLE_DEBIAN:
        .platforms.debian.register_installers(context)
    if ENABLE_OSX:
        .platforms.osx.register_installers(context)
    if ENABLE_PIP:        
        .platforms.pip.register_installers(context)

    # setup platforms
    if ENABLE_DEBIAN:
        .platforms.debian.register_debian(context)
        .platforms.debian.register_ubuntu(context)
        .platforms.debian.register_mint(context)
    if ENABLE_CYGWIN:
        .platforms.cygwin.register_cygwin(context)
    if ENABLE_OSX:
        .platforms.osx.register_osx(context)
        #TODO: register brew
        
    return context

