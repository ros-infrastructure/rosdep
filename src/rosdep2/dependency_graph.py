#!/usr/bin/env python
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

from __future__ import print_function
from collections import defaultdict

class Resolution(dict):
    """docstring for Resolution"""
    def __init__(self):
        super(Resolution, self).__init__()
        self['installer_key'] = None
        self['install_keys'] = []
        self['dependencies'] = []
        self['is_root'] = True

class DependencyGraph(defaultdict):
	"""asfd"""
	def __init__(self):
		defaultdict.__init__(self, Resolution)
	
	def detect_cycles(self, rosdep_key, traveled_keys):
		assert rosdep_key not in traveled_keys, "A cycle in the dependency graph occurred with key `%s`."%rosdep_key
		traveled_keys.append(rosdep_key)
		for dependency in self[rosdep_key]['dependencies']:
			self.detect_cycles(dependency, traveled_keys)

	def validate(self):
		for rosdep_key in self:
			# Ensure all dependencies have definitions
			# i.e.: Ensure we aren't pointing to invalid rosdep keys
			for dependency in self[rosdep_key]['dependencies']:
				if not self.has_key(dependency):
					raise KeyError("Invalid Graph Structure: rosdep key `%s` does not exist in the dictionary of resolutions."%dependency)
				self[dependency]['is_root'] = False
		# Check each entry for cyclical dependencies
		for rosdep_key in self:
			self.detect_cycles(rosdep_key, [])

	def get_ordered_uninstalled(self):
		# Validate the graph
		self.validate()
		# Generate the uninstalled list
		uninstalled = []
		for rosdep_key in self:
			if self[rosdep_key]['is_root']:
				uninstalled.extend(self._get_ordered_uninstalled(rosdep_key))
		# Make the list unique
		result = []
		for item in uninstalled:
			if item not in result:
				result.append(item)
		return result

	def _get_ordered_uninstalled(self, key):
		uninstalled = []
		for dependency in self[key]['dependencies']:
			uninstalled.extend(self._get_ordered_uninstalled(dependency))
		uninstalled.append((self[key]['installer_key'], self[key]['install_keys']))
		return uninstalled
