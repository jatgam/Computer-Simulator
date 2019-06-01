Jatgam Computer Simulator
=========================

Simulates the CPU, Memory, ~~Disk~~, and OS of a computer allowing you to
create and run simple assembly programs.

### Requirements
* Python 3.7 (Didn't test any other versions)

### Usage
Checkout the repo and run `python ComputerSimulator.py`.
Every context switch of the CPU requires input, loading a program from disk or
sending interrupts.

Running `python ComputerSimulator.py --loglevel=debug` will print out a LOT of
information about cpu instructions into a file `computersimulator.log`. Without
this, troubleshooting the machine code programs is very difficult.

#### Programs
In the `programs` directory there are some sample programs the OS can run.
Load programs from `programs/machinecode` to use in the simulator. Assembly
versions and machine code with comments exist in the other directories.
