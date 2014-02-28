#!/usr/bin/python

__author__ = 'bejones'

import glob
import unittest
import os


def buildTestSuite():
    suite = unittest.TestSuite()
    for testcase in glob.glob('tests/test_*.py'):
        modname = os.path.splitext(testcase)[0]
        module = __import__(modname,{},{},['1'])
        suite.addTest(unittest.TestLoader().loadTestsFromModule(module))
    return suite


def main():
    suite = buildTestSuite()
    unittest.TextTestRunner().run(suite)


if __name__ == '__main__'():
    main()

