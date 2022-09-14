# Copyright (c) 2021, Open Source Robotics Foundation, Inc.
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

import base64
import sys
from gzip import GzipFile
from io import BytesIO
try:
    from urllib.request import urlopen
    from urllib.error import URLError
    from urllib.parse import urlparse
    from urllib.parse import urlunparse
    import urllib.request as request
except ImportError:
    from urllib2 import urlopen
    from urllib2 import URLError
    import urllib2 as request
    from urlparse import urlparse
    from urlparse import urlunparse

from ._version import __version__


def urlopen_gzip(url, **kwargs):
    # http/https URLs need custom requests to specify the user-agent, since some repositories reject
    # requests from the default user-agent.
    if url.startswith("http://") or url.startswith("https://"):
        scheme, netloc, path, params, query, frag = urlparse(url)
        auth, host = splituser(netloc)
        url = urlunparse((scheme, host, path, params, query, frag))
        url_request = request.Request(url, headers={
            'Accept-Encoding': 'gzip',
            'User-Agent': 'rosdep/{version}'.format(version=__version__),
        })
        if auth:
            if auth.endswith(":KEYRING"):
                try:
                    import keyring
                    username = auth.split(":")[0]
                    password = keyring.get_password("rosdep", username)
                    auth = "{}:{}".format(username, password)
                except ImportError:
                    print('Cannot import keyring, rosdep will not function properly with passwords stored in keyring',
                          file=sys.stderr)
            if sys.version_info[0] >= 3:
                base64string = base64.b64encode(auth.encode()).decode()
            else:
                base64string = base64.b64encode(auth)
            auth_header = "Basic " + base64string
            url_request.add_header('Authorization', auth_header)
        response = urlopen(url_request, **kwargs)
        if response.info().get('Content-Encoding') == 'gzip':
            buffer = BytesIO(response.read())
            return GzipFile(fileobj=buffer, mode='rb')
        return response

    return urlopen(url, **kwargs)


# copy of urllib.parse._splituser from Python 3.8
# This is required because no fully featured alternative has been provided since splituser was deprecated
# Reference: https://github.com/pypa/setuptools/pull/1670
def splituser(host):
    """splituser('user[:passwd]@host[:port]') --> 'user[:passwd]', 'host[:port]'."""
    user, delim, host = host.rpartition('@')
    return (user if delim else None), host
