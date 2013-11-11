#!/usr/bin/env python

from distutils.core import setup

setup(name='ai-tools',
      version='5.3',
      description='Tools for Agile Infrastructure project',
      author='Nacho Barrientos',
      author_email='ai-config-team@cern.ch',
      url='http://www.cern.ch/ai',
      package_dir= {'': 'src'},
      packages=['aitools'],
      scripts=['bin/ai-bs-vm', 'bin/ai-kill-vm',
        'ai-remote-power-control'],
     )
