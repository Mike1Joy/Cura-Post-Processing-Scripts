# Cura-Post-Processing-Scripts

Post processing scripts for Cura 4.x and 5.x. When active, these Python scripts edit the GCode produced by Cura.


## Installation

### Cura 4.x (Windows)

Place scripts in C:\Program Files\Ultimaker Cura 4.x\plugins\PostProcessingPlugin\scripts

### Cura 5.x (Windows)

Place scripts in C:\Program Files\Ultimaker Cura 5.x\share\cura\plugins\PostProcessingPlugin\scripts


## Use

- In Cura, go to Extensions > Post Processing > Modify G-Code
- Add the script you want to use and fill in the options


## Available Scripts

### Axis To Axis

This script converts one axis to another, applying an optional multiplier. One axis can be converted into a number of others.

For example from "E" to "A1.0 B0.5" will replace this example line "G1 X193.239 Y204.43 E0.530" with "G1 X193.239 Y204.43 A0.530 B0.265

### External Extruder

This script adds lines to GCode for controlling an external extruder (for example with digital pins). Originally developed for 3D printing with Universal Robots (UR5e and UR10e) in Toolpath mode. However, this script is made to be general purpose. Decide what GCode to insert when extruding, retracting and stop extruding.


## Other Resources

- Data.py contains an example list object containting layers of G-Code similar to what would be passed by Cura. This is for debug purposes.
- Debug.py contains a Script class to mimic the Cura Script class for debug purposes. This means you don't have to open Cura to test a script. To run the debug version of each of the scripts, simply place Data.py and Debug.py in the same folder as the script then running the script. See existing scripts in this repository for how to write a script in a way that works for Debug.
