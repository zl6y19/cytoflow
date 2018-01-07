#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2017
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
Created on Dec 1, 2015

@author: brian
'''
import unittest, os, tempfile, shutil

import matplotlib
matplotlib.use('Agg')

import cytoflow as flow

class Test(unittest.TestCase):

    def setUp(self):
        self.cwd = os.path.dirname(os.path.abspath(__file__)) + "/data/Plate01/"
        tube1 = flow.Tube(file = self.cwd + 'RFP_Well_A3.fcs', conditions = {"Dox" : 10.0})
        tube2 = flow.Tube(file= self.cwd + 'CFP_Well_A4.fcs', conditions = {"Dox" : 1.0})
        import_op = flow.ImportOp(conditions = {"Dox" : "float"},
                                  tubes = [tube1, tube2])
        self.ex = import_op.apply()
        
        self.directory = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.directory)
        
    def testRoundtrip(self):
        flow.ExportFCS(path = self.directory,
                       by = ['Dox']).export(self.ex)
                       
        tube1 = flow.Tube(file = self.directory + '/Dox_10.0.fcs', 
                          conditions = {"Dox" : 10.0})
        tube2 = flow.Tube(file = self.directory + '/Dox_1.0.fcs',
                          conditions = {"Dox" : 1.0})
        
        ex_rt = flow.ImportOp(conditions = {"Dox" : "float"},
                              tubes = [tube1, tube2]).apply()

        self.assertTrue((self.ex.data == ex_rt.data).all().all())


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()