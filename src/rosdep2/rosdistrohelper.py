# Copyright (c) 2013, Open Source Robotics Foundation
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

# Author Paul Mathieu/paul@osrfoundation.org

import rosdistro
import warnings

class PreRep137Warning(UserWarning):
    pass

class RDCache:
    index_url = None
    index = None
    release_files = {}

def _check_cache():
    if RDCache.index_url != rosdistro.get_index_url():
        RDCache.index_url = rosdistro.get_index_url()
        RDCache.index = None
        RDCache.release_files = {}


def get_index():
    _check_cache()
    if RDCache.index is None:
        RDCache.index = rosdistro.get_index(RDCache.index_url)
    return RDCache.index

def get_release_file(distro):
    _check_cache()
    if distro not in RDCache.release_files:
        RDCache.release_files[distro] = rosdistro.get_release_file(get_index(), distro)
    return RDCache.release_files[distro]

def get_targets():
    return dict((d, get_release_file(d).platforms) for d in get_index().distributions)
