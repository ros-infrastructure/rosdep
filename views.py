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
                                             'gen_type': 'dry',
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
                                             'gen_type': 'wet'},
                                             context_instance=RequestContext(request))

def combined_raw(request, distro, variant):
    dry_rs = generate_dry_rosinstall(distro, variant)
    wet_rs = generate_rosinstall(distro, variant)
    combined = dry_rs + wet_rs
    return render_to_response('rosinstall.html', {'rosinstall': combined})

def combined_index(request, distro, packages):
    logger.info('Distro: %s' % distro)
    logger.info('Packages: %s' % packages.split(','))
    return render_to_response('index.html', {'distro': distro, 
                                             'packages': packages.split(','), 
                                             'gen_type': 'combined'},
                                             context_instance=RequestContext(request))

