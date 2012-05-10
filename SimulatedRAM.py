#!/usr/bin/env python
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# SimulatedRAM.py
# Version: 0.0.1
# By: Shawn Silva (shawn at jatgam dot com)
# Jatgam Computer Simulator
# 
# Created: 03/27/2012
# Modified: 05/10/2012
# 
# Simulates the RAM.
# -----------------------------------------------------------------------------
#
# 
# REQUIREMENTS:
# Python 3.2.x
# 
# Copyright (C) 2012  Jatgam Technical Solutions
# ----------------------------------------------
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                    TODO                                     #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#  - 
# 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                  CHANGELOG                                  #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# 05/10/2012        v0.0.1 - Added to a git repo.        
# 03/27/2012        v0.0.1 - Initial script creation.
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class SimulatedRAM:
    def __init__(self):
    
        ### Hardware Variables ###
        self.ram = [0]*10000        #Machine Memory