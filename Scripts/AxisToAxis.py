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

class AxisToAxis(Script):
    """Converts one axis to another, applying a multiplier.
    For example, from "E" to "A1.0 B0.5" will replace line "G1 X193.239 Y204.43 E0.530" with "G1 X193.239 Y204.43 A0.530 B0.265"
    """

    def getSettingDataString(self):
        return """{
            "name": "Axis to Axis",
            "key": "AxisToAxis",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "FROM":
                {
                    "label": "From",
                    "description": "Axis to convert from.",
                    "type": "str",
                    "default_value": "E"
                },
                "TO":
                {
                    "label": "To",
                    "description": "Axis to convert to (A) and multiplier (n) in the form An. Separate multiple axes with a space.",
                    "type": "str",
                    "default_value": "A1.0 B0.5"
                },
                "EXCLUDE_INCLUDE":
                {
                    "label": "Exclude or Include Codes",
                    "description": "Select Include to only change lines with code mentioned or Exclude to change all lines except ones with code mentioned",
                    "type": "enum",
                    "options": {"EXCLUDE":"Exclude","INCLUDE":"Include"},
                    "default_value": "EXCLUDE"
                },
                "EXCLUDE_CODE":
                {
                    "label": "Exclude",
                    "description": "Codes to exclude (e.g. M201 M203)",
                    "type": "str",
                    "default_value": "M201 M203",
                    "enabled": "EXCLUDE_INCLUDE == 'EXCLUDE'"
                },
                "INCLUDE_CODE":
                {
                    "label": "Include",
                    "description": "Codes to include (e.g. G0 G1)",
                    "type": "str",
                    "default_value": "G0 G1",
                    "enabled": "EXCLUDE_INCLUDE == 'INCLUDE'"
                }
            }
        }"""

    def execute(self, data):
        EXCLUDE = str(self.getSettingValueByKey("EXCLUDE_INCLUDE")) == "EXCLUDE"
        if EXCLUDE:
            CODES = str(self.getSettingValueByKey("EXCLUDE_CODE")).split()
        else:
            CODES = str(self.getSettingValueByKey("INCLUDE_CODE")).split()

        FROM = str(self.getSettingValueByKey("FROM"))
        TO = str(self.getSettingValueByKey("TO")).split()

        Axes = []
        Mults = []
        for s in TO:
            Axes.append(s[0])
            Mults.append(float(s[1:]))
        count = len(Axes)

        for layer_number, layer in enumerate(data):
            lines = layer.splitlines(keepends=True)
            for i in range(len(lines)):
                code_split = lines[i].split()
                if len(code_split) == 0:
                    continue
                if EXCLUDE != (code_split[0] in CODES): # if code is not excluded or code is included
                    line_comment = lines[i].rstrip().split(";",1)
                    if len(line_comment) == 2:
                        comment = ";" + line_comment[1]
                    else:
                        comment = ""
                    
                    l = line_comment[0]
                    if FROM in l:
                        from_split = l.split(FROM,1)
                        before_from = from_split[0]
                        val_afterfrom = from_split[-1].split(None,1)
                        if len(val_afterfrom) == 0:
                            continue
                        elif len(val_afterfrom) == 1:
                            afterfrom = ""
                        else:
                            afterfrom = " " + val_afterfrom[1]
                        val = float(val_afterfrom[0])

                        new = ""
                        for j in range(count):
                            new += Axes[j] + "{:.3f} ".format(val * Mults[j])
                        new.rstrip()
    
                        lines[i] = before_from + new + afterfrom + comment + "\n"
            data[layer_number] = "".join(lines)

        PrintInfo = f"""
;GCode edited with AxisToAxis.py script - Copyright (c) 2022 Michael Joyce-Badea
;    Axis Conversion: change all {FROM} to {Axes} with multipliers {Mults} (respectively)
;    Exclude/Include: {"Exclude" if EXCLUDE else "Include"} all {CODES} codes, {"exclude" if not EXCLUDE else "include"} everything else

"""
        data[0] = PrintInfo + data[0]
        return data

if __name__ == "__main__":
    print("Running DEBUG program...")

    script = AxisToAxis()
    script.KeyValue = {
        "FROM": "E",
        "TO": "A1.0 B0.5",
        "EXCLUDE_INCLUDE": "INCLUDE",
        "EXCLUDE_CODE": "M201 M203",
        "INCLUDE_CODE": "G0 G1"
    }
    script.DEBUG()

    print("DEBUG program finished!")
