#!/bin/bash

files=(ssd1306.py BME280.py HDC1000.py encoder.py DustSensor.py Fan.py Settings.py AirCleanerController.py wifi_credentials.json main.py static/)

echo "Uploading.."
for index in ${!files[*]}
do
    printf "uploading %d/%d\n" $(($index + 1)) ${#files[*]}
    $PWD/venv/bin/python $HOME/.PyCharm*/config/plugins/intellij-micropython/scripts/microupload.py -C $PWD -v /dev/ttyUSB0 ${files[$index]}
done
