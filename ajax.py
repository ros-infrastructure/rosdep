from django.conf import settings
from dajaxice.decorators import dajaxice_register
from django.utils import simplejson
import datetime
import os
import yaml
from prerelease_website.rosinstall_gen.distro import RosDistro

import logging
logger = logging.getLogger('submit_jobs')

#Generates a rosinstall file for a package and it's dependences
def generate_rosinstall(distro_name, packages):
    packages = packages if type(packages) == list else [packages]
    distro = RosDistro(distro_name, prefetch_dependencies=False, prefetch_upstream=False)
    deps = distro.depends(packages, ['build', 'run'])

    rosinstall = ""
    for p in list(set(deps + packages)):
        rosinstall += distro.packages[p].get_rosinstall_release()
    return rosinstall


@dajaxice_register
def get_rosinstall_ajax(request, distro, packages):
    logger.info("Got distro %s, packages %s" % (distro, packages))
    timestr = datetime.datetime.now().strftime("%Y%m%d-%H%M%S%f")
    filename = '%s.rosinstall' % '_'.join(packages)
    relative_dir = os.path.join('rosinstalls', timestr)
    path = os.path.join(settings.MEDIA_ROOT, relative_dir, filename)
    logger.info("Writing rosinstall file to %s" % path)
    try:
        os.makedirs(os.path.realpath(os.path.dirname(path)))
    except:
        pass

    rosinstall = generate_rosinstall(distro, packages)

    with open(path, 'w+') as f:
        f.write(rosinstall)
        #yaml.dump(rosinstall, f, default_flow_style=False)

    return simplejson.dumps({'rosinstall_url': os.path.join(relative_dir,
                                                            filename)})
