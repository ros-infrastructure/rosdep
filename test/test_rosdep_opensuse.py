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

# Author Ken Conley/kwc@willowgarage.com

import os
import traceback
from mock import patch

def get_test_dir():
    # not used yet
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'opensuse'))

def test_ZypperInstaller():
    from rosdep2.platforms.opensuse import ZypperInstaller

    @patch.object(ZypperInstaller, 'get_packages_to_install')
    def test(mock_method):
        installer = ZypperInstaller()
        mock_method.return_value = []
        assert [] == installer.get_install_command(['fake'])

        # no interactive option with YUM
        mock_method.return_value = ['a', 'b']
        expected = [['sudo', '-H', 'zypper', 'install', '-yl', 'a', 'b']]
        val = installer.get_install_command(['whatever'], interactive=False)
        assert val == expected, val
        expected = [['sudo', '-H', 'zypper', 'install', 'a', 'b']]
        val = installer.get_install_command(['whatever'], interactive=True)
        assert val == expected, val
    try:
        test()
    except AssertionError:
        traceback.print_exc()
        raise
    
