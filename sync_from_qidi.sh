#!/bin/bash
rsync -avz mks@qidi:~/printer_data/ printer_data/ --exclude backup --exclude gcodes/ --exclude logs/ --exclude "*.log" --exclude timelapse/ --exclude ".cache" --exclude ".temp" --exclude ".git" --exclude "comms/" --exclude "database/"  --exclude "*.bkp"
# rsync -avz mks@qidi:~/klipper/klippy/extras/ klippy_extras/ --exclude "__pycache__/"

# rsync -avz mks@qidi:~/fluidd-config/ fluidd-config/ --exclude ".git"
# rsync -avz mks@qidi:~/Klipper-Adaptive-Meshing-Purging/ Klipper-Adaptive-Meshing-Purging/  --exclude ".git"
# rsync -avz mks@qidi:~/moonraker-timelapse/ moonraker-timelapse/ --exclude ".git"