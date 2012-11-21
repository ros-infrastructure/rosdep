from django.shortcuts import render_to_response
from django.template import RequestContext
import logging
logger = logging.getLogger('submit_jobs')

# Create your views here.
def index(request, distro, packages):
    logger.info('Distro: %s' % distro)
    logger.info('Packages: %s' % packages.split(','))
    return render_to_response('index.html', {})
