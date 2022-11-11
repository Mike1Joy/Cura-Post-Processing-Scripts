from Data import gcode

class Script:
    def __init__(self):
        self.gcode = gcode
        self.filePath = r"" # enter file path of where you want the debug gcode to save
        self.KeyValue = {}

    def getSettingValueByKey(self,s):
        return self.KeyValue[s]

    def execute(self, d):
        return d

    def DEBUG(self):
        f = open(self.filePath,"w")
        print("  Writing GCode to " + self.filePath)
        for layer in self.execute(self.gcode):
            f.write(layer)
        f.close()
