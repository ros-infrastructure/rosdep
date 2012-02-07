import os
import sys
import urllib2
import yaml

from rospkg.os_detect import OS_UBUNTU

from .core import InvalidData, DownloadFailure
from .platforms.debian import APT_INSTALLER

#py3k
try:
    unicode
except:
    basestring = unicode = str

# location of targets file for processing gbpdistro files
GBP_TARGETS_URL = 'https://raw.github.com/ros/rosdistro/master/releases/targets.yaml'

# location of an example gbpdistro file for reference and testing
FUERTE_GBPDISTRO_URL = 'https://raw.github.com/ros/rosdistro/master/releases/fuerte.yaml'

#seconds to wait before aborting download of gbpdistro data
DOWNLOAD_TIMEOUT = 15.0 

def gbprepo_to_rosdep_data(gbpdistro_data, targets_data):
    """
    :raises: :exc:`InvalidData`
    """
    # Error reporting for this isn't nearly as good as it could be
    # (e.g. doesn't separate gbpdistro vs. targets, nor provide
    # origin), but rushing this implementation a bit.
    try:
        if not type(targets_data) == list:
            raise InvalidData("targets data must be a list")
        if not type(gbpdistro_data) == dict:
            raise InvalidData("gbpdistro data must be a dictionary")        

        # compute the default target data for the release_name
        release_name = gbpdistro_data['release-name']
        target_data = [t for t in targets_data if release_name in t]
        if not target_data:
            raise InvalidData("targets file does not contain information for release [%s]"%(release_name))
        else:
            # take the first match
            target_data = target_data[0][release_name]

        # compute the rosdep data for each repo
        rosdep_data = {}
        gbp_repos = gbpdistro_data['gbp-repos']
        for repo in gbp_repos:
            if type(repo) != dict:
                raise InvalidData("invalid repo spec in gbpdistro data: %s"%(str(repo)))
            rosdep_key = repo['name']
            rosdep_data[rosdep_key] = {}

            # Do generation for ubuntu
            rosdep_data[rosdep_key][OS_UBUNTU] = {}

            # - debian package name: underscores must be dashes
            deb_package_name = 'ros-%s-%s'%(release_name, rosdep_key)
            deb_package_name = deb_package_name.replace('_', '-')

            repo_targets = repo['target']
            if repo_targets == 'all':
                repo_targets = target_data

            for t in repo_targets:
                if not isinstance(t, basestring):
                    raise InvalidData("invalid target spec: %s"%(t))
                rosdep_data[rosdep_key][OS_UBUNTU][t] = {APT_INSTALLER:
                                                         {'packages': [deb_package_name]}}
        return rosdep_data
    except KeyError as e:
        raise InvalidData("Invalid GBP-distro/targets format: missing key: %s"%(str(e)))
    
def download_gbpdistro_as_rosdep_data(gbpdistro_url, targets_url=GBP_TARGETS_URL):
    """
    Download gbpdistro file from web and convert format to rosdep distro data.
    
    :param gbpdistro_url: url of gbpdistro file, ``str``
    :param target_url: override URL of platform targets file
    :raises: :exc:`DownloadFailure`
    """
    # we can convert a gbpdistro file into rosdep data by following a couple rules
    try:
        f = urllib2.urlopen(targets_url, timeout=DOWNLOAD_TIMEOUT)
        text = f.read()
        f.close()
        targets_data = yaml.safe_load(text)
    except Exception as e:
        raise DownloadFailure("Failed to download target platform data for gbpdistro:\n\t%s"%(str(e)))
    try:
        f = urllib2.urlopen(gbpdistro_url, timeout=DOWNLOAD_TIMEOUT)
        text = f.read()
        f.close()
        gbpdistro_data = yaml.safe_load(text)
        return gbprepo_to_rosdep_data(gbpdistro_data, targets_data)
    except Exception as e:
        raise DownloadFailure("Failed to download target platform data for gbpdistro:\n\t%s"%(str(e)))

