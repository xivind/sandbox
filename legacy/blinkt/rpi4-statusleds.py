"""Code to show system status as led lights"""
#!/usr/bin/env python3

import time
import colorsys
from subprocess import PIPE, Popen
import psutil
import blinkt
from pystemd.systemd1 import Unit

class Blinkt():
    """Class to interact with the Blinkt led device from Pimoroni"""
    def __init__(self):
        self.color_dict = {
            "red" : ("64", "0", "0"),\
            "orange" : ("64", "18", "0"),\
            "green" : ("0", "16", "0"),\
            "blue" : ("0", "0", "1"),\
            "white" : ("16", "16", "16"),\
            "magenta" : ("64", "0", "64"),\
                        }
        self.led_dict = {
            "temp" : 0,\
            "cpuload" : 1,\
            "ramusage" : 2,\
            "diskusage" : 3,\
            "docker" : 4,\
            "promtail" : 5,\
            "prometheus" : 6,\
            "ssh" : 7\
                        }

        self.test_leds()
        self.initialise_leds()

    def test_leds(self):
        """Method to test all leds"""
        spacing = 360.0 / 16.0
        hue = 0
        counter = 0
        blinkt.set_brightness(0.1)

        while counter < 120:
            hue = int(time.time() * 100) % 360
            for led_nr in range(8):
                offset = led_nr * spacing
                hue_modified = ((hue + offset) % 360) / 360.0
                red, green, blue = \
                    [int(color * 255)\
                        for color in colorsys.hsv_to_rgb(hue_modified, 1.0, 1.0)
                    ]
                blinkt.set_pixel(led_nr, red, green, blue)
            blinkt.show()
            time.sleep(0.001)
            counter = counter+1
        blinkt.clear()

    def initialise_leds(self):
        """Method to set idle color on lights to be used"""
        for led in range(8):
            blinkt.set_pixel(led, *self.color_dict["blue"], brightness=0.1)
            time.sleep(0.3)
            blinkt.show()

    def flash_lights(self):
        """Method to flash all lights"""
        blinkt.set_all(*self.color_dict["white"], brightness=0.1)
        blinkt.show()
        time.sleep(0.2)

    def configure_leds(self):
        """
        Method to configur leds
        For more info on the psystmd library >>> https://pypi.org/project/pystemd/
        """
        self.flash_lights()
        SYSTEM.get_system_status()

        if int(SYSTEM.system_status["temp"]) > 55:
            blinkt.set_pixel(self.led_dict["temp"], *self.color_dict["red"], brightness=0.1)
            blinkt.show()

        elif int(SYSTEM.system_status["temp"]) in range(45, 55):
            blinkt.set_pixel(self.led_dict["temp"], *self.color_dict["orange"], brightness=0.1)
            blinkt.show()

        elif int(SYSTEM.system_status["temp"]) < 45:
            blinkt.set_pixel(self.led_dict["temp"], *self.color_dict["green"], brightness=0.1)
            blinkt.show()

        if int(SYSTEM.system_status["cpuload"]) > 50:
            blinkt.set_pixel(self.led_dict["cpuload"], *self.color_dict["red"], brightness=0.1)
            blinkt.show()

        elif int(SYSTEM.system_status["cpuload"]) in range(20, 50):
            blinkt.set_pixel(self.led_dict["cpuload"], *self.color_dict["orange"], brightness=0.1)
            blinkt.show()

        elif int(SYSTEM.system_status["cpuload"]) < 20:
            blinkt.set_pixel(self.led_dict["cpuload"], *self.color_dict["green"], brightness=0.1)
            blinkt.show()

        if int(SYSTEM.system_status["ramusage"]) > 50:
            blinkt.set_pixel(self.led_dict["ramusage"], *self.color_dict["red"], brightness=0.1)
            blinkt.show()

        elif int(SYSTEM.system_status["ramusage"]) in range(20, 50):
            blinkt.set_pixel(self.led_dict["ramusage"], *self.color_dict["orange"], brightness=0.1)
            blinkt.show()

        elif int(SYSTEM.system_status["ramusage"]) < 20:
            blinkt.set_pixel(self.led_dict["ramusage"], *self.color_dict["green"], brightness=0.1)
            blinkt.show()

        if int(SYSTEM.system_status["diskusage"]) > 75:
            blinkt.set_pixel(self.led_dict["diskusage"], *self.color_dict["red"], brightness=0.1)
            blinkt.show()

        elif int(SYSTEM.system_status["diskusage"]) in range(60, 75):
            blinkt.set_pixel(self.led_dict["diskusage"], *self.color_dict["orange"], brightness=0.1)
            blinkt.show()

        elif int(SYSTEM.system_status["diskusage"]) < 60:
            blinkt.set_pixel(self.led_dict["diskusage"], *self.color_dict["green"], brightness=0.1)
            blinkt.show()

        if SYSTEM.system_status["docker"] == b"active":
            blinkt.set_pixel(self.led_dict["docker"], *self.color_dict["green"], brightness=0.1)
            blinkt.show()

        else:
            blinkt.set_pixel(self.led_dict["docker"], *self.color_dict["red"], brightness=0.1)
            blinkt.show()

        if SYSTEM.system_status["promtail"] == b"active":
            blinkt.set_pixel(self.led_dict["promtail"], *self.color_dict["green"], brightness=0.1)
            blinkt.show()

        else:
            blinkt.set_pixel(self.led_dict["promtail"], *self.color_dict["red"], brightness=0.1)
            blinkt.show()

        if SYSTEM.system_status["prometheus"] == b"active":
            blinkt.set_pixel(self.led_dict["prometheus"], *self.color_dict["green"], brightness=0.1)
            blinkt.show()

        else:
            blinkt.set_pixel(self.led_dict["prometheus"], *self.color_dict["red"], brightness=0.1)
            blinkt.show()

        for users in SYSTEM.system_status["ssh"]:
            if users.host != "" and users.host != "localhost":
                blinkt.set_pixel(self.led_dict["ssh"], *self.color_dict["magenta"], brightness=0.1)
                blinkt.show()

            else:
                blinkt.set_pixel(self.led_dict["ssh"], *self.color_dict["green"], brightness=0.1)
                blinkt.show()
