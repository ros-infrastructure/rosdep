import urllib2
import yaml
import urlparse
import os.path

from rospkg.os_detect import OS_UBUNTU
from rospkg.os_detect import OS_OSX

from .core import InvalidData, DownloadFailure
from .platforms.debian import APT_INSTALLER
from .platforms.osx import BREW_INSTALLER
from .rep3 import download_targets_data

#py3k
try:
    unicode
except:
    basestring = unicode = str

# location of an example gbpdistro file for reference and testing
FUERTE_GBPDISTRO_URL = 'https://raw.github.com/ros/rosdistro/master/releases/fuerte.yaml'

#seconds to wait before aborting download of gbpdistro data
DOWNLOAD_TIMEOUT = 15.0 

def get_owner_name(url):
    parsed = urlparse.urlparse(url)
    org_name = os.path.dirname(parsed.path).split('/')
    if '' in org_name:
        org_name.remove('')

    org_name = org_name[0]
    if org_name.startswith('git@github.com:'):
        org_name = org_name[len('git@github.com:'):]
    return org_name

def gbprepo_to_rosdep_data(gbpdistro_data, targets_data, url):
    """
    :raises: :exc:`InvalidData`
    """
    # Error reporting for this isn't nearly as good as it could be
    # (e.g. doesn't separate gbpdistro vs. targets, nor provide
    # origin), but rushing this implementation a bit.
    try:
        if not type(targets_data) == dict:
            raise InvalidData("targets data must be a dict")
        if not type(gbpdistro_data) == dict:
            raise InvalidData("gbpdistro data must be a dictionary")
        if gbpdistro_data['type'] != 'gbp':
            raise InvalidData('gbpdistro must be of type "gbp"')

        # compute the default target data for the release_name
        release_name = gbpdistro_data['release-name']
        if not release_name in targets_data:
            raise InvalidData("targets file does not contain information for release [%s]"%(release_name))
        else:
            # take the first match
            target_data = targets_data[release_name]

        # compute the rosdep data for each repo
        rosdep_data = {}
        gbp_repos = gbpdistro_data['repositories']
        for rosdep_key, repo in gbp_repos.items():
            if type(repo) != dict:
                raise InvalidData("invalid repo spec in gbpdistro data: %s"%(str(repo)))
            rosdep_data[rosdep_key] = {}

            # Do generation for ubuntu
            rosdep_data[rosdep_key][OS_UBUNTU] = {}
            # Do generation for empty OS X entries
            homebrew_name = '%s/%s/%s'%(get_owner_name(url), release_name, rosdep_key)
            rosdep_data[rosdep_key][OS_OSX] = {BREW_INSTALLER: {'packages': [homebrew_name]}}

            # - debian package name: underscores must be dashes
            deb_package_name = 'ros-%s-%s'%(release_name, rosdep_key)
            deb_package_name = deb_package_name.replace('_', '-')

            repo_targets = repo['target'] if 'target' in repo else 'all'
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
    
def download_gbpdistro_as_rosdep_data(gbpdistro_url, targets_url=None):
    """
    Download gbpdistro file from web and convert format to rosdep distro data.
    
    :param gbpdistro_url: url of gbpdistro file, ``str``
    :param target_url: override URL of platform targets file
    :raises: :exc:`DownloadFailure`
    :raises: :exc:`InvalidData` If targets file does not pass cursory validation checks.
    """
    # we can convert a gbpdistro file into rosdep data by following a couple rules
    targets_data = download_targets_data(targets_url=targets_url)
    try:
        f = urllib2.urlopen(gbpdistro_url, timeout=DOWNLOAD_TIMEOUT)
        text = f.read()
        f.close()
        gbpdistro_data = yaml.safe_load(text)
        return gbprepo_to_rosdep_data(gbpdistro_data, targets_data, gbpdistro_url)
    except Exception as e:
        raise DownloadFailure("Failed to download target platform data for gbpdistro:\n\t%s"%(str(e)))

