#!/usr/bin/env python3
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
# Python 3.7.x
#
# Copyright (C) 2012-2019  Jatgam Technical Solutions
# ----------------------------------------------
# This file is part of Jatgam Computer Simulator.
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
import argparse
import logging
import os
from pathlib import Path
import sys
import math

from tkinter import filedialog
from tkinter import Tk

from computersimulator.hardware.SimulatedCPU import SimulatedCPU
import computersimulator.utils.listutils as listutils
import computersimulator.constants as constants

CONST = constants.Constants

class ComputerSimulator:

    osFreeList = CONST.EOL  # OS Free Mem List
    userFreeList = CONST.EOL  # User Free Mem List
    pid = 0  # Process ID
    RQptr = CONST.EOL  # Ready Queue Pointer
    WQptr = CONST.EOL  # waiting queue pointer
    RunningPCBptr = CONST.EOL  # Whats currently Running

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.scpu = SimulatedCPU()

    def initializeSystem(self):
        """Sets all hardware variables to zero. Initializes the user and OS
        free lists."""
        self.scpu.sp = 0
        self.scpu.pc = 0
        self.scpu.ir = 0
        self.scpu.psr = CONST.OSMODE
        self.scpu.clock = 0
        for curgpr in range(len(self.scpu.gpr)):
            self.scpu.gpr[curgpr] = 0
        for mempos in range(len(self.scpu.sram.ram)):
            self.scpu.sram.ram[mempos] = 0
        self._checkDisk()
        #Initialize User Free List
        self.userFreeList = 3000
        self.scpu.sram.ram[3000] = CONST.EOL
        self.scpu.sram.ram[3001] = 4000
        #Initialize OS Free List
        self.osFreeList = 7000
        self.scpu.sram.ram[7000] = CONST.EOL
        self.scpu.sram.ram[7001] = 3000

    def _checkDisk(self):
        if (self.scpu.sdisk.disk[0] == [0]*self.scpu.sdisk.sectorSize):
            #Disk Not Formatted!
            print("Disk not formatted, proceeding with format.")
            self._formatDisk()
        elif (listutils.numJoin(self.scpu.sdisk.disk[0][0:2]) != CONST.PARTITION_TYPE):
            print("Unsupported File System! Quitting!")
            sys.exit()
        else:
            return True

    def _formatDisk(self):
        """
        Writes the MBR and creates a partition on disk.

        Also, loads the OS boot code. In this case, and Idle process.
        """
        idle = [0, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1]
        part1size = self.scpu.sdisk.numSectors-1
        part1fatStart = int(part1size/2)
        part1bitmapsize = math.ceil(part1size/self.scpu.sdisk.sectorSize)
        #Creating the MBR
        self.scpu.sdisk.disk[0][0:2] = listutils.numSplit(CONST.PARTITION_TYPE)
        self.scpu.sdisk.disk[0][2:8] = listutils.numSplit(format(1, "06d"))
        self.scpu.sdisk.disk[0][8:14] = listutils.numSplit(
            format(part1size, "06d"))
        #Creating First Sector of Partition
        self.scpu.sdisk.disk[1][0:6] = listutils.numSplit(
            format(part1fatStart, "06d"))
        self.scpu.sdisk.disk[1][6:12] = listutils.numSplit(
            format(CONST.FAT_SIZE, "06d"))
        self.scpu.sdisk.disk[1][12:18] = listutils.numSplit(format(2, "06d"))
        self.scpu.sdisk.disk[1][18:24] = listutils.numSplit(
            format(part1bitmapsize, "06d"))
        self.scpu.sdisk.disk[1][110:128] = list(idle)
        #Initializing Sector Bitmap
        slack = self.scpu.sdisk.sectorSize - \
            (part1size % self.scpu.sdisk.sectorSize)
        self.partBitmapUpdate(2, 8, part1size+1, slack, CONST.BTMP_INV)
        self.partBitmapUpdate(2, 8, 1, 1, CONST.BTMP_SYS)
        self.partBitmapUpdate(2, 8, 2, 8, CONST.BTMP_SYS)
        self.partBitmapUpdate(2, 8, part1fatStart,
                              CONST.FAT_SIZE, CONST.BTMP_SYS)

    def partBitmapUpdate(self, bitstart, bitsize, start, size, op):
        """Updates the bitmap and either marks free, used, or system."""
        bstartsec = math.ceil(start/self.scpu.sdisk.sectorSize)-1
        bendsec = math.ceil((start+size)/self.scpu.sdisk.sectorSize)-1
        if (start <= self.scpu.sdisk.sectorSize):
            if (bstartsec == bendsec):
                if (start-1 == 0):
                    self.scpu.sdisk.disk[bitstart
                                         + bstartsec][start-1:size] = [op]*size
                else:
                    self.scpu.sdisk.disk[bitstart
                                         + bstartsec][start-1:size+1] = [op]*size
            else:
                offset = start
                newstart = self.scpu.sdisk.sectorSize+1
                while (offset <= self.scpu.sdisk.sectorSize):
                    self.scpu.sdisk.disk[bitstart+bstartsec][offset-1] = op
                    offset += 1
                    size -= 1
                self.partBitmapUpdate(bitstart, bitsize, newstart, size, op)
        else:
            offset = start % self.scpu.sdisk.sectorSize
            if (bstartsec == bendsec):
                if (offset-1 == 0):
                    self.scpu.sdisk.disk[bitstart
                                         + bstartsec][offset-1:size] = [op]*size
                else:
                    self.scpu.sdisk.disk[bitstart
                                         + bstartsec][offset-1:size+1] = [op]*size
            else:
                newstart = (start+size)-((start+size) %
                                         self.scpu.sdisk.sectorSize)+1
                while (offset <= self.scpu.sdisk.sectorSize):
                    self.scpu.sdisk.disk[bitstart+bstartsec][offset-1] = op
                    offset += 1
                    size -= 1
                self.partBitmapUpdate(bitstart, bitsize, newstart, size, op)

    def systemCall(self, sysCallID):
        """
        Takes the supplied sysCallID and performs the correct system call.
        Prints out messages for what system call is performed and what process
        asked for it.
        """
        status = 0
        self.scpu.psr = CONST.OSMODE
        if (sysCallID == CONST.TASK_CREATE):
            self.taskCreate()
            print("-------------------------------")
            print("System Call Recieved: task_create")
            print("PID that issued: {}".format(self.scpu.sram.ram[self.RunningPCBptr+3]))
            print("Input: Address of first Instruction: {}".format(self.scpu.gpr[3]))
            print("Output: PID of Child: {}, Status: {}".format(self.scpu.gpr[2], self.scpu.gpr[0]))
            print("-------------------------------")
        elif (sysCallID == CONST.TASK_DELETE):
            status = self.taskDelete()
            print("-------------------------------")
            print("System Call Recieved: task_delete")
            print("PID that issued: {}".format(self.scpu.sram.ram[self.RunningPCBptr+3]))
            print("Input: PID to delete: {}".format(self.scpu.gpr[1]))
            print("Output: Status: {}".format(self.scpu.gpr[0]))
            print("-------------------------------")
            if (status == CONST.HALT):
                self.scpu.psr = CONST.USERMODE
                return CONST.HALT
        elif (sysCallID == CONST.TASK_INQUIRY):
            self.taskInquiry()
            print("-------------------------------")
            print("System Call Recieved: task_inquiry")
            print("PID that issued: {}".format(self.scpu.sram.ram[self.RunningPCBptr+3]))
            print("Output: PID: {}, Priority: {}, State: {}".format(self.scpu.gpr[1], self.scpu.gpr[2], self.scpu.gpr[3]))
            print("-------------------------------")
        elif (sysCallID == CONST.MEM_ALLOC):  # Mem Alloc System Call
            status = self.mem_alloc(self.scpu.gpr[2])  # Allocate memory with size GPR2
            print("-------------------------------")
            print("System Call Recieved: mem_alloc")
            print("PID that issued: {}".format(self.scpu.sram.ram[self.RunningPCBptr+3]))
            print("Input: Size: {}".format(self.scpu.gpr[2]))
            print("Output: Start Address: {}".format(self.scpu.gpr[1]))
            print("-------------------------------")
        elif (sysCallID == CONST.MEM_FREE):  # Mem Free System Call
            status = self.mem_free(self.scpu.gpr[1], self.scpu.gpr[2])
            print("-------------------------------")
            print("System Call Recieved: mem_free")
            print("PID that issued: {}".format(self.scpu.sram.ram[self.RunningPCBptr+3]))
            print("Input: Size: {}, Start: {}".format(self.scpu.gpr[2], self.scpu.gpr[1]))
            print("-------------------------------")
        elif (sysCallID == CONST.MSG_QSEND):
            status = self.msgQsend()
            if (status == CONST.ER_TID):
                print("-------------------------------")
                print("System Call Recieved: msg_qsend")
                print("PID that issued: {}".format(self.scpu.sram.ram[self.RunningPCBptr+3]))
                print("Output: PID Invalid")
                print("-------------------------------")
            else:
                print("-------------------------------")
                print("System Call Recieved: msg_qsend")
                print("PID that issued: {}".format(self.scpu.sram.ram[self.RunningPCBptr+3]))
                print("Output: Message Sent")
                print("-------------------------------")
        elif (sysCallID == CONST.MSG_QRECIEVE):
            ptr = self.RunningPCBptr
            status = self.msgQRecieve()
            if (status == CONST.WAITING):
                print("-------------------------------")
                print("System Call Recieved: msg_qrecieve")
                print("PID that issued: {}".format(self.scpu.sram.ram[ptr+3]))
                print("Output: Waiting for message")
                print("-------------------------------")
                self.scpu.psr = CONST.USERMODE
                return CONST.WAITING
            else:
                print("-------------------------------")
                print("System Call Recieved: msg_qrecieve")
                print("PID that issued: {}".format(self.scpu.sram.ram[ptr+3]))
                print("Output: Got Message")
                print("-------------------------------")
        elif (sysCallID == CONST.IO_GETC):
            self.scpu.sram.ram[self.RunningPCBptr+4] = CONST.WAITINGGET
            self.scpu.sram.ram[self.RunningPCBptr+1] = CONST.WAITING
            print("-------------------------------")
            print("System Call Recieved: io_getc")
            print("PID that issued: {}".format(self.scpu.sram.ram[self.RunningPCBptr+3]))
            print("Output: Waiting for Input Completion")
            print("-------------------------------")
            self.scpu.psr = CONST.USERMODE
            return CONST.WAITING
        elif (sysCallID == CONST.IO_PUTC):
            self.scpu.sram.ram[self.RunningPCBptr+4] = CONST.WAITINGGET
            self.scpu.sram.ram[self.RunningPCBptr+1] = CONST.WAITING
            print("-------------------------------")
            print("System Call Recieved: io_putc")
            print("PID that issued: {}".format(self.scpu.sram.ram[self.RunningPCBptr+3]))
            print("Output: Waiting for Output Completion")
            print("-------------------------------")
            self.scpu.psr = CONST.USERMODE
            return CONST.WAITING
        elif (sysCallID == CONST.TIME_GET):
            self.scpu.gpr[1] = self.scpu.clock
            print("-------------------------------")
            print("System Call Recieved: time_get")
            print("PID that issued: {}".format(self.scpu.sram.ram[self.RunningPCBptr+3]))
            print("Output: Time: {}".format(self.scpu.gpr[1]))
            print("-------------------------------")
        elif (sysCallID == CONST.TIME_SET):
            self.scpu.clock = self.scpu.gpr[1]
            print("-------------------------------")
            print("System Call Recieved: time_set")
            print("PID that issued: {}".format(self.scpu.sram.ram[self.RunningPCBptr+3]))
            print("Input: Time: {}".format(self.scpu.gpr[1]))
            print("-------------------------------")
        else:
            self.scpu.psr = CONST.USERMODE
            return CONST.ER_ISC
        self.scpu.psr = CONST.USERMODE
        return status

    def mem_alloc(self, size):
        """
        System Call,Takes supplied size of memory allocation and tries to
        allocate the memory. Returns the status and teh start of the address
        to GPRs 0 and 1

        Parameters: 
            size            size of the memory to be allocated

        Returns:
            status          status of the  memory allocation
        """
        status = self.allocateUserMemory(size)
        if (status >= 0):
            self.scpu.gpr[1] = status  # GPR1 Gets pointer to memory
            self.scpu.gpr[0] = CONST.OK  # GPR0 Gets OK Status
        else:
            self.scpu.gpr[0] = status  # GPR0 gets error status
        return status

    def mem_free(self, start, size):
        """
        System Call, Take the supplied start address and size of memory to free
        and tries to free it. Returns the status.

        Parameters:
            start           start address of memory
            size            size of memory to be freed

        Returns:
            status          status of the system call
        """
        status = self.freeUserMemory(start, size)
        return status

    def allocateUserMemory(self, size):
        """
        Takes the supplied size of memory and attempts to allocate it. Searches
        through the userFreeList looking for a block.

        Parameters:
            size            size of memory to be allocated

        Returns:
            ptr             Pointer to the start of mem location
            ER_MEM          No Memory available.
        """
        ptr = self.userFreeList
        previousPtr = CONST.EOL
        while (ptr != CONST.EOL):
            if (self.scpu.sram.ram[ptr+1] >= size):
                break  # Found Free Block
            else:
                previousPtr = ptr
                ptr = self.scpu.sram.ram[ptr]
        # Check Various Cases
        if (ptr == CONST.EOL):
            return CONST.ER_MEM  # No Memory Available
        if (self.scpu.sram.ram[ptr+1] == size):
            # Found equal size block, check for first block
            if (ptr == self.userFreeList):
                # First block equal size
                self.userFreeList = self.scpu.sram.ram[ptr]
                self.scpu.sram.ram[ptr] = CONST.EOL
                return ptr
            else:
                # Middle Block Equal Size
                self.scpu.sram.ram[previousPtr] = self.scpu.sram.ram[ptr]
                self.scpu.sram.ram[ptr] = CONST.EOL
                return ptr
        else:  # Found bigger block, check for first block
            if (ptr == self.userFreeList):  # First Block
                # First block bigger, modify size userFreeList
                self.userFreeList = ptr + size
                self.scpu.sram.ram[ptr+size] = self.scpu.sram.ram[ptr]
                self.scpu.sram.ram[ptr+size+1] = self.scpu.sram.ram[ptr+1] - size
                self.scpu.sram.ram[ptr] = CONST.EOL
                return ptr
            else:  # Not first block
                # Middle block larger size
                self.scpu.sram.ram[ptr+size] = self.scpu.sram.ram[ptr]
                self.scpu.sram.ram[ptr+size+1] = self.scpu.sram.ram[ptr+1] - size
                self.scpu.sram.ram[previousPtr] = self.scpu.sram.ram[ptr+size]
                self.scpu.sram.ram[ptr] = CONST.EOL
                return ptr

    def allocateOSMemory(self, size):
        """
        Takes the supplied size of memory and attempts to allocate it. Searches
        through the osFreeList looking for a block.

        Parameters:
            size            size of memory to be allocated

        Returns:
            ptr             Pointer to the start of mem location
            ER_MEM          No Memory available.
        """
        ptr = self.osFreeList
        previousPtr = CONST.EOL
        while (ptr != CONST.EOL):
            if (self.scpu.sram.ram[ptr+1] >= size):
                break  # Found Free Block
            else:
                previousPtr = ptr
                ptr = self.scpu.sram.ram[ptr]
        # Check Various Cases
        if (ptr == CONST.EOL):
            return CONST.ER_MEM  # No Memory Available
        if (self.scpu.sram.ram[ptr+1] == size):
            # Found equal size block, check for first block
            if (ptr == self.osFreeList):
                # First block equal size
                self.osFreeList = self.scpu.sram.ram[ptr]
                self.scpu.sram.ram[ptr] = CONST.EOL
                return ptr
            else:
                # Middle Block Equal Size
                self.scpu.sram.ram[previousPtr] = self.scpu.sram.ram[ptr]
                self.scpu.sram.ram[ptr] = CONST.EOL
                return ptr
        else:  # Found bigger block, check for first block
            if (ptr == self.osFreeList):  # First Block
                # First block bigger, modify size osFreeList
                self.osFreeList = ptr + size
                self.scpu.sram.ram[ptr+size] = self.scpu.sram.ram[ptr]
                self.scpu.sram.ram[ptr+size+1] = self.scpu.sram.ram[ptr+1] - size
                self.scpu.sram.ram[ptr] = CONST.EOL
                return ptr
            else:  # Not first block
                # Middle block larger size
                self.scpu.sram.ram[ptr+size] = self.scpu.sram.ram[ptr]
                self.scpu.sram.ram[ptr+size+1] = self.scpu.sram.ram[ptr+1] - size
                self.scpu.sram.ram[previousPtr] = self.scpu.sram.ram[ptr+size]
                self.scpu.sram.ram[ptr] = CONST.EOL
                return ptr

    def freeUserMemory(self, start, size):
        """
        Takes the supplied start address and size of memory block and frees it
        from the userFreeList. Adds to correct location in the freeList.

        Parameters:
            start           Start of address of memory
            size            size of memory to free
        
        Returns:
            status
        """
        status = 0
        ptr = self.userFreeList
        previousPtr = CONST.EOL
        if (ptr == CONST.EOL):  # All Memory Used
            self.userFreeList = start
            self.scpu.sram.ram[start] = CONST.EOL
            self.scpu.sram.ram[start+1] = size
        else:
            if (ptr-(start+size) == 0):  # Blocks next to each other at beinning
                self.scpu.sram.ram[start] = self.scpu.sram.ram[ptr]
                self.scpu.sram.ram[start+1] = size + self.scpu.sram.ram[ptr+1]
                self.userFreeList = start
                self.scpu.sram.ram[ptr] = 0
                self.scpu.sram.ram[ptr+1] = 0
                return CONST.OK
            else:
                while (ptr != CONST.EOL):
                    previousPtr = ptr
                    ptr = self.scpu.sram.ram[ptr]
                    if (ptr-(start+size) == 0):
                        # Blocks Next to each other in middle
                        if (start-(previousPtr+self.scpu.sram.ram[previousPtr+1]) == 0):
                            # Between two blocks
                            self.scpu.sram.ram[previousPtr+1] = size + self.scpu.sram.ram[ptr+1] + self.scpu.sram.ram[previousPtr+1]
                            self.scpu.sram.ram[previousPtr] = self.scpu.sram.ram[ptr]
                            self.scpu.sram.ram[ptr] = 0
                            self.scpu.sram.ram[ptr+1] = 0
                            return CONST.OK
                        else:
                            # Next to block
                            self.scpu.sram.ram[start] = self.scpu.sram.ram[ptr]
                            self.scpu.sram.ram[start+1] = size + self.scpu.sram.ram[ptr+1]
                            self.scpu.sram.ram[previousPtr] = start
                            self.scpu.sram.ram[ptr] = 0
                            self.scpu.sram.ram[ptr+1] = 0
                            return CONST.OK
                # Block at end of list
                if (start-(previousPtr+self.scpu.sram.ram[previousPtr+1]) == 0):
                    self.scpu.sram.ram[previousPtr+1] = size + self.scpu.sram.ram[previousPtr+1]
                    return CONST.OK
                else:
                    self.scpu.sram.ram[start] = CONST.EOL
                    self.scpu.sram.ram[start+1] = size
                    self.scpu.sram.ram[previousPtr] = start
                    return CONST.OK
        return status

    def freeOSMemory(self, start, size):
        """
        Takes the supplied start address and size of memory block and frees it
        from the osFreeList. Adds to correct location in the freeList.

        Parameters:
            start           Start of address of memory
            size            size of memory to free
        
        Returns:
            status
        """
        status = 0
        ptr = self.osFreeList
        previousPtr = CONST.EOL
        if (ptr == CONST.EOL):  # All Memory Used
            self.osFreeList = start
            self.scpu.sram.ram[start] = CONST.EOL
            self.scpu.sram.ram[start+1] = size
        else:
            if (ptr-(start+size) == 0):  # Blocks next to each other at beinning
                self.scpu.sram.ram[start] = self.scpu.sram.ram[ptr]
                self.scpu.sram.ram[start+1] = size + self.scpu.sram.ram[ptr+1]
                self.osFreeList = start
                self.scpu.sram.ram[ptr] = 0
                self.scpu.sram.ram[ptr+1] = 0
                return CONST.OK
            else:
                while (ptr != CONST.EOL):
                    previousPtr = ptr
                    ptr = self.scpu.sram.ram[ptr]
                    if (ptr-(start+size) == 0):
                        # Blocks Next to each other in middle
                        if (start-(previousPtr+self.scpu.sram.ram[previousPtr+1]) == 0):
                            # Between two blocks
                            self.scpu.sram.ram[previousPtr+1] = size + self.scpu.sram.ram[ptr+1] + self.scpu.sram.ram[previousPtr+1]
                            self.scpu.sram.ram[previousPtr] = self.scpu.sram.ram[ptr]
                            self.scpu.sram.ram[ptr] = 0
                            self.scpu.sram.ram[ptr+1] = 0
                            return CONST.OK
                        else:
                            # Next to block
                            self.scpu.sram.ram[start] = self.scpu.sram.ram[ptr]
                            self.scpu.sram.ram[start+1] = size + self.scpu.sram.ram[ptr+1]
                            self.scpu.sram.ram[previousPtr] = start
                            self.scpu.sram.ram[ptr] = 0
                            self.scpu.sram.ram[ptr+1] = 0
                            return CONST.OK
                # Block at end of list
                if (start-(previousPtr+self.scpu.sram.ram[previousPtr+1]) == 0):
                    self.scpu.sram.ram[previousPtr+1] = size + self.scpu.sram.ram[previousPtr+1]
                    return CONST.OK
                else:
                    self.scpu.sram.ram[start] = CONST.EOL
                    self.scpu.sram.ram[start+1] = size
                    self.scpu.sram.ram[previousPtr] = start
                    return CONST.OK
        return status

    def absoluteLoader(self, filename):
        """
        Passed in filename is opened, parsed line by line, and stored in RAM.
        Values are checked to make sure they are valid. Returns the value of
        the program counter.

        Parameters:
            filename        name of executable file

        Returns:
            0 to 9999       successful load, PC value
            ER_FILEOPEN     unable to open file
            ER_INVALIDADDR  invalid memory address
            ER_NOENDOFPROG  missing end of program indicator
        """
        try:
            programFile = open(filename, "r")
        except:
            return CONST.ER_FILEOPEN
        for programLine in programFile.readlines():
            temp = programLine.split(" ")
            addr = int(temp[0])
            content = int(temp[1], 0)
            if (addr >= 0) and (addr <= 9999):
                self.scpu.sram.ram[addr] = content
            elif (addr == CONST.ENDPROG):
                programFile.close()
                return content
            else:
                programFile.close()
                return CONST.ER_INVALIDADDR
        programFile.close()
        return CONST.ER_NOENDOFPROG

    def createProcess(self, filename, priority):
        """
        Takes a file and tries to laod the program. Allocates necessary user
        and OS memory for the program and creates the PCB. Inserts PCB in RQ.

        Parameters:
            filename        name of the file that contains the program
            priority        priority of the process being created

        Returns:
            OK              successfully created process
            ER_MEM          no memory available
        """
        # Allocate Memory for PCB
        pcbptr = self.allocateOSMemory(CONST.PCBSIZE)
        if (pcbptr < 0):
            return CONST.ER_MEM
        status = self.absoluteLoader(filename)
        if (status < 0):
            return status

        # Set PC in PCB
        self.scpu.sram.ram[pcbptr+14] = status
        # Allocate Message Queue
        msgqid = self.allocateOSMemory(10)
        # Allocate stack from user free list
        ptr = self.allocateUserMemory(CONST.USER_STACK_SIZE)
        if (ptr < 0):
            return CONST.ER_MEM
        else:
            self.scpu.sram.ram[pcbptr+15] = ptr
            self.scpu.sram.ram[pcbptr+16] = CONST.USER_STACK_SIZE
            self.scpu.sram.ram[pcbptr+13] = ptr - 1  # Empty Stack

            # Initialize GPR0-7 to 0 in PCB
            for i in range(8):
                self.scpu.sram.ram[pcbptr+5+i] = 0
            # Set State to ready
            self.scpu.sram.ram[pcbptr+1] = CONST.READY
            # Set Priority
            self.scpu.sram.ram[pcbptr+2] = priority
            # Set PID
            self.scpu.sram.ram[pcbptr+3] = self.pid
            self.pid += 1
            # Reason for waiting
            self.scpu.sram.ram[pcbptr+4] = 0
            # Set msgqueue start address
            self.scpu.sram.ram[pcbptr+17] = msgqid
            # Set message queue size
            self.scpu.sram.ram[pcbptr+18] = 10
            # set number of messages in queue
            self.scpu.sram.ram[pcbptr+19] = 0

            # Insert into RQ
            self.insertRQ(pcbptr)
            print("--------------------------")
            print("|Process Created PCB Dump|")
            print("--------------------------")
            self.printPCB(pcbptr)
            print("------------------------------")
            print("|End Process Created PCB Dump|")
            print("------------------------------")
            return status

    def taskCreate(self):
        """
        System call, creates a child process of a program already loaded.

        Returns:
            OK              successfully created process
            ER_MEM          no memory available
        """
        # Allocate memory for pcb
        pcbptr = self.allocateOSMemory(CONST.PCBSIZE)
        # Set PC in PCB
        self.scpu.sram.ram[pcbptr+14] = self.scpu.gpr[3]
        # Allocate message queue
        msgqid = self.allocateOSMemory(10)
        # Allocate stack from user free list
        ptr = self.allocateUserMemory(CONST.USER_STACK_SIZE)
        if (ptr < 0):
            return CONST.ER_MEM
        else:
            self.scpu.sram.ram[pcbptr+15] = ptr
            self.scpu.sram.ram[pcbptr+16] = CONST.USER_STACK_SIZE
            self.scpu.sram.ram[pcbptr+13] = ptr - 1  # Empty Stack

            # Initialize GPR0-7 to 0 in PCB
            for i in range(8):
                self.scpu.sram.ram[pcbptr+5+i] = 0
            # Set State to ready
            self.scpu.sram.ram[pcbptr+1] = CONST.READY
            # Set Priority
            self.scpu.sram.ram[pcbptr+2] = CONST.DFLT_USR_PRTY
            # Set PID
            self.scpu.sram.ram[pcbptr+3] = self.pid
            self.pid += 1
            # Reason for waiting
            self.scpu.sram.ram[pcbptr+4] = 0
            # Set msgqueue start address
            self.scpu.sram.ram[pcbptr+17] = msgqid
            # Set message queue size
            self.scpu.sram.ram[pcbptr+18] = 10
            # set number of messages in queue
            self.scpu.sram.ram[pcbptr+19] = 0

            # Insert into RQ
            self.insertRQ(pcbptr)
            self.scpu.gpr[2] = self.scpu.sram.ram[pcbptr+3]
            self.scpu.gpr[0] = CONST.OK
            print("--------------------------")
            print("| Task Created PCB Dump  |")
            print("--------------------------")
            self.printPCB(pcbptr)
            print("------------------------------")
            print("| End Task Created PCB Dump  |")
            print("------------------------------")
            return CONST.OK

    def taskDelete(self):
        """
        System Call, deletes a child process

        Returns:
            status
        """
        if (self.scpu.gpr[1] == 0):
            return CONST.HALT
        if (self.scpu.gpr[1] > 0):
            # Search WQ
            pcbptr = self.searchRemoveWQ(self.scpu.gpr[1])
            if (pcbptr == CONST.EOL):
                pcbptr = self.searchRemoveRQ(self.scpu.gpr[1])
                if (pcbptr == CONST.EOL):
                    if (self.scpu.sram.ram[self.RunningPCBptr+3] == self.scpu.gpr[1]):
                        return CONST.HALT
                    else:
                        self.scpu.gpr[0] = CONST.ER_TID
                        return CONST.OK
                else:  # Found in RQ
                    self.terminateProcess(pcbptr)
                    self.scpu.gpr[0] = CONST.OK
                    return CONST.OK
            else:  # Found in WQ
                self.terminateProcess(pcbptr)
                self.scpu.gpr[0] = CONST.OK
                return CONST.OK
        else:  # PID < 0
            self.scpu.gpr[0] = CONST.ER_TID
            return CONST.OK

    def terminateProcess(self, pcbptr):
        """
        Free the memory of the supplied process using the pointer

        Parameters:
            pcbptr      Pointer to the process to terminate
        """
        self.freeUserMemory(self.scpu.sram.ram[pcbptr+15], self.scpu.sram.ram[pcbptr+16])
        self.freeOSMemory(pcbptr, CONST.PCBSIZE)

    def selectProcess(self):
        """
        Selects a process from the Ready Queue. Removes that process from the
        RQ and returns the ptr to the selected process.

        Returns:
            pcbptr      ptr to chosen process
        """
        pcbptr = self.RQptr
        self.removeFromRQ()
        return pcbptr

    def saveCPUContext(self, pcbptr):
        """
        Saves the current register status into the PCB for the running process

        Parameters:
            pcbptr      pointer to pcb
        """
        self.scpu.sram.ram[pcbptr+5] = self.scpu.gpr[0]
        self.scpu.sram.ram[pcbptr+6] = self.scpu.gpr[1]
        self.scpu.sram.ram[pcbptr+7] = self.scpu.gpr[2]
        self.scpu.sram.ram[pcbptr+8] = self.scpu.gpr[3]
        self.scpu.sram.ram[pcbptr+9] = self.scpu.gpr[4]
        self.scpu.sram.ram[pcbptr+10] = self.scpu.gpr[5]
        self.scpu.sram.ram[pcbptr+11] = self.scpu.gpr[6]
        self.scpu.sram.ram[pcbptr+12] = self.scpu.gpr[7]
        self.scpu.sram.ram[pcbptr+13] = self.scpu.sp
        self.scpu.sram.ram[pcbptr+14] = self.scpu.pc

    def dispatcher(self, pcbptr):
        """
        Sets the registers from the PCB supplied

        Parameters:
            pcbptr      pointer to pcb
        """
        self.scpu.gpr[0] = self.scpu.sram.ram[pcbptr+5]
        self.scpu.gpr[1] = self.scpu.sram.ram[pcbptr+6]
        self.scpu.gpr[2] = self.scpu.sram.ram[pcbptr+7]
        self.scpu.gpr[3] = self.scpu.sram.ram[pcbptr+8]
        self.scpu.gpr[4] = self.scpu.sram.ram[pcbptr+9]
        self.scpu.gpr[5] = self.scpu.sram.ram[pcbptr+10]
        self.scpu.gpr[6] = self.scpu.sram.ram[pcbptr+11]
        self.scpu.gpr[7] = self.scpu.sram.ram[pcbptr+12]
        self.scpu.sp = self.scpu.sram.ram[pcbptr+13]
        self.scpu.pc = self.scpu.sram.ram[pcbptr+14]
        self.scpu.psr = CONST.USERMODE

    def processInterrupts(self):
        """Display a list of valid interrupts, waits for user input. Performs
        the requested interrupt.

        Returns:
            0           No Interrupts/Successful Process
            ER_INT      Invalid Interrupt
            ER_FILEOPEN file not found
        """
        print("------------------------")
        print("Processing Interrupts: ")
        print("0: No interrupt")
        print("1: Read Character")
        print("2: Output Character")
        print("3: Run Program")
        print("4: Shutdown")
        interruptId = input("Interrupt ID: ")
        try: 
            interruptId = int(interruptId)
        except:
            return CONST.ER_INT
        if (interruptId == CONST.NO_INT):  # No Interrupt
            print("0: No Interrupt!")
            return CONST.OK
        elif (interruptId == CONST.INPUT_INT):  # Read Char
            print("1: Read Input!")
            self.inputCompletionInterrupt()
            return CONST.OK
        elif (interruptId == CONST.OUTPUT_INT):  # Output Char
            print("2: Output Character!")
            self.outputCompletionInterrupt()
            return CONST.OK
        elif (interruptId == CONST.RUN_INT):  # Run Program
            root = Tk()
            root.withdraw()
            fileToOpen = filedialog.askopenfilename(initialdir=Path(sys.path[0]+"/programs/machinecode"), title="Select Program", filetypes=(("Programs","*.txt"),("all files","*.*")))
            root.destroy()
            if (os.path.isfile(fileToOpen)):
                print("3: Run Program!")
                status = self.createProcess(fileToOpen, CONST.DFLT_USR_PRTY)
                self.dumpMemory("Program Area after Process Creation Memory Dump", 0, 130)
                return status
            else:
                return CONST.ER_FILEOPEN
        elif ( interruptId == CONST.SHUTDOWN_INT):  # Shutdown
            while (self.RQptr != CONST.EOL):  # Terminate Ready Processes
                ptr = self.scpu.sram.ram[self.RQptr]
                self.terminateProcess(self.RQptr)
                self.RQptr = ptr
            while (self.WQptr != CONST.EOL):  # Terminate Waiting Processes
                ptr = self.scpu.sram.ram[self.WQptr]
                self.terminateProcess(self.WQptr)
                self.WQptr = ptr
            print("4: System Shutting Down!")
            self.logger.info("System Shutting Down")
            sys.exit(0)
        else:  # Invalid Interrupt
            return CONST.ER_INT

    def inputCompletionInterrupt(self):
        """
        Simulates interrupt to read from the keyboard. Takes PID out of WQ,
        reads a character and puts in GPR2. Puts process in RQ.

        Returns:
            0       Successful Read
        """
        inputPid = input("Enter PID of Process needing Input: ")
        try:
            inputPid = int(inputPid)
        except:
            return CONST.ER_TID
        pcbptr = self.searchRemoveWQ(inputPid)
        if (pcbptr == CONST.EOL):
            return CONST.ER_TID
        print(inputPid)
        inputChar = input("Type a character: ")
        self.scpu.sram.ram[pcbptr+6] = ord(inputChar[0])
        self.scpu.sram.ram[pcbptr+5] = CONST.OK
        self.scpu.sram.ram[pcbptr+1] = CONST.READY
        self.insertRQ(pcbptr)
        return CONST.OK

    def outputCompletionInterrupt(self):
        """
        Simulates interrupt to read from keyboard. Takes PID out of WQ, reads
        a character and puts in GPR2. Puts process in RQ.

        Returns:
            0       successful output
        """
        outputPid = input("Enter PID of Process needing Output: ")
        try:
            outputPid = int(outputPid)
        except:
            return CONST.ER_TID
        pcbptr = self.searchRemoveWQ(outputPid)
        if (pcbptr == CONST.EOL):
            return CONST.ER_TID
        print(outputPid)
        outputChar = chr(self.scpu.sram.ram[pcbptr+6])
        print("Output: {}".format(outputChar))
        self.scpu.sram.ram[pcbptr+5] = CONST.OK
        self.scpu.sram.ram[pcbptr+1] = CONST.READY
        self.insertRQ(pcbptr)
        return CONST.OK

    def searchRemoveWQ(self, findpid):
        """
        Takes a given PID, searches for it in the WQ, if found removes it and
        returns the PCB ptr. Otherwise returns not found

        Parameters:
            findpid     pid of process to find

        Returns:
            EOL         Pid not found
            ptr         ptr to pid in pcb
        """
        ptr = self.WQptr
        previousPtr = CONST.EOL
        if (ptr == CONST.EOL):  # Queue empty, not found
            return CONST.EOL
        else:
            while (ptr != CONST.EOL):
                if (self.scpu.sram.ram[ptr+3] == findpid):  # Pid Found
                    if (previousPtr == CONST.EOL):
                        self.WQptr = self.scpu.sram.ram[ptr]
                        self.scpu.sram.ram[ptr] = CONST.EOL
                        return ptr
                    else:
                        self.scpu.sram.ram[previousPtr] = self.scpu.sram.ram[ptr]
                        self.scpu.sram.ram[ptr] = CONST.EOL
                        return ptr
                else:
                    previousPtr = ptr
                    ptr = self.scpu.sram.ram[ptr]
            return CONST.EOL

    def searchRemoveRQ(self, findpid):
        """
        Takes a given PID, searches for it in the RQ, if found removes it and
        returns the PCB ptr. Otherwise returns not found

        Parameters:
            findpid     pid of process to find

        Returns:
            EOL         Pid not found
            ptr         ptr to pid in pcb
        """
        ptr = self.RQptr
        previousPtr = CONST.EOL
        if (ptr == CONST.EOL):  # Queue empty, not found
            return CONST.EOL
        else:
            while (ptr != CONST.EOL):
                if (self.scpu.sram.ram[ptr+3] == findpid):  # Pid Found
                    if (previousPtr == CONST.EOL):
                        self.RQptr = self.scpu.sram.ram[ptr]
                        self.scpu.sram.ram[ptr] = CONST.EOL
                        return ptr
                    else:
                        self.scpu.sram.ram[previousPtr] = self.scpu.sram.ram[ptr]
                        self.scpu.sram.ram[ptr] = CONST.EOL
                        return ptr
                else:
                    previousPtr = ptr
                    ptr = self.scpu.sram.ram[ptr]
            return CONST.EOL

    def insertRQ(self, pcbptr):
        """
        Takes a pcbptr and puts in the correct place in RQ using Priority
        Round Robin.

        Parameters:
            pcbptr          pointer to pcb to put in RQ
        """
        ptr = self.RQptr
        previousPtr = CONST.EOL
        if (pcbptr >= 7000) and (pcbptr <= 9974):  # Valid pcbptr
            if (self.RQptr == CONST.EOL):  # Rq Empty
                self.RQptr = pcbptr
                return
            else:  # RQ has entries, search through and insert correctly
                while (ptr != CONST.EOL):
                    if (self.scpu.sram.ram[pcbptr+2] <= self.scpu.sram.ram[ptr+2]):
                        previousPtr = ptr
                        ptr = self.scpu.sram.ram[ptr]
                    else:  # Found place to insert
                        # Insert between previous ptr and ptr
                        # 1, the beginning
                        if (ptr == self.RQptr):
                            self.scpu.sram.ram[pcbptr] = self.RQptr
                            self.RQptr = pcbptr
                            return
                        else:
                            # Insert in middle
                            self.scpu.sram.ram[pcbptr] = ptr
                            self.scpu.sram.ram[previousPtr] = pcbptr
                            return
                # Insert at end of RQ
                self.scpu.sram.ram[previousPtr] = pcbptr
                return
        else:  # Invalid pcbptr
            return

    def insertWQ(self, pcbptr):
        """
        Takes a pcbptr and puts in the correct place in WQ using Priority
        Round Robin.

        Parameters:
            pcbptr          pointer to pcb to put in RQ
        """
        ptr = self.WQptr
        previousPtr = CONST.EOL
        if (pcbptr >= 7000) and (pcbptr <= 9974):  # Valid pcbptr
            if (self.WQptr == CONST.EOL):  # Rq Empty
                self.WQptr = pcbptr
                return
            else:  # RQ has entries, search through and insert correctly
                while (ptr != CONST.EOL):
                    if (self.scpu.sram.ram[pcbptr+2] <= self.scpu.sram.ram[ptr+2]):
                        previousPtr = ptr
                        ptr = self.scpu.sram.ram[ptr]
                    else:  # Found place to insert
                        # Insert between previous ptr and ptr
                        # 1, the beginning
                        if (ptr == self.WQptr):
                            self.scpu.sram.ram[pcbptr] = self.WQptr
                            self.WQptr = pcbptr
                            return
                        else:
                            # Insert in middle
                            self.scpu.sram.ram[pcbptr] = ptr
                            self.scpu.sram.ram[previousPtr] = pcbptr
                            return
                # Insert at end of RQ
                self.scpu.sram.ram[previousPtr] = pcbptr
                return
        else:  # Invalid pcbptr
            return

    def removeFromRQ(self):
        """
        Takes the first entry from the RQ and removes from the list.
        """
        pcbptr = self.RQptr
        self.RQptr = self.scpu.sram.ram[pcbptr]
        self.scpu.sram.ram[pcbptr] = CONST.EOL

    def removeFromWQ(self):
        """
        Takes the first entry from the WQ and removes from the list.
        """
        pcbptr = self.WQptr
        self.WQptr = self.scpu.sram.ram[pcbptr]
        self.scpu.sram.ram[pcbptr] = CONST.EOL

    def searchPID(self, pid):
        """
        Search through the WQ and RQ for a PID

        Parameters:
            pid         pid of process to find

        Returns:
            pcbptr      ptr to pid
            EOL         pid not found
        """
        ptr = self.WQptr
        while (ptr != CONST.EOL):
            if (self.scpu.sram.ram[ptr+3] == pid):
                return ptr
            else:
                ptr = self.scpu.sram.ram[ptr]
        ptr = self.RQptr
        while (ptr != CONST.EOL):
            if (self.scpu.sram.ram[ptr+3] == pid):
                return ptr
            else:
                ptr = self.scpu.sram.ram[ptr]
        return CONST.EOL

    def msgQsend(self):
        """
        System call, Sends a message with a start address of GPR2 to PID in
        GPR1
        """
        # GPR1 has process PID
        # GPR2 has start address of message
        # Set GPR0 to status when done
        pctptr = self.searchPID(self.scpu.gpr[1])  # Search WQ and RQ for pid
        if (pctptr == CONST.EOL):  # Invalid PID
            self.scpu.gpr[0] = CONST.ER_TID  # Error, invalid PID
            return CONST.ER_TID
        msgaddr = self.scpu.sram.ram[pctptr+17]
        msgcount = self.scpu.sram.ram[pctptr+19]
        self.scpu.sram.ram[msgaddr+msgcount] = self.scpu.gpr[2]
        self.scpu.sram.ram[pctptr+19] += 1
        self.scpu.sram.ram[pctptr+7] = self.scpu.gpr[2]
        self.scpu.gpr[0] = CONST.OK
        return CONST.OK

    def msgQRecieve(self):
        """
        System Call, tries to retrieve message, if none, waits until one
        arrives
        """
        if (self.scpu.sram.ram[self.RunningPCBptr+19] == 0):  # No message in queue
            self.scpu.sram.ram[self.RunningPCBptr+4] = CONST.WAITINGMSG  # Waiting for msg
            self.scpu.sram.ram[self.RunningPCBptr+1] = CONST.WAITING  # Set state to waiting
            return CONST.WAITING
        # There is a message in the queue
        msgqaddr = self.scpu.sram.ram[self.RunningPCBptr+17]
        self.scpu.gpr[2] = self.scpu.sram.ram[msgqaddr]  # Copy msg start addr to gpr2
        self.scpu.gpr[0] = CONST.OK
        return CONST.OK

    def taskInquiry(self):
        """
        Sets the GPRs to contain information about the running process.
        PID, priority, and state.
        """
        self.scpu.gpr[0] = CONST.OK
        self.scpu.gpr[1] = self.scpu.sram.ram[self.RunningPCBptr+3]  # PID
        self.scpu.gpr[2] = self.scpu.sram.ram[self.RunningPCBptr+2]  # Priority
        self.scpu.gpr[3] = self.scpu.sram.ram[self.RunningPCBptr+1]  # State

    def dumpMemory(self, title, start, end):
        """
        Prints out the values of GPRs, selected RAM locations, and the clock
        in a formatted fashion.
        """
        numValues = end - start
        numLines = numValues/10
        if (numValues % 10 != 0):
            numLines += 1
        curIndex = start - start % 10
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
            for i in range(0, 10):
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
        line = pcbptr - (pcbptr % 10)
        curIndex = pcbptr
        num = 0
        offset = pcbptr % 10
        print("Printing PCB for PID "+str(self.scpu.sram.ram[pcbptr+3])+":")
        print(str(pcbptr)+":\t+0\t+1\t+2\t+3\t+4\t+5\t+6\t+7\t+8\t+9\t")
        while (num <= 25):
            print(str(line)+"\t", end='')
            while (offset > 0):
                print("\t", end='')
                offset -= 1
            line += 10
            for i in range(0, 10):
                if (num >= 25):
                    print("\n", end='')
                    return
                else:
                    num += 1
                print(str(self.scpu.sram.ram[curIndex])+"\t", end='')
                curIndex += 1
                if (curIndex % 10 == 0):
                    break
            print("\n", end='')

    def printRQ(self, queuePTR):
        """Steps through the RQ and prints each PCB."""
        ptr = queuePTR
        if (ptr == CONST.EOL):
            print("--------------")
            print("|RQ is empty.|")
            print("--------------")
        else:
            print("--------------")
            print("|Printing RQ.|")
            print("--------------")
            while (ptr != CONST.EOL):
                self.printPCB(ptr)
                ptr = self.scpu.sram.ram[ptr]
                if (ptr != CONST.EOL):
                    print("--------------")
            print("--------------")
            print("| End of RQ. |")
            print("--------------")

    def printWQ(self, queuePTR):
        """Steps through the WQ and prints each PCB."""
        ptr = queuePTR
        if (ptr == CONST.EOL):
            print("--------------")
            print("|WQ is empty.|")
            print("--------------")
        else:
            print("--------------")
            print("|Printing WQ.|")
            print("--------------")
            while (ptr != CONST.EOL):
                self.printPCB(ptr)
                ptr = self.scpu.sram.ram[ptr]
                if (ptr != CONST.EOL):
                    print("--------------")
            print("--------------")
            print("| End of WQ. |")
            print("--------------")

    def printRunningP(self, runningPTR):
        """Prints the PCB for the running process."""
        if (runningPTR == CONST.EOL):
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

    def OSLoop(self):
        """
        Runs the Main OS loop.
        """
        status = 0

        nullProgram = Path("programs/machinecode/null.txt")
        status = self.createProcess(nullProgram, 0)
        print(status)
        while (status >=0):
            # Process Interrupts at every context switch
            self.processInterrupts()
            # Select Process from RQ to give to CPU
            pcbptr = self.selectProcess()
            self.dispatcher(pcbptr)
            self.RunningPCBptr = pcbptr
            self.printRQ(self.RQptr)
            self.printWQ(self.WQptr)
            self.printRunningP(self.RunningPCBptr)
            self.scpu.psr = CONST.USERMODE
            status = self.scpu.executeProgram(self.systemCall)
            self.dumpMemory("User Dynamic Area Memory Dump", 3000, 3390)
            self.scpu.psr = CONST.OSMODE
            if (status == CONST.TIMESLICE):  # Timeslice expired
                self.saveCPUContext(self.RunningPCBptr)
                self.insertRQ(self.RunningPCBptr)
                self.RunningPCBptr = -1
                continue
            elif (status == CONST.WAITING):  # Process waiting for interrupt
                self.saveCPUContext(self.RunningPCBptr)
                self.insertWQ(self.RunningPCBptr)
                self.RunningPCBptr = -1
                continue
            elif (status == 0):  # Program Halt
                self.terminateProcess(self.RunningPCBptr)
                self.RunningPCBptr = -1
                continue
            else:  # Errors in program
                self.terminateProcess(self.RunningPCBptr)
                self.RunningPCBptr = -1
                continue

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Jatgam Computer Simulator")
    parser.add_argument("--loglevel", choices=["debug", "info", "warn", "warning", "error", "exception", "critical"],
                        default="info", type=str, help="The Log Level")
    args = parser.parse_args()

    numeric_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError("Invalid log level: %s" % args.loglevel)
    logging.basicConfig(level=numeric_level, filename="computersimulator.log",
                        format='[%(levelname)s] %(asctime)s [%(name)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    logger = logging.getLogger(__name__)
    logger.info("Starting Simulator")

    # Computer Loop
    comp = ComputerSimulator()
    comp.initializeSystem()
    comp.OSLoop()
    
    logger.error("Simulator had an error and did not stop cleanly.")
