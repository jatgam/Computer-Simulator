class SimulatedRAM:

    def __init__(self, ramSize=10000):
        self.ramSize = ramSize
        ### Hardware Variables ###
        self.ram = [0]*self.ramSize  # Machine Memory
