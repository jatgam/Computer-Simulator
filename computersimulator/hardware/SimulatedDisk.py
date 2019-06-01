import pickle


class SimulatedDisk:

    def __init__(self, path, sectorSize=128, numSectors=1000):
        self.sectorSize = sectorSize # in "bytes"
        self.numSectors = numSectors # Size of disk
        self.diskpath = path
        self.disk = self._loadDisk(path)
        self.cache = False

    def _loadDisk(self, path):
        try:
            dskfile = open(path, 'r+b')
        except:
            return -1
        try:
            disk = pickle.load(dskfile)
            dskfile.close()
            return disk
        except EOFError:
            disk = self._initializeDisk(dskfile)
            dskfile.close()
            return disk

    def _initializeDisk(self, dskfile):
        #fs = [[0]*self.sectorSize]*self.numSectors
        fs = []
        sector = [0]*self.sectorSize
        for i in range(0, self.numSectors):
            fs.append(list(sector))
        pickle.dump(fs, dskfile)
        return fs

    def writeCache(self):
        dskfile = open(self.diskpath, 'r+b')
        dskfile.truncate()
        pickle.dump(self.disk, dskfile)
