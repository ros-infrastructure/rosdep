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
import rospkg.os_detect

import unittest

GITHUB_BASE_URL = 'https://github.com/ros/rosdistro/raw/master/rosdep/base.yaml'
GITHUB_PYTHON_URL = 'https://github.com/ros/rosdistro/raw/master/rosdep/python.yaml'

def get_test_dir():
    return os.path.abspath(os.path.dirname(__file__))

def get_test_tree_dir():
    return os.path.abspath(os.path.join(get_test_dir(), 'tree'))

def get_cache_dir():
    p = os.path.join(get_test_dir(), 'sources_cache')
    assert os.path.isdir(p)
    return p

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
        sources_cache = get_cache_dir()
        cmd_extras = ['-c', sources_cache]
        for commands in [[], ['fake', 'something'], ['check'], ['install', '-a', 'rospack_fake'],
                         ['check', 'rospack_fake', '--os', 'ubuntulucid'],
                         ]:
            try:
                rosdep_main(commands+cmd_extras)
                assert False, "system exit should have occurred"
            except SystemExit:
                pass
        
    def test_check(self):
        sources_cache = get_cache_dir()
        cmd_extras = ['-c', sources_cache]

        with fakeout() as b:
            try:
                rosdep_main(['check', 'python_dep']+cmd_extras)
            except SystemExit:
                assert False, "system exit occurred: %s\n%s"%(b[0].getvalue(), b[1].getvalue())

            stdout, stderr = b
            assert stdout.getvalue().strip() == "All system dependencies have been satisified", stdout.getvalue()
            assert not stderr.getvalue(), stderr.getvalue()
        try:
            osd = rospkg.os_detect.OsDetect()
            override = "%s:%s"%(osd.get_name(), osd.get_codename())
            with fakeout() as b:
                rosdep_main(['check', 'python_dep', '--os', override]+cmd_extras)
                stdout, stderr = b
                assert stdout.getvalue().strip() == "All system dependencies have been satisified"
                assert not stderr.getvalue(), stderr.getvalue()
        except SystemExit:
            assert False, "system exit occurred"

        # this used to abort, but now rosdep assumes validity for even empty stack args
        try:
            with fakeout() as b:
                rosdep_main(['check', 'packageless']+cmd_extras)
                stdout, stderr = b
                assert stdout.getvalue().strip() == "All system dependencies have been satisified"
                assert not stderr.getvalue(), stderr.getvalue()
        except SystemExit:
            assert False, "system exit occurred"

        try:
            rosdep_main(['check', 'nonexistent']+cmd_extras)
            assert False, "system exit should have occurred"
        except SystemExit:
            pass

    def test_install(self):
        sources_cache = get_cache_dir()
        cmd_extras = ['-c', sources_cache]

        try:
            # python must have already been installed
            with fakeout() as b:
                rosdep_main(['install', 'python_dep']+cmd_extras)
                stdout, stderr = b
                assert "All required rosdeps installed" in stdout.getvalue(), stdout.getvalue()
                assert not stderr.getvalue(), stderr.getvalue()
            with fakeout() as b:
                rosdep_main(['install', 'python_dep', '-r']+cmd_extras)
                stdout, stderr = b
                assert "All required rosdeps installed" in stdout.getvalue(), stdout.getvalue()
                assert not stderr.getvalue(), stderr.getvalue()
        except SystemExit:
            assert False, "system exit occurred: "+b[1].getvalue()
        try:
            rosdep_main(['check', 'nonexistent'])
            assert False, "system exit should have occurred"
        except SystemExit:
            pass

    def test_where_defined(self):
        try:
            sources_cache = get_cache_dir()
            expected = GITHUB_PYTHON_URL 
            for command in (['where_defined', 'testpython'], ['where_defined', 'testpython']):
                with fakeout() as b:
                    # set os to ubuntu so this test works on different platforms
                    rosdep_main(command + ['-c', sources_cache, '--os=ubuntu:lucid'])
                    stdout, stderr = b
                    output = stdout.getvalue().strip()
                    assert output == expected, output
        except SystemExit:
            assert False, "system exit occurred"
        
    def test_what_needs(self):
        try:
            sources_cache = get_cache_dir()
            cmd_extras = ['-c', sources_cache]
            expected = ['python_dep']
            with fakeout() as b:
                rosdep_main(['what-needs', 'testpython']+cmd_extras)
                stdout, stderr = b
                output = stdout.getvalue().strip()
                assert output.split('\n') == expected
            expected = ['python_dep']
            with fakeout() as b:
                rosdep_main(['what_needs', 'testpython', '--os', 'ubuntu:lucid', '--verbose']+cmd_extras)
                stdout, stderr = b
                output = stdout.getvalue().strip()
                assert output.split('\n') == expected
        except SystemExit:
            assert False, "system exit occurred"

    def test_keys(self):
        sources_cache = get_cache_dir()
        cmd_extras = ['-c', sources_cache]

        try:
            with fakeout() as b:
                rosdep_main(['keys', 'rospack_fake']+cmd_extras)
                stdout, stderr = b
                assert stdout.getvalue().strip() == "testtinyxml", stdout.getvalue()
                assert not stderr.getvalue(), stderr.getvalue()
            with fakeout() as b:
                rosdep_main(['keys', 'rospack_fake', '--os', 'ubuntu:lucid', '--verbose']+cmd_extras)
                stdout, stderr = b
                assert stdout.getvalue().strip() == "testtinyxml", stdout.getvalue()
        except SystemExit:
            assert False, "system exit occurred"
        try:
            rosdep_main(['keys', 'nonexistent']+cmd_extras)
            assert False, "system exit should have occurred"
        except SystemExit:
            pass
