#!/usr/bin/env python
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# GeneralFunctions.py
# By: Shawn Silva (ssilva at jatgam dot com)
# Part of Jatgam Computer Simulator
#
# General Functions.
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

def numJoin(numList):
    return int(''.join(map(str,numList)))

def numSplit(num):
    return list(map(int,str(num)))
