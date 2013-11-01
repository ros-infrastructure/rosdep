# Copyright (c) 2012, Willow Garage, Inc.
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

# Author William Woodall/wjwwood@gmail.com

def test_DependencyGraph_Linear():
	from rosdep2.dependency_graph import DependencyGraph
	# Normal A-B-C
	dg = DependencyGraph()
	dg['A']['installer_key'] = 'a_installer'
	dg['A']['install_keys'] = ['a']
	dg['A']['dependencies'] = ['B']
	dg['B']['installer_key'] = 'b_installer'
	dg['B']['install_keys'] = ['b']
	dg['B']['dependencies'] = ['C']
	dg['C']['installer_key'] = 'c_installer'
	dg['C']['install_keys'] = ['c']
	dg['C']['dependencies'] = []
	result = dg.get_ordered_dependency_list()
	expected = [('c_installer', ['c']), ('b_installer', ['b']), ('a_installer', ['a'])]
	assert result == expected, "Results did not match expectations: %s == %s"%(str(result),str(expected))

def test_DependencyGraph_Cycle():
	from rosdep2.dependency_graph import DependencyGraph
	# Full Loop A-B-C-A-...
	dg = DependencyGraph()
	dg['A']['installer_key'] = 'a_installer'
	dg['A']['install_keys'] = ['a']
	dg['A']['dependencies'] = ['B']
	dg['B']['installer_key'] = 'b_installer'
	dg['B']['install_keys'] = ['b']
	dg['B']['dependencies'] = ['C']
	dg['C']['installer_key'] = 'c_installer'
	dg['C']['install_keys'] = ['c']
	dg['C']['dependencies'] = ['A']
	try:
		result = dg.get_ordered_dependency_list()
		assert False, "Doesn't fail, it should fail with an AssertionError because of the cycle."
	except AssertionError as e:
		if not str(e).startswith("A cycle in the dependency graph occurred with key"):
			assert False, "Throws AssertionError, but with the wrong message. Error was: %s: %s"%(type(e),str(e))
	except Exception as e:
		assert False, "Throws and Exception, but not an AssertionError. Error was: %s: %s"%(type(e),str(e))

def test_DependencyGraph_Short_Cycle():
	from rosdep2.dependency_graph import DependencyGraph
	# Short cycle A-B-C-D-B-C-D-...
	dg = DependencyGraph()
	dg['A']['installer_key'] = 'a_installer'
	dg['A']['install_keys'] = ['a']
	dg['A']['dependencies'] = ['B']
	dg['B']['installer_key'] = 'b_installer'
	dg['B']['install_keys'] = ['b']
	dg['B']['dependencies'] = ['C']
	dg['C']['installer_key'] = 'c_installer'
	dg['C']['install_keys'] = ['c']
	dg['C']['dependencies'] = ['D']
	dg['D']['installer_key'] = 'd_installer'
	dg['D']['install_keys'] = ['d']
	dg['D']['dependencies'] = ['B']
	try:
		result = dg.get_ordered_dependency_list()
		assert False, "Doesn't fail, it should fail with an AssertionError because of the cycle."
	except AssertionError as e:
		if not str(e).startswith("A cycle in the dependency graph occurred with key"):
			assert False, "Throws AssertionError, but with the wrong message. Error was: %s: %s"%(type(e),str(e))
	except Exception as e:
		assert False, "Throws and Exception, but not an AssertionError. Error was: %s: %s"%(type(e),str(e))

def test_DependencyGraph_Invalid_Key():
	from rosdep2.dependency_graph import DependencyGraph
	# Invalid graph A-B-C where C doesn't exist
	dg = DependencyGraph()
	dg['A']['installer_key'] = 'a_installer'
	dg['A']['install_keys'] = ['a']
	dg['A']['dependencies'] = ['B']
	dg['B']['installer_key'] = 'b_installer'
	dg['B']['install_keys'] = ['b']
	dg['B']['dependencies'] = ['C']
	try:
		result = dg.get_ordered_dependency_list()
		assert False, "Doesn't fail, it should fail with an KeyError because of the invalid rosdep key."
	except KeyError as e:
		if not str(e).endswith("does not exist in the dictionary of resolutions.'"):
			assert False, "Throws KeyError, but with the wrong message. Error was: %s: %s"%(type(e),str(e))
	except Exception as e:
		assert False, "Throws and Exception, but not an KeyError. Error was: %s: %s"%(type(e),str(e))

def test_DependencyGraph_Invalid_Key2():
	from rosdep2.dependency_graph import DependencyGraph
	# Invalid graph A-B-C where B doesn't exist
	dg = DependencyGraph()
	dg['A']['installer_key'] = 'a_installer'
	dg['A']['install_keys'] = ['a']
	dg['A']['dependencies'] = ['B']
	dg['C']['installer_key'] = 'c_installer'
	dg['C']['install_keys'] = ['c']
	dg['C']['dependencies'] = []
	try:
		result = dg.get_ordered_dependency_list()
		assert False, "Doesn't fail, it should fail with an KeyError because of the invalid rosdep key."
	except KeyError as e:
		if not str(e).endswith("does not exist in the dictionary of resolutions.'"):
			assert False, "Throws KeyError, but with the wrong message. Error was: %s: %s"%(type(e),str(e))
	except Exception as e:
		assert False, "Throws and Exception, but not an KeyError. Error was: %s: %s"%(type(e),str(e))

def test_DependencyGraph_Multi_Root():
	from rosdep2.dependency_graph import DependencyGraph
	# Multi root, shared dependency: A-B-C, D-C
	dg = DependencyGraph()
	dg['A']['installer_key'] = 'a_installer'
	dg['A']['install_keys'] = ['a']
	dg['A']['dependencies'] = ['B']
	dg['B']['installer_key'] = 'b_installer'
	dg['B']['install_keys'] = ['b']
	dg['B']['dependencies'] = ['C']
	dg['C']['installer_key'] = 'c_installer'
	dg['C']['install_keys'] = ['c']
	dg['C']['dependencies'] = []
	dg['D']['installer_key'] = 'd_installer'
	dg['D']['install_keys'] = ['d']
	dg['D']['dependencies'] = ['C']
	result = dg.get_ordered_dependency_list()
	# TODO: The expected might also have a different order, for example it might be:
	# [('c_installer', ['c']), ('d_installer', ['d']), ('b_installer', ['b']), ('a_installer', ['a'])]
	# But that wont invalidate the order from a dependency graph stand point
	expected = [
		[('c_installer', ['c']), ('b_installer', ['b']), ('a_installer', ['a']), ('d_installer', ['d'])],
		[('c_installer', ['c']), ('d_installer', ['d']), ('b_installer', ['b']), ('a_installer', ['a'])],
	]
	assert result in expected, "Results did not match expectations: %s == %s"%(str(result),str(expected))

def test_DependencyGraph_Realworld():
	from rosdep2.dependency_graph import DependencyGraph
	# Real world example
	dg = DependencyGraph()
	dg['python-matplotlib']['installer_key'] = 'pip'
	dg['python-matplotlib']['install_keys'] = ['matplotlib']
	dg['python-matplotlib']['dependencies'] = ['pkg-config']
	dg['pkg-config']['installer_key'] = 'homebrew'
	dg['pkg-config']['install_keys'] = ['pkg-config']
	dg['pkg-config']['dependencies'] = []
	result = dg.get_ordered_dependency_list()
	expected = [('homebrew', ['pkg-config']), ('pip', ['matplotlib'])]
	assert result == expected, "Results did not match expectations: %s == %s"%(str(result),str(expected))

