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

import os
import sys
import cStringIO

import rospkg

import unittest

def get_test_tree_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'tree'))

from rosdep2.main import rosdep_main

from contextlib import contextmanager
@contextmanager
def fakeout():
    realstdout = sys.stdout
    realstderr = sys.stderr
    fakestdout = cStringIO.StringIO()
    fakestderr = cStringIO.StringIO()
    sys.stdout = fakestdout
    sys.stderr = fakestderr
    yield fakestdout, fakestderr
    sys.stdout = realstdout
    sys.stderr = realstderr
    
# the goal of these tests is only to test that we are wired into the
# APIs.  More exhaustive tests are at the unit level.
class TestRosdepMain(unittest.TestCase):
    def setUp(self):
        if 'ROSDEP_DEBUG' in os.environ:
            del os.environ['ROSDEP_DEBUG']
        self.old_rr = rospkg.get_ros_root()
        self.old_rpp = rospkg.get_ros_package_path()
        if 'ROS_ROOT' in os.environ:
            del os.environ['ROS_ROOT']
        os.environ['ROS_PACKAGE_PATH'] = os.path.join(get_test_tree_dir())

    def tearDown(self):
        if self.old_rr is not None:
            os.environ['ROS_ROOT'] = self.old_rr
        if self.old_rpp is not None:
            os.environ['ROS_PACKAGE_PATH'] = self.old_rpp

    def test_bad_commands(self):
        for commands in [[], ['fake', 'something'], ['check'], ['install', '-a', 'rospack_fake'],
                         ['check', 'rospack_fake', '--os', 'ubuntulucid'],
                         ]:
            try:
                rosdep_main(commands)
                assert False, "system exit should have occurred"
            except SystemExit:
                pass
        
    def test_check(self):
        with fakeout() as b:
            try:
                rosdep_main(['check', 'python_dep'])
            except SystemExit:
                assert False, "system exit occurred: %s\n%s"%(b[0].getvalue(), b[1].getvalue())

            stdout, stderr = b
            assert stdout.getvalue().strip() == "All system dependencies have been satisified", stdout.getvalue()
            assert not stderr.getvalue(), stderr.getvalue()
        try:
            with fakeout() as b:
                rosdep_main(['check', 'python_dep', '--os', 'ubuntu:lucid'])
                stdout, stderr = b
                assert stdout.getvalue().strip() == "All system dependencies have been satisified"
                assert not stderr.getvalue(), stderr.getvalue()
        except SystemExit:
            assert False, "system exit occurred"

        with fakeout() as b:
            missing = ['p1dep1-ubuntu','p2dep1-ubuntu','dep1-ubuntu','dep2-ubuntu','p1dep2-ubuntu']
            try:
                rosdep_main(['check', 'stack1_p1', 'stack1_p2'])
                assert False, "system exit should have occurred"
            except SystemExit:
                pass

            stdout, stderr = b
            out = stdout.getvalue().strip()
            apts = [x for x in out.split('\n') if x.startswith('apt')]
            apt_deps = [x.split('\t')[1] for x in apts]
            assert "System dependencies have not been satisified" in out
            assert set(apt_deps) == set(missing), apt_deps
            assert not stderr.getvalue(), stderr.getvalue()

        try:
            with fakeout() as b:
                rosdep_main(['check', 'packageless'])
                stdout, stderr = b
                assert stdout.getvalue().strip() == "No packages in arguments, aborting", stdout.getvalue()
                assert not stderr.getvalue(), stderr.getvalue()
        except SystemExit:
            assert False, "system exit occurred"

        try:
            rosdep_main(['check', 'nonexistent'])
            assert False, "system exit should have occurred"
        except SystemExit:
            pass

    def test_install(self):
        try:
            # python must have already been installed
            with fakeout() as b:
                rosdep_main(['install', 'python_dep'])
                stdout, stderr = b
                assert "All required rosdeps installed" in stdout.getvalue(), stdout.getvalue()
                assert not stderr.getvalue(), stderr.getvalue()
            with fakeout() as b:
                rosdep_main(['install', 'python_dep', '-r'])
                stdout, stderr = b
                assert "All required rosdeps installed" in stdout.getvalue(), stdout.getvalue()
                assert not stderr.getvalue(), stderr.getvalue()
        except SystemExit:
            assert False, "system exit occurred"
        try:
            rosdep_main(['check', 'nonexistent'])
            assert False, "system exit should have occurred"
        except SystemExit:
            pass

    def test_where_defined(self):
        try:
            expected = os.path.join(get_test_tree_dir(), 'ros', 'rosdep.yaml')
            with fakeout() as b:
                rosdep_main(['where_defined', 'python'])
                stdout, stderr = b
                output = stdout.getvalue().strip()
                assert os.path.samefile(expected, output)
        except SystemExit:
            assert False, "system exit occurred"
        
    def test_what_needs(self):
        try:
            expected = ['python_dep']
            with fakeout() as b:
                rosdep_main(['what_needs', 'python'])
                stdout, stderr = b
                output = stdout.getvalue().strip()
                assert output.split('\n') == expected
            expected = ['python_dep']
            with fakeout() as b:
                rosdep_main(['what_needs', 'python', '--os', 'ubuntu:lucid', '--verbose'])
                stdout, stderr = b
                output = stdout.getvalue().strip()
                assert output.split('\n') == expected
        except SystemExit:
            assert False, "system exit occurred"

    def test_keys(self):
        try:
            with fakeout() as b:
                rosdep_main(['keys', 'rospack_fake'])
                stdout, stderr = b
                assert stdout.getvalue().strip() == "tinyxml", stdout.getvalue()
                assert not stderr.getvalue(), stderr.getvalue()
            with fakeout() as b:
                rosdep_main(['keys', 'rospack_fake', '--os', 'ubuntu:lucid', '--verbose'])
                stdout, stderr = b
                assert stdout.getvalue().strip() == "tinyxml", stdout.getvalue()
                assert not stderr.getvalue(), stderr.getvalue()
        except SystemExit:
            assert False, "system exit occurred"
        try:
            rosdep_main(['keys', 'nonexistent'])
            assert False, "system exit should have occurred"
        except SystemExit:
            pass
