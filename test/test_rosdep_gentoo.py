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

# Author Ken Conley/kwc@willowgarage.com, Murph Finnicum/murph@murph.cc

import os
import traceback
from mock import Mock, patch

import rospkg.os_detect

def is_gentoo():
    return rospkg.os_detect.Gentoo().is_os()

def get_test_dir():
    # not used yet
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'gentoo'))

# Requires 2.7 @unittest.skipIf(not rospkg.os_detect.Gentoo().is_os(), "not running Gentoo")
def test_portage_available():
    if not is_gentoo():
        print("Skipping not Gentoo")
        return 
    from rosdep2.platforms.gentoo import portage_available

    original_exists = os.path.exists

    path_overrides = {}
    def mock_path(path):
        if path in path_overrides:
            return path_overrides[path]
        else: 
            return original_exists(path)

    m = Mock(side_effect=mock_path)
    os.path.exists = m

    #Test with portageq missing
    m.reset_mock()
    path_overrides = {}
    path_overrides['/usr/bin/portageq'] = False
    path_overrides['/usr/bin/emerge'] = True

    val = portage_available()
    assert val==False, "Portage should not be available without portageq"

    #Test with emerge missing
    m.reset_mock()
    path_overrides = {}
    path_overrides['/usr/bin/portageq'] = True
    path_overrides['/usr/bin/emerge'] = False

    val = portage_available()
    assert val==False, "Portage should not be available without emerge"

    # Test with nothing missing
    m.reset_mock()
    path_overrides = {}
    path_overrides['/usr/bin/portageq'] = True
    path_overrides['/usr/bin/emerge'] = True

    val = portage_available()
    assert val==True, "Portage should be available"
    
    os.path.exists = original_exists

# This actually tests portage_detect_single and portage_detect

def test_portage_detect():
    if not is_gentoo():
        print("Skipping not Gentoo")
        return 

    from rosdep2.platforms.gentoo import portage_detect

    m = Mock()
    m.return_value = []

    val = portage_detect([], exec_fn=m)
    assert val == [], val
    
    # Test checking for a package that we do not have installed
    m = Mock(return_value = [])
    val = portage_detect(['tinyxml[stl]'], exec_fn=m)
    assert val == [], "Result was actually: %s" % val
    m.assert_called_with(['portageq', 'match', '/', 'tinyxml[stl]'])

    # Test checking for a package that we do have installed
    m = Mock(return_value = ['dev-libs/tinyxml-2.6.2-r1'])
    val = portage_detect(['tinyxml[stl]'], exec_fn=m)
    assert val == ['tinyxml[stl]'], "Result was actually: %s" % val
    m.assert_called_with(['portageq', 'match', '/', 'tinyxml[stl]'])
    
    # Test checking for two packages that we have installed
    m = Mock(side_effect = [['sys-devel/gcc-4.5.3-r2'], ['dev-libs/tinyxml-2.6.2-r1']])
    val = portage_detect(['tinyxml[stl]', 'gcc'], exec_fn=m)
    assert val == ['gcc', 'tinyxml[stl]'], "Result was actually: %s" % val
    m.assert_any_call(['portageq', 'match', '/', 'tinyxml[stl]'])   
    m.assert_any_call(['portageq', 'match', '/', 'gcc'])
    
    # Test checking for two missing packages
    m = Mock(side_effect = [[],[]])

    val = portage_detect(['tinyxml[stl]', 'gcc'], exec_fn=m)
    assert val == [], "Result was actually: %s" % val
    m.assert_any_call(['portageq', 'match', '/', 'tinyxml[stl]'])   
    m.assert_any_call(['portageq', 'match', '/', 'gcc'])

    # Test checking for one missing, one installed package
    m = Mock(side_effect = [['sys-devel/gcc-4.5.3-r2'], []])

    val = portage_detect(['tinyxml[stl]', 'gcc'], exec_fn=m)
    assert val == ['gcc'], "Result was actually: %s" % val
    m.assert_any_call(['portageq', 'match', '/', 'tinyxml[stl]'])   
    m.assert_any_call(['portageq', 'match', '/', 'gcc'])

    # Test checking for one installed, one missing package (reverse order)
    m = Mock(side_effect = [[], ['dev-libs/tinyxml-2.6.2-r1']])

    val = portage_detect(['tinyxml[stl]', 'gcc'], exec_fn=m)
    assert val == ['tinyxml[stl]'], "Result was actually: %s" % val
    m.assert_any_call(['portageq', 'match', '/', 'tinyxml[stl]'])   
    m.assert_any_call(['portageq', 'match', '/', 'gcc'])

    # Test duplicates (requesting the same package twice)
    #TODO what's the desired behavior here
    m = Mock(side_effect = [['dev-libs/tinyxml-2.6.2-r1'],['dev-libs/tinyxml-2.6.2-r1']])

    val = portage_detect(['tinyxml[stl]', 'tinyxml[stl]'], exec_fn=m)
    assert val == ['tinyxml[stl]','tinyxml[stl]'], "Result was actually: %s" % val
    m.assert_any_call(['portageq', 'match', '/', 'tinyxml[stl]'])   
    # and a second of the same, but any_call won't show that.

    # Test packages with multiple slot
    m = Mock(side_effect = [['dev-lang/python-2.7.2-r3','dev-lang/python-3.2.2']])
    val = portage_detect(['python'], exec_fn=m)
    assert val == ['python'], "Result was actually: %s" % val
    m.assert_any_call(['portageq', 'match', '/', 'python'])   

def test_PortageInstaller():
    if not is_gentoo():
        print("Skipping not Gentoo")
        return 

    from rosdep2.platforms.gentoo import PortageInstaller

    @patch.object(PortageInstaller, 'get_packages_to_install')
    def test(mock_method):
        installer = PortageInstaller()
        mock_method.return_value = []
        assert [] == installer.get_install_command(['fake'])

        mock_method.return_value = ['a', 'b']
        
        expected = [['sudo', '-H', 'emerge', 'a'],
                    ['sudo', '-H', 'emerge', 'b']]
        val = installer.get_install_command(['whatever'], interactive=False)
        assert val == expected, val

        expected = [['sudo', '-H', 'emerge', '-a', 'a'],
                    ['sudo', '-H', 'emerge', '-a', 'b']]
        val = installer.get_install_command(['whatever'], interactive=True)
        assert val == expected, val
        
    try:
        test()
    except AssertionError:
        traceback.print_exc()
        raise
    
