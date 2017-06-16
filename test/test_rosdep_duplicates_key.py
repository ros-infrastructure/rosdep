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

from __future__ import print_function

import unittest

from rosdep2.lookup import RosdepLookup, RosdepView
from rosdep2.rospkg_loader import DEFAULT_VIEW_KEY
from rosdep2.sources_list import SourcesListLoader, get_sources_cache_dir

class DuplicatesRosdepKey(unittest.TestCase):
    def testRosdepKey(self):
        ret = True
        sources_loader = SourcesListLoader.create_default(sources_cache_dir=get_sources_cache_dir())
        lookup = RosdepLookup.create_from_rospkg(sources_loader=sources_loader)
        view = lookup.get_rosdep_view(DEFAULT_VIEW_KEY, verbose=None) # to call init

        db_name_view = dict()
        for view_key in lookup.rosdep_db.get_view_dependencies(DEFAULT_VIEW_KEY):
            db_entry=lookup.rosdep_db.get_view_data(view_key)       
            for dep_name, dep_data in db_entry.rosdep_data.items():
                if dep_name in db_name_view:
                    print("%s is multiply defined in\n\t%s and \n\t%s\n"%(dep_name, db_name_view[dep_name], view_key))
                    ret = False
                db_name_view[dep_name] = view_key

        self.assertTrue(ret)

if __name__ == '__main__':
    unittest.main()
