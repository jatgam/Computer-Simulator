#!/usr/bin/env python
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# ComputerSimulator.py
# By: Shawn Silva (ssilva at jatgam dot com)
# Jatgam Computer Simulator
# 
# Simulates the CPU, Memory, Disk, and OS of a computer allowing you to create
# and run simple assembly programs.
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
import sys
import math

from computersimulator.hardware.SimulatedCPU import SimulatedCPU
from GeneralFunctions import *

class ComputerSimulator:
    
    ### System Calls ###
    TASK_CREATE = 0                 #Create Task
    TASK_DELETE = 1                 #Delete Task
    TASK_INQUIRY = 5                #Task Inquiry
    MEM_ALLOC = 8                   #Allocate Memory
    MEM_FREE = 9                    #Release Memory
    MSG_QSEND = 12                  #Send message to queue
    MSG_QRECIEVE = 13               #Recieve message from queue
    IO_GETC = 14                    #Get one character
    IO_PUTC = 15                    #Display one character
    TIME_GET = 16                   #Get the time
    TIME_SET = 17                   #Set the time
    
    ### OS Values ###
    OSMODE = 1
    USERMODE = 0
    EOL = -1                        #End of List
    DFLT_USR_PRTY = 127             #Default Priority
    USER_STACK_SIZE = 10            #Default User Stack Size
    PCBSIZE = 25                    #Default PCB Size
    READY = 1                       #Process Ready Status
    WAITING = 2                     #Process Waiting Status
    EXECUTING = 0                   #Process Executing Status
    TIMESLICE = 1                   #Time Slice Expired
    WAITINGMSG = 2                  #waiting for message
    WAITINGGET = 3                  #waiting for input
    WAITINGPUT = 4                  #waiting to output
    HALT = -20                      #halt status
    
    osFreeList = EOL                #OS Free Mem List
    userFreeList = EOL              #User Free Mem List
    pid = 0                         #Process ID
    RQptr = EOL						#Ready Queue Pointer
    WQptr = EOL						#waiting queue pointer
    RunningPCBptr = EOL				#Whats currently Running
    
    ### Interrupts ###
    NO_INT = 0                      #No interrupts
    INPUT_INT = 1                   #Read one character
    OUTPUT_INT = 2                  #Output one character
    RUN_INT = 3                     #Run user program
    SHUTDOWN_INT = 4                #shutdown system
    
    ### Disk File System Values ###
    PARTITION_TYPE = 42             #Made up Partition Type ID
    FAT_SIZE = 20                   #Size of FAT in sectors
    BTMP_FREE = 0                   #Bitmap Sector Free
    BTMP_USED = 1                   #Bitmap Sector Used
    BTMP_SYS = 2                    #Bitmap Sector Used by System    
    BTMP_INV = -1                   #Bitmap Sector is out of Partition/Invalid
    
    
    def __init__(self):
        self.scpu = SimulatedCPU()
    
    def initializeSystem(self):
        """Sets all hardware variables to zero. Initializes the user and OS
        free lists."""
        self.scpu.sp = 0
        self.scpu.pc = 0
        self.scpu.ir = 0
        self.scpu.psr = self.OSMODE
        self.scpu.clock = 0
        for curgpr in range(len(self.scpu.gpr)):
            self.scpu.gpr[curgpr] = 0
        for mempos in range(len(self.scpu.sram.ram)):
            self.scpu.sram.ram[mempos] = 0
        self._checkDisk()
        #Initialize User Free List
        self.userFreeList = 3000
        self.scpu.sram.ram[3000] = self.EOL
        self.scpu.sram.ram[3001] = 4000;
        #Initialize OS Free List
        self.osFreeList = 7000;
        self.scpu.sram.ram[7000] = self.EOL
        self.scpu.sram.ram[7001] = 3000;

    def _checkDisk(self):
        if (self.scpu.sdisk.disk[0] == [0]*self.scpu.sdisk.SECTOR_SIZE):
            #Disk Not Formatted!
            print("Disk not formatted, proceeding with format.")
            self._formatDisk()
        elif (numJoin(self.scpu.sdisk.disk[0][0:2]) != PARTITION_TYPE):
            print("Unsupported File System! Quitting!")
            sys.exit()
        else:
            return True
    
    def _formatDisk(self):
        """
        Writes the MBR and creates a partition on disk.
        
        Also, loads the OS boot code. In this case, and Idle process.
        """
        idle = [0,6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1]
        part1size = self.scpu.sdisk.NUM_SECTORS-1
        part1fatStart = int(part1size/2)
        part1bitmapsize = math.ceil(part1size/self.scpu.sdisk.SECTOR_SIZE)
        #Creating the MBR
        self.scpu.sdisk.disk[0][0:2] = numSplit(self.PARTITION_TYPE)
        self.scpu.sdisk.disk[0][2:8] = numSplit(format(1, "06d"))
        self.scpu.sdisk.disk[0][8:14] = numSplit(format(part1size, "06d"))
        #Creating First Sector of Partition
        self.scpu.sdisk.disk[1][0:6] = numSplit(format(part1fatStart, "06d"))
        self.scpu.sdisk.disk[1][6:12] = numSplit(format(self.FAT_SIZE, "06d"))
        self.scpu.sdisk.disk[1][12:18] = numSplit(format(2, "06d"))
        self.scpu.sdisk.disk[1][18:24] = numSplit(format(part1bitmapsize, "06d"))
        self.scpu.sdisk.disk[1][110:128] = list(idle)
        #Initializing Sector Bitmap
        slack = self.scpu.sdisk.SECTOR_SIZE-(part1size%self.scpu.sdisk.SECTOR_SIZE)
        self.partBitmapUpdate(2,8,part1size+1,slack,self.BTMP_INV)
        self.partBitmapUpdate(2,8,1,1,self.BTMP_SYS)
        self.partBitmapUpdate(2,8,2,8,self.BTMP_SYS)
        self.partBitmapUpdate(2,8,part1fatStart,self.FAT_SIZE,self.BTMP_SYS)
    
    def partBitmapUpdate(self, bitstart, bitsize, start, size, op):
        """Updates the bitmap and either marks free, used, or system."""
        bstartsec = math.ceil(start/self.scpu.sdisk.SECTOR_SIZE)-1
        bendsec = math.ceil((start+size)/self.scpu.sdisk.SECTOR_SIZE)-1
        if (start <= self.scpu.sdisk.SECTOR_SIZE):
            if (bstartsec == bendsec):
                if (start-1 == 0):
                    self.scpu.sdisk.disk[bitstart+bstartsec][start-1:size] = [op]*size
                else:
                    self.scpu.sdisk.disk[bitstart+bstartsec][start-1:size+1] = [op]*size
            else:
                offset = start
                newstart = self.scpu.sdisk.SECTOR_SIZE+1
                while (offset <= self.scpu.sdisk.SECTOR_SIZE):
                    self.scpu.sdisk.disk[bitstart+bstartsec][offset-1] = op
                    offset += 1
                    size -= 1
                self.partBitmapUpdate(bitstart, bitsize, newstart, size, op)
        else:
            offset = start%self.scpu.sdisk.SECTOR_SIZE
            if (bstartsec == bendsec):
                if (offset-1 == 0):
                    self.scpu.sdisk.disk[bitstart+bstartsec][offset-1:size] = [op]*size
                else:
                    self.scpu.sdisk.disk[bitstart+bstartsec][offset-1:size+1] = [op]*size
            else:
                newstart = (start+size)-((start+size)%self.scpu.sdisk.SECTOR_SIZE)+1
                while (offset <= self.scpu.sdisk.SECTOR_SIZE):
                    self.scpu.sdisk.disk[bitstart+bstartsec][offset-1] = op
                    offset += 1
                    size -= 1
                self.partBitmapUpdate(bitstart, bitsize, newstart, size, op)
    
    def dumpMemory(self, title, start, end):
        """
        Prints out the values of GPRs, selected RAM locations, and the clock
        in a formatted fashion.
        """
        numValues = end - start
        numLines = numValues/10
        if (numValues%10 != 0):
            numLines += 1
        curIndex = start - start%10
        print("----------------------------------------")
        print(title)
        print("----------------------------------------")
        print("GPRs:\t", end='')
        for gpr in range(len(self.scpu.gpr)):
            print(str(self.scpu.gpr[gpr]) + "\t", end='')
        print(str(self.scpu.sp)+"\t"+str(self.scpu.pc)+"\n")
        print("Address:+0\t+1\t+2\t+3\t+4\t+5\t+6\t+7\t+8\t+9\t")
        while (numLines >= 0):
            print(str(curIndex)+"\t", end='')
            for i in range(0,10):
                print(str(self.scpu.sram.ram[curIndex])+"\t", end='')
                curIndex += 1
            print("\n")
            numLines -= 1
        print("Clock = "+str(self.scpu.clock))
        print("PSR: "+str(self.scpu.psr))
        print("----------------------------------------")
        print("End: "+title)
        print("----------------------------------------")
        
    def printPCB(self, pcbptr):
        """Prints a given PCB's Values."""
        line = pcbptr = pcbptr%10
        curIndex = pcbptr
        num = 0
        offset = pcbptr%10
        print("Printing PCB for PID "+str(self.scpu.sram.ram[pcbptr+3])+":")
        print(str(pcbptr)+":\t+0\t+1\t+2\t+3\t+4\t+5\t+6\t+7\t+8\t+9\t")
        while (num <= 25):
            print(str(line)+"\t", end='')
            while (offset > 0):
                print("\t", end='')
                offset -= 1
            line += 10
            for i in range(0,10):
                if (num >= 25):
                    print("\n", end='')
                    return
                else:
                    num += 1
                print(str(self.scpu.sram.ram[curIndex])+"\t", end='')
                curIndex += 1
                if (curIndex%10 == 0):
                    break
            print("\n", end='')
            
    def printRQ(self, queuePTR):
        """Steps through the RQ and prints each PCB."""
        ptr = queuePTR
        if (ptr == self.EOL):
            print("--------------")
            print("|RQ is empty.|")
            print("--------------")
        else:
            print("--------------")
            print("|Printing RQ.|")
            print("--------------")
            while (ptr != self.EOL):
                self.printPCB(ptr)
                ptr = self.scpu.sram.ram[ptr]
                if (ptr != self.EOL):
                    print("--------------")
            print("--------------")
            print("| End of RQ. |")
            print("--------------")
        
    def printWQ(self, queuePTR):
        """Steps through the WQ and prints each PCB."""
        ptr = queuePTR
        if (ptr == self.EOL):
            print("--------------")
            print("|WQ is empty.|")
            print("--------------")
        else:
            print("--------------")
            print("|Printing WQ.|")
            print("--------------")
            while (ptr != self.EOL):
                self.printPCB(ptr)
                ptr = self.scpu.sram.ram[ptr]
                if (ptr != self.EOL):
                    print("--------------")
            print("--------------")
            print("| End of WQ. |")
            print("--------------")
            
    def printRunningP(self, runningPTR):
        """Prints the PCB for the running process."""
        if (runningPTR == self.EOL):
            print("-------------------------------")
            print("|     No Running Process.     |")
            print("-------------------------------")
        else:
            print("-------------------------------")
            print("|Printing Running Process PCB.|")
            print("-------------------------------")
            self.printPCB(runningPTR)
            print("-------------------------------")
            print("|End of Running Process PCB.|")
            print("-------------------------------")
        
if __name__=="__main__":
    comp = ComputerSimulator()
    comp.initializeSystem()
    print(comp.scpu.sdisk.disk[0:10])
    #comp.printRQ(comp.RQptr)
    #comp.dumpMemory("trial", 2999, 3050)
    #print(comp.sdisk.disk[0])
    #print(len(comp.sdisk.disk[0]))
    #print(comp.sdisk.disk[1])
    #print(len(comp.sdisk.disk[1]))
    #print(len(comp.sdisk.disk))