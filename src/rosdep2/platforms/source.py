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

# Author Tully Foote/tfoote@willowgarage.com

from __future__ import print_function

import shutil
import tarfile
import tempfile
import urllib

import yaml

from ..core import rd_debug
from ..installers import Installer, InstallFailed
from ..model import InvalidRosdepData
from ..shell_utils import create_tempfile_from_string_and_execute

SOURCE_INSTALLER='source'

def register_installers(context):
    context.set_installer(SOURCE_INSTALLER, SourceInstaller())

class InvalidRdmanifest(Exception):
    """
    rdmanifest format is invalid.
    """
    pass

class DownloadFailed(Exception): pass
class Md5Mismatch(Exception): pass

def _sub_fetch_file(url, md5sum=None):
    """
    Sub-routine of _fetch_file
    
    :raises: :exc:`Md5Mismatch`
    :raises: :exc:`DownloadFailed`
    """
    contents = ''
    try:
        fh = urllib2.urlopen(url)
        contents = fh.read()
        filehash =  hashlib.md5(contents).hexdigest()
        if md5sum and filehash != md5sum:
            raise Md5Mismatch( "md5sum didn't match for %s.  Expected %s got %s"%(url, md5sum, filehash))
    except urllib2.URLError as ex:
        raise DownloadFailed(str(ex))

    return contents    

def get_file_hash(filename):
    md5 = hashlib.md5()
    with open(filename,'rb') as f: 
        for chunk in iter(lambda: f.read(8192), ''): 
            md5.update(chunk)
    return md5.hexdigest()

def fetch_file(url, md5sum):
    error = contents = ''
    try:
        contents = _sub_fetch_file(url, md5sum)
    except DownloadFailed as e:
        rd_debug("Download of file %s failed"%(url))
        error = str(e)
    except Md5Mismatch as e:
        rd_debug("Download of file %s failed"%(url))
        error = str(e)
    return contents, error

def load_rdmanifest(url, md5sum, alt_url=None):
    """
    :returns: contents of rdmanifest
    :raises: :exc:`DownloadFailed`
    """
    contents, error = fetch_file(url, md5sum)
    # fetch the manifest
    error_prefix = "Failed to load a rdmanifest from %s: "%(url)
    if not contents and alt_url: # try the backup url
        contents, error = fetch_file(url, md5sum)
        error_prefix = "Failed to load a rdmanifest from either %s or %s: "%(url, alt_url)
    if not contents:
        raise DownloadFailed(error_prefix + error)
    try:
        manifest = yaml.load(contents)
    except yaml.scanner.ScannerError as ex:
        raise InvalidRdmanifest("Failed to parse yaml in %s:  Error: %s"%(contents, ex))        
    return manifest

#TODO: create SourceInstall instance objects
class SourceInstaller(Installer):

    def __init__(self):
        pass
    
    def resolve(self, rosdep_args):
        """
        :raises: :exc:`InvalidRosdepData`
        """
        #TODOXXX: should not take in rosdep_args
        
        self.url = rosdep_args.get("uri")
        if not self.url:
            raise InvalidRosdepData("uri required for source rosdeps") 
        self.alt_url = rosdep_args.get("alternate-uri")
        self.md5sum = rosdep_args.get("md5sum")

        self.manifest = None

        try:
            #TODO add md5sum verification
            rd_debug("Downloading manifest %s"%self.url)
            set_manifest(load_rdmanifest(self.url, self.md5sum, self.alt_url))
        except DownloadFailed as ex:
            # not sure this should be masked this way
            raise InvalidRosdepData(str(ex))            
        except InvalidRdmanifest as ex:
            raise InvalidRosdepData(str(ex))

    def set_manifest(self, manifest):
        self.manifest = manifest
        rd_debug("Loading manifest:\n{{{%s\n}}}\n"%manifest)
        
        self.install_command = manifest.get("install-script", "#!/bin/bash\n#no install-script specificd")
        self.check_presence_command = manifest.get("check-presence-script", "#!/bin/bash\n#no check-presence-script\nfalse")

        self.exec_path = manifest.get("exec-path", ".")
        self.depends = manifest.get("depends", [])
        self.tarball = manifest.get("uri")
        if not self.tarball:
            raise RosdepException("uri required for source rosdeps") 
        self.alternate_tarball = manifest.get("alternate-uri")
        self.tarball_md5sum = manifest.get("md5sum")
        
    def check_presence(self):
        return create_tempfile_from_string_and_execute(self.check_presence_command)

    def get_install_command(self, interactive=True):
        tempdir = tempfile.mkdtemp()
        success = False

        rd_debug("Fetching %s"%self.tarball)
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
                        raise InstallFailed("md5sum check on %s and %s failed.  Expected %s got %s and %s"%(self.tarball, self.alternate_tarball, self.tarball_md5sum, hash1, hash2))
                else:
                    raise InstallFailed("md5sum check on %s failed.  Expected %s got %s "%(self.tarball, self.tarball_md5sum, hash1))
        else:
            rd_debug("No md5sum defined for tarball, not checking.")
            
        try:
            tarf = tarfile.open(filename)
            tarf.extractall(tempdir)

            if execute:
                rd_debug("Running installation script")
                success = create_tempfile_from_string_and_execute(self.install_command, os.path.join(tempdir, self.exec_path))
            elif display:
                print("Would have executed\n{{{%s\n}}}"%self.install_command)
        finally:
            shutil.rmtree(tempdir)
            os.remove(f[0])

        if success:
            rd_debug("successfully executed script")
            return True
        return False

    def get_depends(self): 
        #todo verify type before returning
        return self.depends
        
