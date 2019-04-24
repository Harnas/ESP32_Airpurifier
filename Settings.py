import os
import ujson

class Settings:
    def __init__(self, settings_filename):
        self.settings_filename = settings_filename
        self.settings = {}
        self.display_on = True

    def save_settings(self):

        f = open(self.settings_filename, 'w')
        f.write(ujson.dumps(self.settings))
        f.close()

        return self.settings

    def load_settings(self):
        if self.settings_filename in os.listdir(""):
            f = open(self.settings_filename)
            self.settings = ujson.loads(f.read())
            f.close()
            return self.settings
        else:
            self.settings['set_speed'] = 70
            self.settings['manual_speed'] = 50
            self.settings['mode'] = 'A'

            return self.save_settings()