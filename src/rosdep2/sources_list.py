import os
import sys
import yaml
import hashlib
import urllib2

import rospkg
import rospkg.distro

from .loader import RosdepLoader

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

#TODO: download default sources list : goes to a
#github.com/ros/rosdep_rules URL and downloads a default sources list
#file

# Default rosdep.yaml format.  For now this is the only valid type and
# is specified for future compatibility.
TYPE_YAML = 'yaml'

class SourceListDownloadFailure(Exception):
    pass

class DataSource(object):
    
    def __init__(self, type_, url, tags, origin=None):
        """
        :param type_: data source type, e.g. TYPE_YAML
        :param url: URL of data location
        :param tags: tags for matching data source to configurations
        :param origin: filename or other indicator of where data came from for debugging.
        """
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

def parse_sources_data(data):
    """
    Parse sources file format::
    
      <type> <uri> <tags>

    e.g.::

      yaml http://foo/rosdep.yaml fuerte lucid ubuntu
    
    :param data: data in sources file format
    :returns: List of data sources, [:class:`DataSource`]
    :raises: :exc:`InvalidSourcesFile`
    """
    sources = []
    for line in data.split('\n'):
        splits = line.split(' ')
        if len(splits) < 3:
            raise InvalidSourcesFile("In [%s], invalid line:\n%s"%(filepath, line))
        type_ = splits[0]
        url = splits[1]
        tags = splits[2:]
        sources.append(DataSource(type_, url, tags))
    return sources

def parse_sources_file(filepath):
    """
    Parse file on disk
    
    :returns: List of data sources, [:class:`DataSource`]
    :raises: :exc:`InvalidSourcesFile`
    """
    try:
        with open(filepath, 'r') as f:
            parse_sources_data(f.read())
    except IOError as e:
        raise InvalidSourcesFile("I/O error reading sources file [%s]: %s"%(e))

def parse_sources_list(sources_list_dir=None):
    """
    :returns: List of data sources, [:class:`DataSource`]
    :raises: :exc:`InvalidSourcesFile`
    """
    if sources_list_dir is None:
        source_list_dir = get_sources_list_dir()
    filelist = os.listdir(sources_list_dir)
    sources_list = []
    for f in sorted(filelist):
        filepath = parse_sources_file(os.path.join(sources_list_dir, f))
        parse_sources_file(filepath)
        data_source = DataSource(type_, url, tags, source=filepath)
        sources_list.append(data_source)
    return sources_list

def update_sources_list():
    sources = parse_sources_list()
    write_cache_file(sources_cache_dir, url, rosdep_data)
    
    pass

def load_sources_list():
    sources = parse_sources_list()

def write_cache_file(source_cache_d, filename_key, rosdep_data):
    """
    :param source_cache_d: directory to write cache file to
    :param filename_key: hash of filename is used to store data in
    :param rosdep_data: dictionary of data to serialize as YAML
    :returns: name of file where cache is stored
    """
    sha_hash = hashlib.sha1()
    sha_hash.update(filename_key)
    key_hash = sha_hash.hexdigest()
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
