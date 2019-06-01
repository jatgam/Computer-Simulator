def const(cls):
    is_special = lambda name: (name.startswith("__") and name.endswith("__"))
    class_contents = {n: getattr(cls, n) for n in vars(cls) if not is_special(n)}
    def unbind(value):
        return lambda self: value
    propertified_contents = {name: property(unbind(value))
                             for (name, value) in class_contents.items()}
    receptor = type(cls.__name__, (object,), propertified_contents)
    return receptor()

@const
class Constants(object):
    ### Opcodes ###
    OP_HALT = 0x0  # Opcode: Halt
    OP_ADD = 0x1  # Opcode: Add
    OP_SUB = 0x2  # Opcode: Subtract
    OP_MULT = 0x3  # Opcode: Multiply
    OP_DIV = 0x4  # Opcode: Divide
    OP_MOVE = 0x5  # Opcode: Move
    OP_BRANCH = 0x6  # Opcode: Branch
    OP_BRANCHM = 0x7  # Opcode: Branch on Minus
    OP_SYSTEM = 0x8  # Opcode: System Call
    OP_BRANCHP = 0x9  # Opcode: Branch on Plus
    OP_BRANCHZ = 0xa  # Opcode: Branch on Zero
    OP_PUSH = 0xb  # Opcode: Push
    OP_POP = 0xc  # Opcode: Pop

    MODE_DIRECT = 0x0  # Mode: Direct
    MODE_REGISTER = 0x1  # Mode: Register
    MODE_REGDEFERRED = 0x2  # Mode: Register Deffered
    MODE_AUTOINC = 0x3  # Mode: Auto Increment
    MODE_AUTODEC = 0x4  # Mode: Auto Decrement
    MODE_IMMEDIATE = 0x5  # Mode: Immediate

    ENDPROG = -1  # End of Program

    ### Return Codes ###
    OK = 0  # Successful execution
    ER_TID = -1  # Error: Task ID
    ER_PCB = -2  # Error: No PCBs available
    ER_MEM = -3  # Error: No memory available
    ER_NMB = -4  # Error: Not a memory Block
    ER_ISC = -5  # Error: Invalid System Call
    ER_TMO = -6  # Error: Time Out
    ER_NMP = -7  # Error: No message present
    ER_QID = -8  # Error: Queue ID
    ER_QFL = -9  # Error: Queue full
    ER_FILEOPEN = -10  # Error: File Not Found
    ER_INVALIDADDR = -11  # Error: Invalid Memory Address
    ER_NOENDOFPROG = -12  # Error: No end of program
    ER_INVALIDMODE = -13  # Error: Invalid Mode
    ER_OPNOTIMP = -14  # Error: Operand not Implemented
    ER_DIVBYZ = -15  # Error: Divide By Zero
    ER_INVALIDOP = -16  # Error: Invalid Opcode
    ER_INT = -17  # Error: Invalid Interrupts
    ER_PC = -18  # Error: Invalid PC

    ### System Calls ###
    TASK_CREATE = 0  # Create Task
    TASK_DELETE = 1  # Delete Task
    TASK_INQUIRY = 5  # Task Inquiry
    MEM_ALLOC = 8  # Allocate Memory
    MEM_FREE = 9  # Release Memory
    MSG_QSEND = 12  # Send message to queue
    MSG_QRECIEVE = 13  # Recieve message from queue
    IO_GETC = 14  # Get one character
    IO_PUTC = 15  # Display one character
    TIME_GET = 16  # Get the time
    TIME_SET = 17  # Set the time

    ### OS Values ###
    OSMODE = 1
    USERMODE = 0
    EOL = -1  # End of List
    DFLT_USR_PRTY = 127  # Default Priority
    USER_STACK_SIZE = 10  # Default User Stack Size
    PCBSIZE = 25  # Default PCB Size
    READY = 1  # Process Ready Status
    WAITING = 2  # Process Waiting Status
    EXECUTING = 0  # Process Executing Status
    TIMESLICE = 1  # Time Slice Expired
    WAITINGMSG = 2  # waiting for message
    WAITINGGET = 3  # waiting for input
    WAITINGPUT = 4  # waiting to output
    HALT = -20  # halt status

    ### Interrupts ###
    NO_INT = 0  # No interrupts
    INPUT_INT = 1  # Read one character
    OUTPUT_INT = 2  # Output one character
    RUN_INT = 3  # Run user program
    SHUTDOWN_INT = 4  # shutdown system

    ### Disk File System Values ###
    PARTITION_TYPE = 42  # Made up Partition Type ID
    FAT_SIZE = 20  # Size of FAT in sectors
    BTMP_FREE = 0  # Bitmap Sector Free
    BTMP_USED = 1  # Bitmap Sector Used
    BTMP_SYS = 2  # Bitmap Sector Used by System
    BTMP_INV = -1  # Bitmap Sector is out of Partition/Invalid
