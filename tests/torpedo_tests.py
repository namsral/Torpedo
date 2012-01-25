#!/usr/bin/env python
# -*- coding: utf-8 -*-

import NAME
import unittest

class TestSequenceFunctions(unittest.TestCase):
    
    def setUp(self):
        print "Setup."
    
    def test_first(self):
        print "First test."

if __name__ == '__main__':
    unittest.main()