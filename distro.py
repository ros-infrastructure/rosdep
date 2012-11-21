import urllib2
import os
import subprocess
import sys
import fnmatch
import yaml
import threading
import time
from Queue import Queue
from threading import Thread

import logging
logger = logging.getLogger('submit_jobs')

## {{{ http://code.activestate.com/recipes/577187/ (r9)
class Worker(Thread):
    """Thread executing tasks from a given tasks queue"""
    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try: func(*args, **kargs)
            except Exception, e: 
                logger.error(e)
            self.tasks.task_done()

class ThreadPool:
    """Pool of threads consuming tasks from a queue"""
    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads): Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        self.tasks.join()

class RosDistro:
    def __init__(self, name, prefetch_dependencies=False, prefetch_upstream=False):
        url = urllib2.urlopen('https://raw.github.com/ros/rosdistro/master/releases/%s.yaml'%name)
        distro = yaml.load(url.read())['repositories']
        self.repositories = {}
        self.packages = {}
        for repo_name, data in distro.iteritems():
            distro_pkgs = []
            url = data['url']
            version = data['version']
            if not data.has_key('packages'):   # support unary disto's
                data['packages'] = {repo_name: ''}
            for pkg_name in data['packages'].keys():
                pkg = RosDistroPackage(pkg_name, repo_name, url, version)
                distro_pkgs.append(pkg)
                self.packages[pkg_name] = pkg
            self.repositories[repo_name] = RosDistroRepo(repo_name, url, version, distro_pkgs)

        # prefetch package dependencies
        if prefetch_dependencies:
            self.prefetch_package_dependencies()

        # prefetch distro upstream
        if prefetch_upstream:
            self.prefetch_repository_upstream()



    def prefetch_package_dependencies(self):
        threadpool = ThreadPool(5)

        # add jobs to queue
        for name, pkg in self.packages.iteritems():
            threadpool.add_task(pkg.get_dependencies)

        # wait for queue to be finished
        failed = []
        logger.info("Waiting for prefetching of package dependencies to finish")
        for name, pkg in self.packages.iteritems():
            count = 0
            while not pkg.depends1:
                time.sleep(0.1)
                count += 1
                if not count%10:
                    logger.info("Still waiting for package %s to complete"%pkg.name)
            if pkg.depends1 == "Failure":
                logger.info("Failed to complete package %s"%pkg.name)
                failed.append(name)

        # remove failed packages
        logger.info("Could not fetch dependencies of the following packages from githib; pretending they do not exist: %s"%', '.join(failed))
        for f in failed:
            if self.repositories.has_key(self.packages[f].repo):
                self.repositories.pop(self.packages[f].repo)
            self.packages.pop(f)
        logger.info("All package dependencies have been prefetched")


    def prefetch_repository_upstream(self):
        threadpool = ThreadPool(5)

        # add jobs to queue
        for name, repo in self.repositories.iteritems():
            threadpool.add_task(repo.get_upstream)

        # wait for queue to be finished
        for name, repo in self.repositories.iteritems():
            while not repo.upstream:
                time.sleep(0.1)


    def depends1(self, package, dep_type):
        if type(package) == list:
            res = []
            for p in package:
                res.append(self.depends1(p, dep_type))
            return res
        else:
            dep_list = dep_type if type(dep_type) == list else [dep_type]
            for dt in dep_list:
                d = self.packages[package].get_dependencies()[dt]
            logger.info("%s depends on %s"%(package, str(d)))
            return d



    def depends(self, package, dep_type, res=[]):
        if type(package) == list:
            for p in package:
                self.depends(p, dep_type, res)
        else:
            for d in self.depends1(package, dep_type):
                if d in self.packages and not d in res:
                    res.append(d)
                    self.depends(d, dep_type, res)
        return res


    def depends_on1(self, package, dep_type):
        if type(package) == list:
            res = []
            for p in package:
                res.append(self.depends_on1(p, dep_type))
            return res
        else:
            depends_on1 = []
            for name, pkg in self.packages.iteritems():
                dep_list = dep_type if type(dep_type) == list else [dep_type]
                for dt in dep_list:
                    if package in pkg.get_dependencies()[dt]:
                        depends_on1.append(name)
            return depends_on1


    def depends_on(self, package, dep_type, res=[]):
        if type(package) == list:
            for p in package:
                self.depends_on(p, dep_type, res)
        else:
            for d in self.depends_on1(package, dep_type):
                if d in self.packages and not d in res:
                    res.append(d)
                    self.depends_on(d, dep_type, res)
        return res

