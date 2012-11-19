#!/usr/bin/env python
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# SimulatedCPU.py
# By: Shawn Silva (ssilva at jatgam dot com)
# Part of Jatgam Computer Simulator
# 
# Simulates the CPU.
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
from computersimulator.hardware.SimulatedRAM import SimulatedRAM
from computersimulator.hardware.SimulatedDisk import SimulatedDisk

class SimulatedCPU:
    
    ### Opcodes ###
    OP_HALT = 0                 #Opcode: Halt
    OP_ADD = 1                  #Opcode: Add
    OP_SUB = 2                  #Opcode: Subtract
    OP_MULT = 3                 #Opcode: Multiply
    OP_DIV = 4                  #Opcode: Divide
    OP_MOVE = 5                 #Opcode: Move
    OP_BRANCH = 6               #Opcode: Branch
    OP_BRANCHM = 7              #Opcode: Branch on Minus
    OP_SYSTEM = 8               #Opcode: System Call
    OP_BRANCHP = 9              #Opcode: Branch on Plus
    OP_BRANCHZ = 10             #Opcode: Branch on Zero
    OP_PUSH = 11                #Opcode: Push
    OP_POP = 12                 #Opcode: Pop
    
    MODE_DIRECT = 0             #Mode: Direct
    MODE_REGISTER = 1           #Mode: Register
    MODE_REGDEFERRED = 2        #Mode: Register Deffered
    MODE_AUTOINC = 3            #Mode: Auto Increment
    MODE_AUTODEC = 4            #Mode: Auto Decrement
    MODE_IMMEDIATE = 5          #Mode: Immediate
    
    ENDPROG = -1                #End of Program
    
    ### Return Codes ###
    OK = 0                      #Successful execution
    ER_TID = -1                 #Error: Task ID
    ER_PCB = -2                 #Error: No PCBs available
    ER_MEM = -3                 #Error: No memory available
    ER_NMB = -4                 #Error: Not a memory Block
    ER_ISC = -5                 #Error: Invalid System Call
    ER_TMO = -6                 #Error: Time Out
    ER_NMP = -7                 #Error: No message present
    ER_QID = -8                 #Error: Queue ID
    ER_QFL = -9                 #Error: Queue full
    ER_FILEOPEN = -10           #Error: File Not Found
    ER_INVALIDADDR = -11        #Error: Invalid Memory Address
    ER_NOENDOFPROG = -12        #Error: No end of program
    ER_INVALIDMODE = -13        #Error: Invalid Mode
    ER_OPNOTIMP = -14           #Error: Operand not Implemented
    ER_DIVBYZ = -15             #Error: Divide By Zero
    ER_INVALIDOP = -16          #Error: Invalid Opcode
    ER_INT = -17                #Error: Invalid Interrupts
    ER_PC = -18                 #Error: Invalid PC

    '''
    ### Fetch Operand Variables ###
    opValue
    opAddr
    op1Value
    op1Addr
    op2Value
    op2Addr
    '''
    
    def __init__(self):
        
        ### CPU Hardware Variables ###
        self.gpr = [0]*8        #General Purpose Registers
        self.sp = None          #Stack Pointer
        self.pc = None          #Program Counter
        self.ir = None          #Instruction Register
        self.psr = None         #Processor Status Register
        self.clock = None       #Clock
        ### Other Hardware Accessed by CPU ###
        self.sram = SimulatedRAM()
        self.sdisk = SimulatedDisk("computersimulator/hardware/disks/disk.dsk")
        if (self.sdisk.disk == -1):
            print("Fatal Error! Disk not found!")
            sys.exit()
        print(self._fetchOperand(0,5))
            
    def _fetchOperand(self, mode, reg):
        if (mode == self.MODE_DIRECT):   #Direct Mode
            if (self.pc >= 0) and (self.pc <= 9999):
                opAddr = self.sram.ram[self.pc] #get opAddr using PC
                self.pc += 1
                if (opAddr >= 0) and (opAddr <= 9999):
                    opValue = self.sram.ram[opAddr] #get opValue
                else:
                    return self.ER_INVALIDADDR, None, None
            else:
                return self.ER_INVALIDADDR, None, None
            return self.OK, opAddr, opValue
            
        elif (mode == self.MODE_REGISTER):  #Register Mode
            opAddr = -1 #Not in Memory
            apValue = self.gpr[reg]
            return self.OK, opAddr, opValue
            
        elif (mode == self.MODE_REGDEFERRED):   #Register Deferred Mode
            opAddr = self.gpr[reg]
            if (opAddr >= 0) and (opAddr <= 9999):
                opValue = self.ram[opAddr]
            else:
                return self.ER_INVALIDADDR, None, None
            return self.OK, opAddr, opValue
            
        elif (mode == self.MODE_AUTOINC):   #Auto Increment Mode
            opAddr = self.gpr[reg]
            if (opAddr >= 0) and (opAddr <= 9999):
                opValue = self.ram[opAddr]
            else:
                return self.ER_INVALIDADDR, None, None
            self.gpr[reg] += 1
            return self.OK, opAddr, opValue
            
        elif (mode == self.MODE_AUTODEC):   #Auto Decrement Mode
            self.gpr[reg] -= 1
            opAddr = self.gpr[reg]
            if (opAddr >= 0) and (opAddr <= 9999):
                opValue = self.ram[opAddr]
            else:
                return self.ER_INVALIDADDR, None, None
            return self.OK, opAddr, opValue
            
        elif (mode == self.MODE_IMMEDIATE): #Immediate Mode
            opAddr = self.pc
            self.pc += 1
            if (opAddr >= 0) and (opAddr <= 9999):
                opValue = self.ram[opAddr]
            else:
                return self.ER_INVALIDADDR, None, None
            return self.OK, opAddr, opValue
            
        else:
            return self.ER_INVALIDMODE, None, None
    