class System():
    """Class to retrieve system information"""
    def __init__(self):
        self.unit_docker = Unit(b'docker.service')
        self.unit_promtail = Unit(b'promtail-pi4.service')
        self.unit_prometheus = Unit(b'prometheusexporter-pi4.service')
        self.system_status = {}

    def get_system_status(self):
        """Method to read and store system status"""
        self.system_status = {}
        self.unit_docker.load()
        self.unit_promtail.load()
        self.unit_prometheus.load()
        self.system_status.update({
            "temp" : self.get_cpu_temperature(),\
            "cpuload" : psutil.cpu_percent(interval=1, percpu=False),\
            "ramusage" : psutil.virtual_memory().percent,\
            "diskusage" : psutil.disk_usage('/').percent,\
            "docker" : self.unit_docker.Unit.ActiveState,\
            "promtail" : self.unit_promtail.Unit.ActiveState,\
            "prometheus" : self.unit_prometheus.Unit.ActiveState,\
            "ssh" : psutil.users(),\
                                })

    def get_cpu_temperature(self):
        """Method to get Pi temperature"""
        process = Popen(
            ["vcgencmd", "measure_temp"], stdout=PIPE, universal_newlines=True
        )
        output, _error = process.communicate()
        return float(output[output.index("=") + 1 : output.rindex("'")])

if __name__ == "__main__":

    SYSTEM = System()
    LED_DEVICE = Blinkt()

    while True:
        LED_DEVICE.configure_leds()
        time.sleep(60)
