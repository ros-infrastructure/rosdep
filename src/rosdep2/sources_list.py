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

# Author Ken Conley/kwc@willowgarage.com

import os
import sys
import yaml
import hashlib
import urllib2

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse #py3k
    
import rospkg
import rospkg.distro

from .loader import RosdepLoader

#TODO: download default sources list to initialize user : goes to a
#github.com/ros/rosdep_rules URL and downloads a default sources list
#file

#seconds to wait before aborting download of rosdep data
DOWNLOAD_TIMEOUT = 15.0 

SOURCES_LIST_DIR = 'sources.list.d'
SOURCES_CACHE_DIR = 'sources.cache'

def get_sources_list_dir():
    # base of where we read config files from
    etc_ros = rospkg.get_etc_ros_dir()
    # compute cache directory
    return os.path.join(etc_ros, 'rosdep', SOURCES_LIST_DIR)

def get_sources_cache_dir():
    ros_home = rospkg.get_ros_home()
    return os.path.join(ros_home, 'rosdep', SOURCES_CACHE_DIR)

# Default rosdep.yaml format.  For now this is the only valid type and
# is specified for future compatibility.
TYPE_YAML = 'yaml'
VALID_TYPES = [TYPE_YAML]

class SourceListDownloadFailure(Exception):
    """
    Failure downloading sources list data for I/O or other format reasons.
    """
    pass
class InvalidSourcesFile(Exception):
    """
    Sources list data is in an invalid format
    """
    pass

class DataSource(object):
    
    def __init__(self, type_, url, tags, origin=None):
        """
        :param type_: data source type, e.g. TYPE_YAML
        :param url: URL of data location
        :param tags: tags for matching data source to configurations
        :param origin: filename or other indicator of where data came from for debugging.
        """
        # validate inputs
        if not type_ in VALID_TYPES:
            raise ValueError("type must be one of [%s]"%(','.join(VALID_TYPES)))
        parsed = urlparse.urlparse(url)
        if not parsed.scheme or not parsed.netloc or parsed.path in ('', '/'):
            raise ValueError("url must be a fully-specified URL with scheme, hostname, and path: %s"%(str(url)))
        if not type(tags) == list:
            raise ValueError("tags must be a list: %s"%(str(tags)))

        self.type = type_
        self.tags = tags
        
        self.url = url
        self.origin = origin

    def __eq__(self, other):
        return self.type == other.type and \
               self.tags == other.tags and \
               self.url == other.url and \
               self.origin == other.origin
    
    def __str__(self):
        if self.origin:
            return "[%s]:\n%s %s %s"%(self.origin, self.type, self.url, ' '.join(self.tags))
        else:
            return "%s %s %s"%(self.type, self.url, ' '.join(self.tags))            

    def __repr__(self):
        return repr((self.type, self.url, self.tags, self.origin))

class DataSourceMatcher(object):
    
    def __init__(self, tags):
        self.tags = tags
        
    def matches(self, rosdep_data_source):
        """
        Check if the datasource matches this configuration.
        
        :param rosdep_data_source: :class:`DataSource`
        """
        # all of the rosdep_data_source tags must be in our matcher tags
        return not any(set(rosdep_data_source.tags)-set(self.tags))
                 
def download_rosdep_data(url):
    """
    :raises: :exc:`SourceListDownloadFailure` If data cannot be
        retrieved (e.g. 404, bad YAML format, server down).
    """
    try:
        f = urllib2.urlopen(url, timeout=DOWNLOAD_TIMEOUT)
        text = f.read()
        f.close()
        data = yaml.safe_load(text)
        if type(data) != dict:
            raise SourceListDownloadFailure('rosdep data from [%s] is not a YAML dictionary'%(url))
        return data
    except urllib2.URLError as e:
        raise SourceListDownloadFailure(str(e))
    except yaml.YAMLError as e:
        raise SourceListDownloadFailure(str(e))
    
def create_default_matcher():
    """
    Create a :class:`DataSourceMatcher` to match the current
    configuration.

    :returns: :class:`DataSourceMatcher`
    """
    distro_name = rospkg.distro.current_distro_codename()
    os_detect = rospkg.os_detect.OsDetect()
    os_name, os_version, os_codename = os_detect.detect_os()
    tags = [distro_name, os_name, os_codename]
    return DataSourceMatcher(tags)

def parse_sources_data(data, origin='<string>'):
    """
    Parse sources file format (tags optional)::
    
      # comments and empty lines allowed
      <type> <uri> [tags]

    e.g.::

      yaml http://foo/rosdep.yaml fuerte lucid ubuntu
    
    If tags are specified, *all* tags must match the current
    configuration for the sources data to be used.
    
    :param data: data in sources file format
    :returns: List of data sources, [:class:`DataSource`]
    :raises: :exc:`InvalidSourcesFile`
    """
    sources = []
    for line in data.split('\n'):
        line = line.strip()
        # ignore empty lines or comments
        if not line or line.startswith('#'):
            continue
        splits = line.split(' ')
        if len(splits) < 2:
            raise InvalidSourcesFile("In [%s], invalid line:\n%s"%(origin, line))
        type_ = splits[0]
        url = splits[1]
        tags = splits[2:]
        try:
            sources.append(DataSource(type_, url, tags, origin=origin))
        except ValueError as e:
            raise InvalidSourcesFile("In [%s], line:\n\t%s\n%s"%(origin, line, e))
    return sources

