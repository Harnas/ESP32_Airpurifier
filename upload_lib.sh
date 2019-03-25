#!/bin/bash
# if downloading files from main.py doesnt work, download these files manually, save in proper directory (lib/uasyncio/) and run this script

files=(lib/)

echo "Uploading.."
for index in ${!files[*]}
do
    printf "uploading %d/%d\n" $(($index + 1)) ${#files[*]}
    $PWD/venv/bin/python $HOME/.PyCharm*/config/plugins/intellij-micropython/scripts/microupload.py -C $PWD -v /dev/ttyUSB0 ${files[$index]}
done
