import logging
import sys
from computersimulator.hardware.SimulatedRAM import SimulatedRAM
from computersimulator.hardware.SimulatedDisk import SimulatedDisk
from computersimulator.utils.bitutils import *
import computersimulator.constants as constants

CONST = constants.Constants
logger = logging.getLogger(__name__)
class SimulatedCPU:

    def __init__(self):
        logger.info("Initializing CPU")
        ### CPU Hardware Variables ###
        self.gpr = [0]*8  # General Purpose Registers
        self.sp = None  # Stack Pointer
        self.pc = None  # Program Counter
        self.ir = None  # Instruction Register
        self.psr = None  # Processor Status Register
        self.clock = None  # Clock
        ### Other Hardware Accessed by CPU ###
        self.sram = SimulatedRAM()
        self.sdisk = SimulatedDisk("computersimulator/hardware/disks/disk.dsk")
        if (self.sdisk.disk == -1):
            print("Fatal Error! Disk not found!")
            sys.exit()

    def executeProgram(self, systemCallCallback, timeslice=200):
        """
        Runs through the ram and grabs the next IR and decodes it. Then
        performs the correct operation.
        """
        status = 0
        clock_start = self.clock
        while (status >= 0):
            if (self.pc < 0) or (self.pc > 9999): # Check to see if PC valid
                return CONST.ER_PC
            if (self.clock - clock_start >= timeslice):
                return CONST.TIMESLICE
            self.ir = self.sram.ram[self.pc]
            self.pc += 1
            # Decode IR
            op_code = self.ir >> 16
            op1_mode = extractBits(self.ir, 4, 13)
            op1_reg = extractBits(self.ir, 4, 9)
            op2_mode = extractBits(self.ir, 4, 5)
            op2_reg = extractBits(self.ir, 4, 1)

            logger.debug("IR:%s op_code:%s op1_mode:%s op1_reg:%s op1_mode:%s op1_reg:%s",
                            hex(self.ir), hex(op_code), hex(op1_mode), hex(op1_reg), hex(op2_mode), hex(op2_reg))

            if (op_code == CONST.OP_HALT):  # Halt Opcode
                self.clock += 12
                return CONST.OK
            elif (op_code == CONST.OP_ADD):  # Add Opcode
                status, op1_addr, op1_value = self._fetchOperand(op1_mode, op1_reg)
                if (status != 0):
                    return CONST.ER_INVALIDMODE
                status, op2_addr, op2_value = self._fetchOperand(op2_mode, op2_reg)
                if (status != 0):
                    return CONST.ER_INVALIDMODE
                result = op1_value + op2_value  # ALU
                if (op2_mode == CONST.MODE_REGISTER):
                    self.gpr[op2_reg] = result
                else:
                    self.sram.ram[op2_addr] = result
                self.clock += 3
                continue
            elif (op_code == CONST.OP_SUB):  # Subtract Opcode
                status, op1_addr, op1_value = self._fetchOperand(op1_mode, op1_reg)
                if (status != 0):
                    return CONST.ER_INVALIDMODE
                status, op2_addr, op2_value = self._fetchOperand(op2_mode, op2_reg)
                if (status != 0):
                    return CONST.ER_INVALIDMODE
                result = op2_value - op1_value  # ALU
                if (op2_mode == CONST.MODE_REGISTER):
                    self.gpr[op2_reg] = result
                else:
                    self.sram.ram[op2_addr] = result
                self.clock += 3
                continue
            elif (op_code == CONST.OP_MULT):  # Multiply Opcode
                status, op1_addr, op1_value = self._fetchOperand(op1_mode, op1_reg)
                if (status != 0):
                    return CONST.ER_INVALIDMODE
                status, op2_addr, op2_value = self._fetchOperand(op2_mode, op2_reg)
                if (status != 0):
                    return CONST.ER_INVALIDMODE
                result = op1_value * op2_value  # ALU
                if (op2_mode == CONST.MODE_REGISTER):
                    self.gpr[op2_reg] = result
                else:
                    self.sram.ram[op2_addr] = result
                self.clock += 6
                continue
            elif (op_code == CONST.OP_DIV):  # Divide Opcode
                status, op1_addr, op1_value = self._fetchOperand(op1_mode, op1_reg)
                if (status != 0):
                    return CONST.ER_INVALIDMODE
                status, op2_addr, op2_value = self._fetchOperand(op2_mode, op2_reg)
                if (status != 0):
                    return CONST.ER_INVALIDMODE
                result = op2_value / op1_value  # ALU
                if (op2_mode == CONST.MODE_REGISTER):
                    self.gpr[op2_reg] = result
                else:
                    self.sram.ram[op2_addr] = result
                self.clock += 6
                continue
            elif (op_code == CONST.OP_MOVE):  # Move Opcode
                status, op1_addr, op1_value = self._fetchOperand(op1_mode, op1_reg)
                if (status != 0):
                    return CONST.ER_INVALIDMODE
                status, op2_addr, op2_value = self._fetchOperand(op2_mode, op2_reg)
                if (status != 0):
                    return CONST.ER_INVALIDMODE
                result = op1_value
                if (op2_mode == CONST.MODE_REGISTER):
                    self.gpr[op2_reg] = result
                else:
                    self.sram.ram[op2_addr] = result
                self.clock += 2
                continue
            elif (op_code == CONST.OP_BRANCH):  # Branch Opcode
                if (self.pc >= 0) and (self.pc <=9999):
                    self.pc = self.sram.ram[self.pc]
                    self.clock += 2
                else:
                    return CONST.ER_INVALIDADDR
                continue
            elif (op_code == CONST.OP_BRANCHM):  # Branch on Minus Opcode
                status, op1_addr, op1_value = self._fetchOperand(op1_mode, op1_reg)
                if (status != 0):
                    return CONST.ER_INVALIDMODE
                if (op1_value < 0):
                    self.pc = self.sram.ram[self.pc]
                else:
                    self.pc += 1
                self.clock += 4
                continue
            elif (op_code == CONST.OP_SYSTEM):  # System Call Opcode
                status, op1_addr, op1_value = self._fetchOperand(op1_mode, op1_reg)
                if (status != 0):
                    return CONST.ER_INVALIDMODE
                status = systemCallCallback(op1_value)
                self.clock += 12
                if (status == CONST.WAITING):
                    return CONST.WAITING
                if (status == CONST.HALT):
                    return 0
                continue
            elif (op_code == CONST.OP_BRANCHP):  # Branch on Plus Opcode
                status, op1_addr, op1_value = self._fetchOperand(op1_mode, op1_reg)
                if (status != 0):
                    return CONST.ER_INVALIDMODE
                if (op1_value > 0):
                    self.pc = self.sram.ram[self.pc]
                else:
                    self.pc += 1
                self.clock += 4
                continue
            elif (op_code == CONST.OP_BRANCHZ):  # Branch on Zero Opcode
                status, op1_addr, op1_value = self._fetchOperand(op1_mode, op1_reg)
                if (status != 0):
                    return CONST.ER_INVALIDMODE
                if (op1_value == 0):
                    self.pc = self.sram.ram[self.pc]
                else:
                    self.pc += 1
                self.clock += 4
                continue
            elif (op_code == CONST.OP_PUSH):  # Push Opcode
                return CONST.ER_OPNOTIMP
            elif (op_code == CONST.OP_POP):  # Pop Opcode
                return CONST.ER_OPNOTIMP
            else:
                logger.warn("Invalid Op Code")
                return CONST.ER_INVALIDOP
        return CONST.OK


    def _fetchOperand(self, mode, reg):
        """
        Takes input of a mode and register and returns the values of the
        operands and a status.

        Returns: status, opAddr, opValue
        """
        if (mode == CONST.MODE_DIRECT):  # Direct Mode
            if (self.pc >= 0) and (self.pc <= 9999):
                opAddr = self.sram.ram[self.pc]  # get opAddr using PC
                self.pc += 1
                if (opAddr >= 0) and (opAddr <= 9999):
                    opValue = self.sram.ram[opAddr]  # get opValue
                else:
                    return CONST.ER_INVALIDADDR, None, None
            else:
                return CONST.ER_INVALIDADDR, None, None
            return CONST.OK, opAddr, opValue

        elif (mode == CONST.MODE_REGISTER):  # Register Mode
            opAddr = -1  # Not in Memory
            opValue = self.gpr[reg]
            return CONST.OK, opAddr, opValue

        elif (mode == CONST.MODE_REGDEFERRED):  # Register Deferred Mode
            opAddr = self.gpr[reg]
            if (opAddr >= 0) and (opAddr <= 9999):
                opValue = self.sram.ram[opAddr]
            else:
                return CONST.ER_INVALIDADDR, None, None
            return CONST.OK, opAddr, opValue

        elif (mode == CONST.MODE_AUTOINC):  # Auto Increment Mode
            opAddr = self.gpr[reg]
            if (opAddr >= 0) and (opAddr <= 9999):
                opValue = self.sram.ram[opAddr]
            else:
                return CONST.ER_INVALIDADDR, None, None
            self.gpr[reg] += 1
            return CONST.OK, opAddr, opValue

        elif (mode == CONST.MODE_AUTODEC):  # Auto Decrement Mode
            self.gpr[reg] -= 1
            opAddr = self.gpr[reg]
            if (opAddr >= 0) and (opAddr <= 9999):
                opValue = self.sram.ram[opAddr]
            else:
                return CONST.ER_INVALIDADDR, None, None
            return CONST.OK, opAddr, opValue

        elif (mode == CONST.MODE_IMMEDIATE):  # Immediate Mode
            opAddr = self.pc
            self.pc += 1
            if (opAddr >= 0) and (opAddr <= 9999):
                opValue = self.sram.ram[opAddr]
            else:
                return CONST.ER_INVALIDADDR, None, None
            return CONST.OK, opAddr, opValue

        else:
            return CONST.ER_INVALIDMODE, None, None
