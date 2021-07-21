#!/usr/bin/env python3

import psutil
import time
import datetime
import colorsys
import blinkt
import argparse
from blinkt import set_all, set_pixel, show, clear, set_brightness
from pystemd.systemd1 import Unit
from subprocess import PIPE, Popen
from icecream import ic

# For more info on the psystmd library >>> https://pypi.org/project/pystemd/
# For more on icecream debugging, see https://pypi.org/project/icecream/

# Reading variables for the script
# For more on argparse, refer to https://zetcode.com/python/argparse/

# Get Raspberry Pi Temperature
def get_cpu_temperature():
    process = Popen(
        ["vcgencmd", "measure_temp"], stdout=PIPE, universal_newlines=True
    )
    output, _error = process.communicate()
    ic()
    return float(output[output.index("=") + 1 : output.rindex("'")])

parser = argparse.ArgumentParser(description="Show leds for system status")
parser.add_argument("--debug", type=str, help="Flag to enable or disable icecream debug",required=True)
args = parser.parse_args()
ic(args)

print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Starting program...')

# Enable / disable debugging
if args.debug == "yes":
  print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Debug mode')
  ic()
elif args.debug == "no":
  ic.disable()
  ic()
  print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Debug deactivated')

# Make sure the leds stop and clear on exit
blinkt.set_clear_on_exit()

# Define units
unitDocker = Unit(b'docker.service')
unitPromtail = Unit(b'promtail-pi4.service')
unitPrometheusexporter = Unit(b'prometheusexporter-pi4.service')

# Define colors
red = "64", "0", "0"
orange = "64", "18", "0"
green = "0", "64", "0"
greenSoft = "0", "16", "0"
blue = "0", "0", "1"
white = "16", "16", "16"
magenta = "128", "0", "128"

# Dictionary to map topics to leds
ledDict = {"temp" : 0,\
            "cpuload" : 1,\
            "ramusage" : 2,\
            "diskusage" : 3,\
            "docker" : 4,\
            "promtail" : 5,\
            "prometheusexporter" : 6,\
            "ssh" : 7\
          }

# Test all leds
spacing = 360.0 / 16.0
hue = 0
set_brightness(0.1)

for testFlashes in range(120):
    hue = int(time.time() * 100) % 360
    for x in range(8):
        offset = x * spacing
        h = ((hue + offset) % 360) / 360.0
        r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(h, 1.0, 1.0)]
        set_pixel(x, r, g, b)
    show()
    time.sleep(0.001)

clear()

# Idle color on lights to be used
for led in range (8):
    set_pixel(led, *blue, brightness=0.1)
    time.sleep(0.1)
    show()

while(True):
    
    temp = get_cpu_temperature()
    cpuload = psutil.cpu_percent(interval=1, percpu=False)
    ramusage = psutil.virtual_memory().percent
    diskusage = psutil.disk_usage('/').percent
    unitDocker.load()
    unitPromtail.load()
    unitPrometheusexporter.load()
    sessions = psutil.users()

    # Flash all leds for script status once each time script run
    set_all(*white, brightness=0.5)
    show()
    time.sleep(0.2)

    
    # Configure led for temp
    if temp > 55:
        set_pixel(ledDict["temp"], *red, brightness=0.5)
        show()
        ic()
    elif temp > 45 and temp <= 55 :
        set_pixel(ledDict["temp"], *orange, brightness=0.5)
        show()
        ic()
    elif temp <= 45:
        set_pixel(ledDict["temp"], *greenSoft, brightness=0.1)
        show()
        ic()

    # Configure led for cpu load
    if cpuload > 30:
        set_pixel(ledDict["cpuload"], *red, brightness=0.5)
        show()
        ic()
    elif cpuload > 20 and cpuload <= 30 :
        set_pixel(ledDict["cpuload"], *orange, brightness=0.5)
        show()
        ic()
    elif cpuload <= 20:
        set_pixel(ledDict["cpuload"], *greenSoft, brightness=0.1)
        show()
        ic()
    
    # Configure led for ram usage
    if ramusage > 30:
        set_pixel(ledDict["ramusage"], *red, brightness=0.5)
        show()
        ic()
    elif ramusage > 15 and ramusage <= 30 :
        set_pixel(ledDict["ramusage"], *orange, brightness=0.5)
        show()
        ic()
    elif ramusage <= 15:
        set_pixel(ledDict["ramusage"], *greenSoft, brightness=0.1)
        show()
        ic()

    # Configure led for disk usage
    if diskusage > 60:
        set_pixel(ledDict["diskusage"], *red, brightness=0.5)
        show()
        ic()
    elif diskusage > 55 and diskusage <= 60 :
        set_pixel(ledDict["diskusage"], *orange, brightness=0.5)
        show()
        ic()
    elif diskusage <= 55:
        set_pixel(ledDict["diskusage"], *greenSoft, brightness=0.1)
        show()
        ic()

    # Configure led for docker
    if ic(unitDocker.Unit.ActiveState) == b"active":
        set_pixel(ledDict["docker"], *greenSoft, brightness=0.1)
        show()
        ic()
    else:
        set_pixel(ledDict["docker"], *red, brightness=0.5)
        show()
        ic()
    
    # Configure led for promtail
    if ic(unitPromtail.Unit.ActiveState) == b"active":
        set_pixel(ledDict["promtail"], *greenSoft, brightness=0.1)
        show()
        ic()
    else:
        set_pixel(ledDict["promtail"], *red, brightness=0.5)
        show()
        ic()

    # Configure led for prometheus exporter
    if ic(unitPrometheusexporter.Unit.ActiveState) == b"active":
        set_pixel(ledDict["prometheusexporter"], *greenSoft, brightness=0.1)
        show()
        ic()
    else:
        set_pixel(ledDict["prometheusexporter"], *red, brightness=0.5)
        show()
        ic()

    # Configure led for ssh
    for users in sessions:
        if users.host != "" and users.host != "localhost":
            set_pixel(ledDict["ssh"], *magenta, brightness=0.5)
            show()
            ic()
        else:
            set_pixel(ledDict["ssh"], *greenSoft, brightness=0.1)
            show()
            ic()

    time.sleep(60)