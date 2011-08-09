#!/usr/bin/env python
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

from __future__ import print_function

import shutil
import tarfile
import tempfile
import urllib

import yaml

from .shell_utils import create_tempfile_from_string_and_execute

class SourceInstaller(Installer):
    def __init__(self, arg_dict):
        self.url = arg_dict.get("uri")
        if not self.url:
            raise rosdep.core.RosdepException("uri required for source rosdeps") 
        self.alt_url = arg_dict.get("alternate-uri")
        self.md5sum = arg_dict.get("md5sum")

        self.manifest = None

        #TODO add md5sum verification
        if "ROSDEP_DEBUG" in os.environ:
            print "Downloading manifest %s"%self.url

        error = ''

        contents = ''
        # fetch the manifest
        try:
            contents = fetch_file(self.url, self.md5sum)
        except rosdep.core.RosdepException, ex:
            if "ROSDEP_DEBUG" in os.environ:
                print "Failed to fetch file %s for reason %s"%(self.url, ex)

        if not contents: # try the backup url
            if not self.alt_url:
                raise rosdep.core.RosdepException("Failed to load a rdmanifest from %s, and no alternate URI given"%(self.url))
            try:
                contents = fetch_file(self.alt_url, self.md5sum)
            except rosdep.core.RosdepException, ex:
                if "ROSDEP_DEBUG" in os.environ:
                    print "Failed to fetch file %s for reason %s"%(self.alt_url, ex)

        if not contents:
            raise rosdep.core.RosdepException("Failed to load a rdmanifest from either %s or %s"%(self.url, self.alt_url))

                
        try:
            self.manifest = yaml.load(contents)
                    
        except yaml.scanner.ScannerError, ex:
            raise rosdep.core.RosdepException("Failed to parse yaml in %s:  Error: %s"%(contents, ex))        
                
        if "ROSDEP_DEBUG" in os.environ:
            print "Downloaded manifest:\n{{{%s\n}}}\n"%self.manifest
        
        self.install_command = self.manifest.get("install-script", "#!/bin/bash\n#no install-script specificd")
        self.check_presence_command = self.manifest.get("check-presence-script", "#!/bin/bash\n#no check-presence-script\nfalse")

        self.exec_path = self.manifest.get("exec-path", ".")

        self.depends = self.manifest.get("depends", [])

        self.tarball = self.manifest.get("uri")
        if not self.tarball:
            raise rosdep.core.RosdepException("uri required for source rosdeps") 
        self.alternate_tarball = self.manifest.get("alternate-uri")
        self.tarball_md5sum = self.manifest.get("md5sum")
        

    def check_presence(self):
        return create_tempfile_from_string_and_execute(self.check_presence_command)

    def generate_package_install_command(self, default_yes = False, execute = True, display =True):
        tempdir = tempfile.mkdtemp()
        success = False

        if "ROSDEP_DEBUG" in os.environ:
            print "Fetching %s"%self.tarball
        f = urllib.urlretrieve(self.tarball)
        filename = f[0]
        if self.tarball_md5sum:
            hash1 = get_file_hash(filename)
            if self.tarball_md5sum != hash1:
                #try backup tarball if it is defined
                if self.alternate_tarball:
                    f = urllib.urlretrieve(self.alternate_tarball)
                    filename = f[0]
                    hash2 = get_file_hash(filename)
                    if self.tarball_md5sum != hash2:
                        raise rosdep.core.RosdepException("md5sum check on %s and %s failed.  Expected %s got %s and %s"%(self.tarball, self.alternate_tarball, self.tarball_md5sum, hash1, hash2))
                else:
                    raise rosdep.core.RosdepException("md5sum check on %s failed.  Expected %s got %s "%(self.tarball, self.tarball_md5sum, hash1))
            
        else:
            if "ROSDEP_DEBUG" in os.environ:
                print "No md5sum defined for tarball, not checking."
            
        try:
            tarf = tarfile.open(filename)
            tarf.extractall(tempdir)

            if execute:
                if "ROSDEP_DEBUG" in os.environ:
                    print "Running installation script"
                success = create_tempfile_from_string_and_execute(self.install_command, os.path.join(tempdir, self.exec_path))
            elif display:
                print "Would have executed\n{{{%s\n}}}"%self.install_command
            
        finally:
            shutil.rmtree(tempdir)
            os.remove(f[0])

        if success:
            if "ROSDEP_DEBUG" in os.environ:
                print "successfully executed script"
            return True
        return False

    def get_depends(self): 
        #todo verify type before returning
        return self.depends
        
