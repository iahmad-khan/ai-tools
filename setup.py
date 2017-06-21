#!/usr/bin/env python

from distutils.core import setup

setup(name='ai-tools',
      version='10.1.0',
      description='Tools for Agile Infrastructure project',
      author='AI Config Team',
      author_email='ai-config-team@cern.ch',
      url='http://www.cern.ch/ai',
      package_dir= {'': 'src'},
      packages=['aitools'],
      scripts=[
        'bin/ai-add-param',
        'bin/ai-bs-vm',
        'bin/ai-disownhost',
        'bin/ai-foreman',
        'bin/ai-hiera',
        'bin/ai-installhost',
        'bin/ai-ipmi',
        'bin/ai-kill-vm',
        'bin/ai-modulesync',
        'bin/ai-pwn',
        'bin/ai-rc',
        'bin/ai-rebuild-vm',
        'bin/ai-remote-power-control',
        'bin/ai-rename-host',
        'bin/ai-set-fe',
        'bin/ai-whatfe',
        'bin/tbag'
      ],
)
