import os
import distutils.version
import urllib2
import json

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse #py3k

GITHUB_V2_API_REPOS = 'https://github.com/api/v2/json/repos/'
PATTERN_GITHUB_V2_API_REPOS_SHOW_TAGS = GITHUB_V2_API_REPOS + 'show/%(org_name)s/%(repo_name)s/tags'
# include extra filename on the end to help brew with its infererence rules.  Github should ignore them.
PATTERN_GITHUB_TARBALL_DOWNLOAD = 'https://github.com/%(org_name)s/%(repo_name)s/tarball/%(tag_name)s/%(repo_name)s-%(version)s.tar.gz'

def get_api(api_pattern, org_name, repo_name):
    return api_pattern%locals()

def list_tags(org_name, repo_name, prefix):
    f = urllib2.urlopen(get_api(PATTERN_GITHUB_V2_API_REPOS_SHOW_TAGS, org_name, repo_name))
    json_data = json.load(f)
    f.close()
    return [t for t in json_data['tags'].keys() if t.startswith(prefix)]

def get_org_name(url):
    parsed = urlparse.urlparse(url)
    org_name = os.path.dirname(parsed.path)
    if org_name.startswith('git@github.com:'):
        org_name = org_name[len('git@github.com:'):]
    return org_name

def get_repo_name(url):
    repo_name = os.path.basename(url)
    if repo_name.endswith('.git'):
        repo_name = repo_name[:-4]
    return repo_name

def compute_tarball_url_for_latest(org_name, repo_name):
    """
    Compute the latest upstream tag and return a github.com download URL for that tarball
    """
    prefix = 'upstream/'
    tags = list_tags(org_name, repo_name, prefix)
    versions = sorted([distutils.version.LooseVersion(t[len(prefix):]) for t in tags])
    version = versions[-1].vstring #for pattern
    tag_name = 'upstream/%s'%(version)
    return PATTERN_GITHUB_TARBALL_DOWNLOAD%locals()

