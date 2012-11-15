#!/usr/bin/env python
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# SimulatedRAM.py
# By: Shawn Silva (ssilva at jatgam dot com)
# Jatgam Computer Simulator
# 
# Simulates the RAM.
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

class SimulatedRAM:
    RAMSIZE = 10000
    def __init__(self):
        ### Hardware Variables ###
        self.ram = [0]*self.RAMSIZE        #Machine Memory