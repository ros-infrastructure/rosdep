from django.shortcuts import render_to_response
from django.template import RequestContext
from prerelease_website.rosinstall_gen.distro import generate_rosinstall
from prerelease_website.rosinstall_gen.old_distro import generate_dry_rosinstall

import logging
logger = logging.getLogger('submit_jobs')

# Create your views here.
def dry_raw(request, distro, variant):
    rosinstall = generate_dry_rosinstall(distro, variant)
    return render_to_response('rosinstall.html', {'rosinstall': rosinstall})

def dry_index(request, distro, packages):
    logger.info('Distro: %s' % distro)
    logger.info('Packages: %s' % packages.split(','))
    return render_to_response('index.html', {'distro': distro, 
                                             'packages': packages.split(','),
                                             'dry': 'true',
                                            },
                                             context_instance=RequestContext(request))
def raw(request, distro, packages):
    rosinstall = generate_rosinstall(distro, packages.split(','))
    return render_to_response('rosinstall.html', {'rosinstall': rosinstall})

def index(request, distro, packages):
    logger.info('Distro: %s' % distro)
    logger.info('Packages: %s' % packages.split(','))
    return render_to_response('index.html', {'distro': distro, 
                                             'packages': packages.split(','), 
                                             'dry': 'false'},
                                             context_instance=RequestContext(request))