class RosDistroRepo:
    def __init__(self, name, url, version, pkgs):
        self.name = name
        self.url = url
        if version:
            self.version = version.split('-')[0]
        else:
            self.version = version
        self.pkgs = pkgs
        self.upstream = None

    def get_rosinstall_release(self, version=None):
        rosinstall = ""
        for p in self.pkgs:
            rosinstall += p.get_rosinstall_release(version)
        return rosinstall

    def get_rosinstall_latest(self):
        rosinstall = ""
        for p in self.pkgs:
            rosinstall += p.get_rosinstall_latest()
        return rosinstall

    def get_upstream(self):
        if not self.upstream:
            url = self.url
            url = url.replace('.git', '/bloom/bloom.conf')
            url = url.replace('git://', 'https://')
            url = url.replace('https://', 'https://raw.')
            retries = 5
            while not self.upstream and retries > 0:
                res = {'version': ''}
                repo_conf = urllib2.urlopen(url).read()
                for r in repo_conf.split('\n'):
                    conf = r.split(' = ')
                    if conf[0] == '\tupstream':
                        res['url'] = conf[1]
                    if conf[0] == '\tupstreamtype':
                        res['type'] = conf[1]
                    if conf[0] == '\tupstreamversion':
                        res['version'] = conf[1]
                if res['version'] == '':
                    if res['type'] == 'git':
                        res['version'] = 'master'
                    if res['type'] == 'hg':
                        res['version'] = 'default'
                self.upstream = res

                # fix for svn trunk
                if res['type'] == 'svn':
                    res['url'] += "/trunk"
        return self.upstream

class RosDistroPackage:
    def __init__(self, name, repo, url, version):
        self.name = name
        self.repo = repo
        self.url = url
        if version:
            self.version = version.split('-')[0]
            self.depends1 = None
        else:
            self.version = version
            self.depends1 = {'build': [], 'test': [], 'run': []}

    def get_dependencies(self):
        if self.depends1:
            return self.depends1

        url = self.url
        url = url.replace('.git', '/release/%s/%s/package.xml'%(self.name, self.version))
        url = url.replace('git://', 'https://')
        url = url.replace('https://', 'https://raw.')
        retries = 5
        while retries > 0:
            try:
                package_xml = urllib2.urlopen(url).read()
                from catkin_pkg import package as catkin_pkg
                pkg = catkin_pkg.parse_package_string(package_xml)
                self.depends1 = {'build': [d.name for d in pkg.build_depends], 'test':  [d.name for d in pkg.test_depends], 'run': [d.name for d in pkg.run_depends]}
                return self.depends1
            except:
                logger.info("!!!! Failed to download package.xml for package %s at url %s"%(self.name, url))
                time.sleep(2.0)
                retries -= 1

        if not self.depends1:
            self.depends1 = "Failure"
            raise BuildException("Failed to get package.xml at %s"%url)

    def get_rosinstall_release(self, version=None):
        if not version:
            version = self.version
        return yaml.safe_dump([{'git': {'local-name': self.name, 'uri': self.url, 'version': '?'.join(['release', self.name, version])}}],
                              default_style=False).replace('?', '/')

    def get_rosinstall_latest(self):
        return yaml.dump([{'git': {'local-name': self.name, 'uri': self.url, 'version': '/'.join(['release', self.name])}}],
                         default_style=False)

class BuildException(Exception):
    def __init__(self, msg):
        self.msg = msg
