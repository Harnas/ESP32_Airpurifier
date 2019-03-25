import utime
import Settings

class AirCleanerController:
    def __init__(self, read_sensors_callback, settings_controller: Settings):
        self.settings = settings_controller

        self.settings.load_settings()

        self.set_speed = self.settings.settings['set_speed']
        self.manual_speed = self.settings.settings['manual_speed']
        self.mode = self.settings.settings['mode']
        self.read_sensors_callback = read_sensors_callback

        self.sensors_values = {}
        self.last_senor_read = 0

    def save_settings(self):
        self.settings.save_settings()
        return True

    def read_sensors(self):
        if (utime.ticks_ms() - self.last_senor_read) > 1000:
            self.sensors_values = self.read_sensors_callback(self.sensors_values)
            self.last_senor_read = utime.ticks_ms()

    def fan_speed(self):
        if self.settings.settings['mode'] == 'M':
            return self.settings.settings['manual_speed']
        else:
            return int(self.settings.settings['set_speed'] * self.sensors_values["dust_level"] / 20)

    @property
    def temperature(self):
        return self.sensors_values["temperature"]

    @property
    def humidity(self):
        return self.sensors_values["humidity"]

    @property
    def air_pressure(self):
        return self.sensors_values["air_pressure"]

    @property
    def dust_level(self):
        return self.sensors_values["dust_level"]

    @property
    def fan_power(self):
        if self.settings.settings['mode'] == 'M':
            return self.settings.settings['manual_speed']
        else:
            return self.settings.settings['set_speed']

    @property
    def temperature_str(self):
        return "{:.2f}°C".format(self.sensors_values["temperature"])

    @property
    def humidity_str(self):
        return "{:.2f}%".format(self.sensors_values["humidity"])

    @property
    def air_pressure_str(self):
        return self.sensors_values["air_pressure"]

    @property
    def dust_level_str(self):
        return "{:.2f}ug/m3".format(self.sensors_values["dust_level"])

    @property
    def fan_power_str(self):
        if self.settings.settings['mode'] == 'M':
            return "{}%".format(self.settings.settings['manual_speed'])
        else:
            return "{}%".format(self.settings.settings['set_speed'])

