#!/usr/bin/env python

from distutils.core import setup

setup(name='ai-tools',
      version='9.1',
      description='Tools for Agile Infrastructure project',
      author='AI Config Team',
      author_email='ai-config-team@cern.ch',
      url='http://www.cern.ch/ai',
      package_dir= {'': 'src'},
      packages=['aitools'],
      scripts=['bin/ai-add-param', 'bin/ai-bs-vm',
        'bin/ai-kill-vm', 'bin/ai-rebuild-vm', 'bin/ai-ipmi',
        'bin/ai-remote-power-control', 'bin/ai-hiera',
        'bin/ai-rename-host', 'bin/ai-set-fe', 'bin/tbag',
        'bin/ai-qai', 'bin/ai-whatfe', 'bin/ai-installhost',
        'bin/ai-foreman'],
     )
