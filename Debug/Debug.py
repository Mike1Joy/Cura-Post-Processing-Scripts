from Data import gcode

class Script:
    def __init__(self):
        self.gcode = gcode
        self.filePath = r"C:\Users\ms-joyce\OneDrive - UWE Bristol\Projects\22-10 Cura Scripts\PostProcessingPlugin\scripts\Debug.gcode"
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
