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

"""
Underlying model of rosdep data.  The basic data model of rosdep is to
store a dictionary of data indexed by stack.  This data includes a
dictionary mapping rosdep dependency names to rules and the stack
dependencies.

This is a lower-level representation.  Higher-level representation can
combine these rosdep dependency maps and stack dependencies together
into a combined view on which queries can be made.
"""

class InvalidRosdepData(Exception):
    """
    Data is not in valid rosdep format.
    """

    def __init__(self, message, origin=None):
        super(InvalidRosdepData, self).__init__(message)
        self.origin = origin

class RosdepDatabaseEntry:
    """
    Stores rosdep data and metadata for a single stack.
    """
    
    def __init__(self, rosdep_data, stack_dependencies, origin):
        """
        :param rosdep_data: raw rosdep dictionary map for stack
        :param stack_dependencies: list of stack dependency names
        :param origin: name of where data originated, e.g. filename
        """
        self.rosdep_data = rosdep_data
        self.stack_dependencies = stack_dependencies
        self.origin = origin
        
class RosdepDatabase:
    """
    Stores loaded rosdep data for multiple stacks.
    """
    
    def __init__(self):
        self._rosdep_db = {} # {stack_name: RosdepDatabaseEntry}

    def is_loaded(self, stack_name):
        """
        :param stack_name: name of stack to check
        :returns: ``True`` if *stack_name* has been loaded into this
          database.
        """
        return stack_name in self._rosdep_db

    def mark_loaded(self, stack_name):
        """
        If stack is not already loaded, this will mark it as such.  This in effect sets the data for the stack to be empty.

        :param stack_name: name of stack to mark as loaded
        """
        self.set_stack_data(stack_name, {}, [], None)
        
    def set_stack_data(self, stack_name, rosdep_data, stack_dependencies, origin):
        """
        Set data associated with stack.  This will create a new
        :class:`RosdepDatabaseEntry`.

        :param rosdep_data: rosdep data map to associated with stack.
          This will be copied.
        :param origin: origin of stack data, e.g. filepath of ``rosdep.yaml``
        """
        self._rosdep_db[stack_name] = RosdepDatabaseEntry(rosdep_data.copy(), stack_dependencies, origin)

    def get_stack_names(self):
        """
        :returns: list of stack names that are loaded into this database.
        """
        return self._rosdep_db.keys()
    
    def get_stack_data(self, stack_name):
        """
        :returns: :class:`RosdepDatabaseEntry` of given stack.

        :raises: :exc:`KeyError` if no entry for *stack_name*
        """
        return self._rosdep_db[stack_name]
    
    def get_stack_dependencies(self, stack_name):
        """
        :raises: :exc:`KeyError` if *stack_name* is not an entry, or if
          all of stack's dependencies have not been properly loaded.
        """
        entry = self.get_stack_data(stack_name)
        dependencies = set(entry.stack_dependencies)
        for s in entry.stack_dependencies:
            dependencies.update(self.get_stack_dependencies(s))
        return list(set(dependencies))
