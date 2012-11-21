from django.shortcuts import render_to_response
from django.template import RequestContext
from prerelease_website.rosinstall_gen.distro import generate_rosinstall

import logging
logger = logging.getLogger('submit_jobs')

# Create your views here.
def raw(request, distro, packages):
    rosinstall = generate_rosinstall(distro, packages.split(','))
    return render_to_response('rosinstall.html', {'rosinstall': rosinstall})

def index(request, distro, packages):
    logger.info('Distro: %s' % distro)
    logger.info('Packages: %s' % packages.split(','))
    return render_to_response('index.html', {'distro': distro, 'packages':
                                             packages.split(',')},
                                             context_instance=RequestContext(request))
