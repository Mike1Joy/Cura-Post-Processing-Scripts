# Copyright (c) 2022 Michael Joyce-Badea

# For use with Cura 4.x
# Place this script in C:\Program Files\Ultimaker Cura 4.x\plugins\PostProcessingPlugin\scripts

# For use with Cura 5.x
# Place this script in C:\Program Files\Ultimaker Cura 5.x\share\cura\plugins\PostProcessingPlugin\scripts

import math

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
                "EXRD_FORWARD_MAX":
                {
                    "label": "MaxSpeed variable",
                    "description": "Max speed of extrusion in mm/s when motors will spin with maximum RPM - when pins are set to max (mm/s). Used in extrude bit expressions.",
                    "type": "int",
                    "default_value": 75
                },
                "EXRD_FORWARD_b0":
                {
                    "label": "Extrude bit 0",
                    "description": "Expression to decide what to set pin 0 when extruding. Use EF for current E-axis speed and MaxSpeed for maximum speed. Written in Python to be evalucated with eval().",
                    "type": "str",
                    "default_value": "bool(int(round(min(max(0,(EF/MaxSpeed)*14),14)))&0b0001)"
                },
                "EXRD_FORWARD_b1":
                {
                    "label": "Extrude bit 1",
                    "description": "Expression to decide what to set pin 1 when extruding. Use EF for current E-axis speed and MaxSpeed for maximum speed. Written in Python to be evalucated with eval().",
                    "type": "str",
                    "default_value": "bool(int(round(min(max(0,(EF/MaxSpeed)*14),14)))&0b0010)"
                },
                "EXRD_FORWARD_b2":
                {
                    "label": "Extrude bit 2",
                    "description": "Expression to decide what to set pin 2 when extruding. Use EF for current E-axis speed and MaxSpeed for maximum speed. Written in Python to be evalucated with eval().",
                    "type": "str",
                    "default_value": "bool(int(round(min(max(0,(EF/MaxSpeed)*14),14)))&0b0100)"
                },
                "EXRD_FORWARD_b3":
                {
                    "label": "Extrude bit 3",
                    "description": "Expression to decide what to set pin 3 when extruding. Use EF for current E-axis speed and MaxSpeed for maximum speed. Written in Python to be evalucated with eval().",
                    "type": "str",
                    "default_value": "bool(int(round(min(max(0,(EF/MaxSpeed)*14),14)))&0b1000)"
                },
                "DWELL":
                {
                    "label": "Add Dwells",
                    "description": "Add a dwell when extruding but gantry is not moving. Eg 'G1 E1.0'",
                    "type": "bool",
                    "default_value": true
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
                    "default_value": "M63 P0 M63 P1 M63 P2 M63 P3; Stop Extruder Header"
                },
                "FOOTER":
                {
                    "label": "Footer GCode",
                    "description": "Footer to add at end of file.",
                    "type": "str",
                    "default_value": "M63 P0 M63 P1 M63 P2 M63 P3; Stop Extruder Footer"
                }
            }
        }"""
    
    def execute(self, data):
        # Get values
        EXRD_FORWARD_MAX = self.getSettingValueByKey("EXRD_FORWARD_MAX")
        MaxSpeed = int(EXRD_FORWARD_MAX)
        EXRD_FORWARD_b0 = self.getSettingValueByKey("EXRD_FORWARD_b0")
        EXRD_FORWARD_b1 = self.getSettingValueByKey("EXRD_FORWARD_b1")
        EXRD_FORWARD_b2 = self.getSettingValueByKey("EXRD_FORWARD_b2")
        EXRD_FORWARD_b3 = self.getSettingValueByKey("EXRD_FORWARD_b3")

        b0 = 0
        b1 = 0
        b2 = 0
        b3 = 0

        last_b0 = 0
        last_b1 = 0
        last_b2 = 0
        last_b3 = 0

        DWELL = self.getSettingValueByKey("DWELL")

        CODES = self.getSettingValueByKey("CODES").split()
        HEADER = self.getSettingValueByKey("HEADER")
        FOOTER = self.getSettingValueByKey("FOOTER")

        E_Absolute = False
        E_Last = 0.0
        X_Last = 0.0
        Y_Last = 0.0
        Z_Last = 0.0

        this_last_E = 0.0
        this_last_X = 0.0
        this_last_Y = 0.0
        this_last_Z = 0.0

        G0_F = 0
        G1_F = 0

        FEED = False

        # Go through GCode
        for layer_number, layer in enumerate(data):
            lines = layer.splitlines(keepends=True)
            for line in range(len(lines)):
                if "G92" in lines[line]:
                    if "E" in lines[line]:
                        E_Last = 0
                    if "X" in lines[line]:
                        X_Last = 0
                    if "Y" in lines[line]:
                        Y_Last = 0
                    if "Z" in lines[line]:
                        Z_Last = 0
                    continue

                E_value = 0
                X_value = 0
                Y_value = 0
                Z_value = 0
                Dwell_time = 0
                Gant_dist = 0
                EF = 0

                line_comment =  lines[line].split(";",maxsplit=1)
                lines[line] = line_comment[0]
                comment = ""
                if len(line_comment) > 1:
                    comment = ";"+line_comment[1]

                if "M82" in lines[line]:
                    E_Absolute = True
                elif "M83" in lines[line]:
                    E_Absolute = False
                
                if any(G in lines[line] for G in CODES):
                    FEED = "G1" in lines[line]

                    if "F" in lines[line]:
                        if FEED:
                            G1_F = float(lines[line].split("F",maxsplit=1)[-1].split(maxsplit=1)[0])/60.0
                        else:
                            G0_F = float(lines[line].split("F",maxsplit=1)[-1].split(maxsplit=1)[0])/60.0
                        

                    if "E" in lines[line]:
                        UpToE = lines[line].split("E",maxsplit=1)
                        EOnwards = UpToE[-1].split(maxsplit=1)
                        E_value = float(EOnwards[0])

                        this_last_E = E_value

                        if E_Absolute:
                            E_value -= E_Last
                    
                    if "X" in lines[line]:
                        this_last_X = float(lines[line].split("X",maxsplit=1)[-1].split(maxsplit=1)[0])
                        X_value = this_last_X - X_Last
                    else:
                        X_value = 0.0
                    
                    if "Y" in lines[line]:
                        this_last_Y = float(lines[line].split("Y",maxsplit=1)[-1].split(maxsplit=1)[0])
                        Y_value = this_last_Y - Y_Last
                    else:
                        Y_value = 0.0
                    
                    if "Z" in lines[line]:
                        this_last_Z = float(lines[line].split("Z",maxsplit=1)[-1].split(maxsplit=1)[0])
                        Z_value = this_last_Z - Z_Last
                    else:
                        Z_value = 0.0

                    if E_value < 0:
                        b0 = 1
                        b1 = 1
                        b2 = 1
                        b3 = 1
                        Dwell_time = -E_value / MaxSpeed
                    elif E_value == 0:
                        b0 = 0
                        b1 = 0
                        b2 = 0
                        b3 = 0
                        Dwell_time = 0
                    else:
                        Gant_dist = math.sqrt(X_value**2 + Y_value**2 + Z_value**2)

                        if Gant_dist > 0:
                            if FEED:
                                T = Gant_dist / G1_F
                            else:
                                T = Gant_dist / G0_F
                            EF = E_value/T
                        else:
                            EF = MaxSpeed
                            Dwell_time = E_value / MaxSpeed
                    
                        b0 = eval(EXRD_FORWARD_b0)
                        b1 = eval(EXRD_FORWARD_b1)
                        b2 = eval(EXRD_FORWARD_b2)
                        b3 = eval(EXRD_FORWARD_b3)

                    pin_string = ""
                    if b0 != last_b0:
                        if b0: pin_string += "M62 P0 "
                        else:  pin_string += "M63 P0 "
                    if b1 != last_b1:
                        if b1: pin_string += "M62 P1 "
                        else:  pin_string += "M63 P1 "
                    if b2 != last_b2:
                        if b2: pin_string += "M62 P2 "
                        else:  pin_string += "M63 P2 "
                    if b3 != last_b3:
                        if b3: pin_string += "M62 P3 "
                        else:  pin_string += "M63 P3 "
                    
                    #pin_string += f"; b0: {b0}, b1: {b1}, b2: {b2}, b3: {b3}, EF: {EF}, Dwell_time: {Dwell_time:.4f}, Gant_dist: {Gant_dist:.4f}, E_value: {E_value}, G1_F: {G1_F}, G0_F: {G0_F}, X_value: {X_value}, Y_value: {Y_value}, Z_value: {Z_value}"

                    if len(pin_string) > 0:
                        lines[line] = pin_string + f" ;0b{int(b3)}{int(b2)}{int(b1)}{int(b0)} = {EF}mm/s out of max {MaxSpeed}mm/s\n" + lines[line]
                    if Dwell_time > 0 and DWELL:
                        lines[line] = lines[line] + f"G4 P{Dwell_time:.4f} ;Robot Dwell - extrude {E_value}mm at {MaxSpeed}mm/s\n"
                

                E_Last = this_last_E
                X_Last = this_last_X
                Y_Last = this_last_Y
                Z_Last = this_last_Z

                last_b0 = b0
                last_b1 = b1
                last_b2 = b2
                last_b3 = b3

                if comment:
                    lines[line] += comment

            data[layer_number] = "".join(lines)

        # Header and footer
        data[0] = HEADER + "\n" + data[0]
        data[-1] += FOOTER + "\n"

        return data

if __name__ == "__main__":
    print("Running DEBUG program...")

    script = ExternalExtruder()
    script.KeyValue = {
        "EXRD_FORWARD_MAX": 75,
        "EXRD_FORWARD_b0": "bool(int(round(min(max(0,(EF/MaxSpeed)*14),14)))&0b0001)",
        "EXRD_FORWARD_b1": "bool(int(round(min(max(0,(EF/MaxSpeed)*14),14)))&0b0010)",
        "EXRD_FORWARD_b2": "bool(int(round(min(max(0,(EF/MaxSpeed)*14),14)))&0b0100)",
        "EXRD_FORWARD_b3": "bool(int(round(min(max(0,(EF/MaxSpeed)*14),14)))&0b1000)",
        "DWELL": True,
        "CODES": "G0 G1 G2 G3 G4 G28",
        "HEADER": "M63 P0 M63 P1 M63 P2 M63 P3; Stop Extruder Header",
        "FOOTER": "M63 P0 M63 P1 M63 P2 M63 P3; Stop Extruder Footer"
    }
    script.DEBUG()

    print("DEBUG program finished!")


