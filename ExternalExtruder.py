# Copyright (c) 2022 Michael Joyce-Badea

# For use with Cura 4.x
# Place this script in C:\Program Files\Ultimaker Cura 4.x\plugins\PostProcessingPlugin\scripts

# For use with Cura 5.x
# Place this script in C:\Program Files\Ultimaker Cura 5.x\share\cura\plugins\PostProcessingPlugin\scripts

if __name__ == "__main__":
    from Debug import Script
    print("Debug mode")
else:
    from ..Script import Script

class ExternalExtruder(Script):
    """Adds lines to GCode for controlling external extruder (for example with digital pins).
    Developed for Universal Robots in Toolpath mode, but can be general purpose.
    """

    def getSettingDataString(self):
        return """{
            "name": "External Extruder",
            "key": "ExternalExtruder",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "EXRD_":
                {
                    "label": "Extruder Change",
                    "description": "Add GCode whenever the extruder state changes (forward, backwards or stopped).",
                    "type": "bool",
                    "default_value": true
                },
                "EXRD_FORWARD":
                {
                    "label": "Extrude GCode",
                    "description": "GCode to insert when extruding forward.",
                    "type": "str",
                    "default_value": "M62 P1 M62 P0; Start Extruder",
                    "enabled": "EXRD_"
                },
                "EXRD_STOPPED":
                {
                    "label": "Stop Extrude GCode",
                    "description": "GCode to insert when extruding has stopped.",
                    "type": "str",
                    "default_value": "M63 P0; Stop Extruder",
                    "enabled": "EXRD_"
                },
                "EXRD_BACKWARDS":
                {
                    "label": "Retract GCode",
                    "description": "GCode to insert when extruding backwards.",
                    "type": "str",
                    "default_value": "M63 P1 M62 P0; Start Retracting",
                    "enabled": "EXRD_"
                },
                "GANT_":
                {
                    "label": "Gantry Move",
                    "description": "Add GCode whenever the gantry state changes (moves or stops).",
                    "type": "bool",
                    "default_value": true
                },
                "GANT_MOVING":
                {
                    "label": "Gantry Moving GCode",
                    "description": "GCode to insert when gantry is moving.",
                    "type": "str",
                    "default_value": "M62 P2; Gantry Moving",
                    "enabled": "GANT_"
                },
                "GANT_STOPPED":
                {
                    "label": "Gantry Stopped GCode",
                    "description": "GCode to insert when gantry is stopped.",
                    "type": "str",
                    "default_value": "M63 P2; Gantry Stopped",
                    "enabled": "GANT_"
                },
                "AXES":
                {
                    "label": "Movement Axes",
                    "description": "All axes to be treated as the gantry moving (separate with spaces).",
                    "type": "str",
                    "default_value": "X Y Z A B C",
                    "enabled": "GANT_"
                },
                "DWELL":
                {
                    "label": "Add Dwells",
                    "description": "Add a dwell when extruding but gantry is not moving. Eg 'G1 E1.0'",
                    "type": "bool",
                    "default_value": false
                },
                "DWELL_EXTR_SPEED":
                {
                    "label": "Stationary Feed Rate",
                    "description": "Feed rate (mm/s) for extruder when gantry is stopped. This will determine the time the printer will dwell when extruding and not moving.",
                    "unit": "mm/s",
                    "type": "float",
                    "minimum_value": "0",
                    "default_value": 15.0,
                    "enabled": "DWELL"
                },
                "REMOVE_E":
                {
                    "label": "Remove E",
                    "description": "Remove the E axis from GCode after processing.",
                    "type": "bool",
                    "default_value": false
                },
                "GCODE_FREQ":
                {
                    "label": "Insertion Frequency",
                    "description": "Insert lines of GCode on every line or only when something changes.",
                    "type": "enum",
                    "options": {"EVERYLINE":"Every Line", "ONCHANGE":"On Change"},
                    "default_value": "ONCHANGE"
                },
                "CODES":
                {
                    "label": "Include Codes",
                    "description": "Codes to include. All other codes will be ignored (separate with spaces).",
                    "type": "str",
                    "default_value": "G0 G1 G2 G3 G28"
                },
                "HEADER":
                {
                    "label": "Header GCode",
                    "description": "Header to add at top of file.",
                    "type": "str",
                    "default_value": "M63 P0 M63 P1 M63 P2 ;Turn all pins off"
                },
                "FOOTER":
                {
                    "label": "Footer GCode",
                    "description": "Footer to add at end of file.",
                    "type": "str",
                    "default_value": "M63 P0 M63 P1 M63 P2 ;Turn all pins off"
                }
            }
        }"""

    def execute(self, data):
        # Get values
        EXRD_ = self.getSettingValueByKey("EXRD_")
        EXRD_FORWARD = self.getSettingValueByKey("EXRD_FORWARD")
        EXRD_STOPPED = self.getSettingValueByKey("EXRD_STOPPED")
        EXRD_BACKWARDS = self.getSettingValueByKey("EXRD_BACKWARDS")
        EXRD = [EXRD_FORWARD+"\n",EXRD_STOPPED+"\n",EXRD_BACKWARDS+"\n"]
        E_FRWD = 0
        E_STOP = 1
        E_BKWD = 2
        E_STATE = E_STOP

        GANT_ = self.getSettingValueByKey("GANT_")
        GANT_MOVING = self.getSettingValueByKey("GANT_MOVING")
        GANT_STOPPED = self.getSettingValueByKey("GANT_STOPPED")
        GANT = [GANT_MOVING+"\n",GANT_STOPPED+"\n"]
        G_MOVE = 0
        G_STOP = 1
        G_STATE = G_STOP

        DWELL = self.getSettingValueByKey("DWELL")
        DWELL_EXTR_SPEED = self.getSettingValueByKey("DWELL_EXTR_SPEED")

        REMOVE_E = self.getSettingValueByKey("REMOVE_E")

        EVERYLINE = (self.getSettingValueByKey("GCODE_FREQ") == "EVERYLINE")

        CODES = self.getSettingValueByKey("CODES").split()
        AXES = self.getSettingValueByKey("AXES").split()

        HEADER = self.getSettingValueByKey("HEADER")
        FOOTER = self.getSettingValueByKey("FOOTER")

        # Go through GCode
        for layer_number, layer in enumerate(data):
            lines = layer.splitlines(keepends=True)
            for line in range(len(lines)):
                this_E_STATE = E_STATE
                this_G_STATE = G_STATE

                E_value = 0
                Dwell_time = 0

                line_comment =  lines[line].split(";",maxsplit=1)
                lines[line] = line_comment[0]
                comment = ""
                if len(line_comment) > 1:
                    comment = ";"+line_comment[1]

                if any(G in lines[line] for G in CODES):
                    if "E" in lines[line]:
                        UpToE = lines[line].split("E",maxsplit=1)
                        EOnwards = UpToE[-1].split(maxsplit=1)
                        E_value = float(EOnwards[0])

                        if REMOVE_E:
                            lines[line] = UpToE[0] + ("\n" if len(EOnwards) == 1 else EOnwards[1])

                    if E_value == 0:
                        this_E_STATE = E_STOP
                    elif E_value < 0:
                        this_E_STATE = E_BKWD
                    else:
                        this_E_STATE = E_FRWD
                        
                    if any(move in lines[line] for move in AXES):
                        this_G_STATE = G_MOVE
                    else:
                        this_G_STATE = G_STOP
                        Dwell_time = abs(E_value)/DWELL_EXTR_SPEED
                    
                    # add lines to gcode in reverse order
                    if DWELL and this_E_STATE != E_STOP and this_G_STATE == G_STOP and Dwell_time > 0:
                        lines[line] = f"G4 P{Dwell_time:.4f} ;Robot Dwell\n" + lines[line]
                    
                    if (EVERYLINE or this_E_STATE != E_STATE) and EXRD_:
                        E_STATE = this_E_STATE
                        lines[line] = EXRD[E_STATE] + lines[line]
                    
                    if (EVERYLINE or this_G_STATE != G_STATE) and GANT_:
                        G_STATE = this_G_STATE
                        lines[line] = GANT[G_STATE] + lines[line]
            
                if comment:
                    lines[line] += comment

            data[layer_number] = "".join(lines)

        # Header and footer
        data[0] = HEADER + "\n" + data[0]
        data[-1] += FOOTER + "\n"

        PrintInfo = f"""
;GCode edited with ExternalExtruder.py script - Copyright (c) 2022 Michael Joyce-Badea
;   EXRD_FORWARD: {EXRD_FORWARD},
;   EXRD_STOPPED: {EXRD_STOPPED},
;   EXRD_BACKWARDS: {EXRD_BACKWARDS},
;   GANT_MOVING: {GANT_MOVING},
;   GANT_STOPPED: {GANT_STOPPED},
;   DWELL: {DWELL},
;   DWELL_EXTR_SPEED: {DWELL_EXTR_SPEED},
;   REMOVE_E: {REMOVE_E},
;   GCODE_FREQ: {"EVERYLINE" if EVERYLINE else "ONCHANGE"},
;   CODES: {CODES},
;   AXES: {AXES},
;   HEADER: {HEADER},
;   FOOTER: {FOOTER}

"""
        data[0] = PrintInfo + data[0]
        return data

if __name__ == "__main__":
    print("Running DEBUG program...")

    script = ExternalExtruder()
    script.KeyValue = {
        "EXRD_FORWARD": "M62 P0 M62 P1; EXRD_FORWARD",
        "EXRD_STOPPED": "M63 P0; EXRD_STOPPED",
        "EXRD_BACKWARDS": "M62 P0 M63 P1; EXRD_BACKWARDS",
        "GANT_MOVING": "M62 P2; GANT_MOVING",
        "GANT_STOPPED": "M63 P2; GANT_STOPPED",
        "DWELL": True,
        "DWELL_EXTR_SPEED": 15.0,
        "REMOVE_E": False,
        "GCODE_FREQ": "ONCHANGE",
        "CODES": "G0 G1 G2 G3 G4 G28",
        "AXES": "X Y Z A B C",
        "HEADER": "M63 P0 M63 P1 M63 P2 ;Turn all pins off",
        "FOOTER": "M63 P0 M63 P1 M63 P2 ;Turn all pins off"
    }
    script.DEBUG()

    print("DEBUG program finished!")