def parse_sources_file(filepath):
    """
    Parse file on disk
    
    :returns: List of data sources, [:class:`DataSource`]
    :raises: :exc:`InvalidSourcesFile` If any error occurs reading
        file, so an I/O error, non-existent file, or invalid format.
    """
    try:
        with open(filepath, 'r') as f:
            return parse_sources_data(f.read(), origin=filepath)
    except IOError as e:
        raise InvalidSourcesFile("I/O error reading sources file [%s]: %s"%(filepath, e))

def parse_sources_list(sources_list_dir=None):
    """
    Parse data stored in on-disk sources list directory into a list of
    :class:`DataSource` for processing.

    :returns: List of data sources, [:class:`DataSource`]. If there is
        no sources list dir, this returns an empty list.
    :raises: :exc:`InvalidSourcesFile`
    :raises: :exc:`IOError` if *sources_list_dir* cannot be read.
    """
    if sources_list_dir is None:
        sources_list_dir = get_sources_list_dir()
    if not os.path.exists(sources_list_dir):
        # no sources on this system.  this is a valid state.
        return []
        
    filelist = os.listdir(sources_list_dir)
    sources_list = []
    for f in sorted(filelist):
        sources_list.extend(parse_sources_file(os.path.join(sources_list_dir, f)))
    return sources_list

def update_sources_list(sources_list_dir=None, sources_cache_dir=None, error_handler=None):
    """
    :param sources_list_dir: override source list directory
    :param sources_cache_dir: override sources cache directory
    :param error_handler: fn(url, SourceListDownloadFailure) to call
        if a particular source fails.  This hook is mainly for
        printing errors to console.

    :returns: list of cache files that were updated, ``[str]``
    :raises: :exc:`InvalidSourcesFile` If any of the sources list files is invalid
    :raises: :exc:`IOError` If *sources_list_dir* cannot be read or cache data cannot be written
    """
    sources = parse_sources_list(sources_list_dir=sources_list_dir)
    if sources_cache_dir is None:
        sources_cache_dir = get_sources_cache_dir()
    for source in sources:
        try:
            rosdep_data = download_rosdep_data(source.url)
            filepath = write_cache_file(sources_cache_dir, source.url, rosdep_data)
        except SourceListDownloadFailure as e:
            if error_handler is not None:
                error_handler(source.url, e)

def load_sources_list():
    sources = parse_sources_list()
    raise NotImplemented()

def compute_filename_hash(filename_key):
    sha_hash = hashlib.sha1()
    sha_hash.update(filename_key)
    return sha_hash.hexdigest()
    
def write_cache_file(source_cache_d, filename_key, rosdep_data):
    """
    :param source_cache_d: directory to write cache file to
    :param filename_key: hash of filename is used to store data in
    :param rosdep_data: dictionary of data to serialize as YAML
    :returns: name of file where cache is stored
    """
    key_hash = compute_filename_hash(filename_key)
    filepath = os.path.join(source_cache_d, key_hash)
    with open(filepath, 'w') as f:
        f.write(yaml.safe_dump(rosdep_data))
    return filepath
    
class SourcesListLoader(RosdepLoader):
    """
    SourcesList loader implements the general RosdepLoader API.  This
    implementation is fairly simple as there is only one view the
    source list loader can create.

    This loader will probably not be used directly; instead, it is
    more useful as a backend loader of higher-level implementations,
    like the :class:`rosdep2.rospkg_loader.RospkgLoader`.
    """

    RESOURCE_KEY = 'all'
    VIEW_KEY = 'sources.list'

    def load_view(self, view_name, rosdep_db, verbose=False):
        """
        Load view data into rosdep_db. If the view has already been
        loaded into rosdep_db, this method does nothing.

        :param view_name: name of ROS stack to load, ``str``
        :param rosdep_db: database to load stack data into, :class:`RosdepDatabase`

        :raises: :exc:`InvalidRosdepData`
        """
        if view_name != SourcesListLoader.VIEW_KEY:
            raise rospkg.ResourceNotFound(view_name)
        raise NotImplementedError()

    def get_loadable_resources(self):
        return [SourcesListLoader.RESOURCE_KEY]

    def get_loadable_views(self):
        return [SourcesListLoader.VIEW_KEY]

    def get_rosdeps(self, resource_name, implicit=True):
        """
        SourceListLoader always returns empty list as no resources have explicit rosdeps.
        
        :raises: :exc:`rospkg.ResourceNotFound` if *resource_name* cannot be found.
        """
        if resource_name != SourcesListLoader.RESOURCE_KEY:
            raise rospkg.ResourceNotFound(resource_name)
        return []
    
    def get_view_key(self, resource_name):
        """
        SourceListLoader only understands a single resource and view.
        It will map that resource to the view.

        :returns: Name of view that *resource_name* is in, ``None`` if no associated view.
        :raises: :exc:`rospkg.ResourceNotFound` if *resource_name* cannot be found.
        """
        if resource_name == SourcesListLoader.RESOURCE_KEY:
            return SourcesListLoader.VIEW_KEY
        else:
            raise rospkg.ResourceNotFound(resource_name)
