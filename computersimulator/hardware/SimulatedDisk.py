#!/usr/bin/env python
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# SimulatedDisk.py
# By: Shawn Silva (ssilva at jatgam dot com)
# Jatgam Computer Simulator
#
# Simulates the Disk.
# -----------------------------------------------------------------------------
#
# REQUIREMENTS:
# Python 3.2.x
#
# Copyright (C) 2012  Jatgam Technical Solutions
# ----------------------------------------------
# This file is part of Jatgam Computer Simulator.
#
# Jatgam Computer Simulator is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Jatgam Computer Simulator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Jatgam Computer Simulator.  If not, see <http://www.gnu.org/licenses/>.
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
import pickle

class SimulatedDisk:

    SECTOR_SIZE = 128               #in "bytes"
    NUM_SECTORS = 1000              #Size of disk

    def __init__(self, path):
        self.diskpath = path
        self.disk = self._loadDisk(path)
        self.cache = False

    def _loadDisk(self, path):
        try:
            dskfile = open(path, 'r+b')
        except:
            return -1
        try:
            disk = pickle.load(dskfile)
            dskfile.close()
            return disk
        except EOFError:
            disk = self._initializeDisk(dskfile)
            dskfile.close()
            return  disk

    def _initializeDisk(self, dskfile):
        #fs = [[0]*self.SECTOR_SIZE]*self.NUM_SECTORS
        fs = []
        sector = [0]*self.SECTOR_SIZE
        for i in range(0,self.NUM_SECTORS):
            fs.append(list(sector))
        pickle.dump(fs, dskfile)
        return fs

    def writeCache(self):
        dskfile = open(self.diskpath, 'r+b')
        dskfile.truncate()
        pickle.dump(self.disk, dskfile)
