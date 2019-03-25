import micropython
micropython.opt_level(3)

import _thread
import network
import utime
from machine import Pin, I2C, Timer, deepsleep
import ujson

import BME280
import DustSensor
import Fan
import HDC1000
import encoder
import ssd1306
import AirCleanerController
import Settings



WIFI_CREDENTIALS_FILENAME = 'wifi_credentials.json'
SETTINGS_FILENAME = 'settings.json'



def connect_to_strongest_wifi():
    try:
        f = open(WIFI_CREDENTIALS_FILENAME)
        wifi_credentials = ujson.loads(f.read())
        f.close()

        sta_if = network.WLAN(network.STA_IF)
        sta_if.active(False)
        sta_if.active(True)
        sta_if.disconnect()
        available_nets = sta_if.scan()

        for net in available_nets:
            ssid = net[0].decode("utf-8")
            if ssid in wifi_credentials:
                print("connecting to: " + ssid)
                sta_if.connect(ssid, wifi_credentials[ssid])

                time_start = utime.ticks_ms()
                while not sta_if.isconnected() and (utime.ticks_ms() - time_start) < 5000:
                    utime.sleep_ms(100)
                    pass

                if sta_if.ifconfig()[0] == '0.0.0.0':
                    sta_if.disconnect()
                else:
                    return sta_if.ifconfig()
        return sta_if.ifconfig()
    except Exception:
        return sta_if.ifconfig()

try:
    import picoweb
except Exception:
    import upip

    connect_to_strongest_wifi()
    upip.install('picoweb')
    upip.install('micropython-ulogging')

    # update to other version
    # solution from https://forum.micropython.org/viewtopic.php?t=6002
    upip.save_file("lib/uasyncio/__init__.py", upip.url_open(
        "https://raw.githubusercontent.com/micropython/micropython-lib/master/uasyncio/uasyncio/__init__.py"))
    upip.save_file("lib/uasyncio/core.py", upip.url_open(
        "https://raw.githubusercontent.com/micropython/micropython-lib/master/uasyncio.core/uasyncio/core.py"))

    import picoweb


def wifi_maintenance():
    sta_if = network.WLAN(network.STA_IF)

    if sta_if.ifconfig()[0] == '0.0.0.0' or not sta_if.isconnected():
        return connect_to_strongest_wifi()
    return sta_if.ifconfig()


def dust_sensor_thread():
    while True:
        dust_sensor.measure_average_quick()
        utime.sleep_us(9700)
        # for i in range(30):
        #     dust_sensor.measure_average_quick()
        #     utime.sleep_us(9700)
        #
        # utime.sleep_ms(500)


encoder_button_event_time = 0


def encoder_button_event():
    global encoder_button_event_time
    if (utime.ticks_ms() - encoder_button_event_time) > 1000:
        if settings.settings['mode'] == 'M':
            settings.settings['mode'] = 'A'
        else:
            settings.settings['mode'] = 'M'
    encoder_button_event_time = utime.ticks_ms()


board_button_event_time = 0


def board_button_event():
    global board_button_event_time
    if (utime.ticks_ms() - board_button_event_time) > 1000:
        main_controller.save_settings()
    board_button_event_time = utime.ticks_ms()


def encoder_rotate_event():
    if settings.settings['mode'] == 'M':
        settings.settings['manual_speed'] += enc.value
        settings.settings['manual_speed'] = min(100, max(0, settings.settings['manual_speed']))
    else:
        settings.settings['set_speed'] += enc.value
        settings.settings['set_speed'] = min(100, max(0, settings.settings['set_speed']))

    enc.reset()


def i2c_sensors_read(sensors_values):
    sensors_values["HDC_temperature"] = hdc1000.readTemperature()
    sensors_values["HDC_humidity"] = hdc1000.readHumidity()
    sensors_values["BMP_temperature"] = bme.temperature
    sensors_values["BMP_pressure"] = bme.pressure


def read_sensors(sensors_values):
    i2c_sensors_read(sensors_values)
    for i in range(30):
        dust_sensor.measure_average_quick()
        utime.sleep_us(11000)

    adc_read, calcVoltage, dustDensity = dust_sensor.get_average()
    sensors_values["dust_level"] = dustDensity

    sensors_values["temperature"] = sensors_values["HDC_temperature"]
    sensors_values["humidity"] = sensors_values["HDC_humidity"]
    sensors_values["air_pressure"] = sensors_values["BMP_pressure"]
    sensors_values["dust_level"] = sensors_values["dust_level"]

    return sensors_values



server = None
if __name__ == "__main__":
    Button_pin = 4
    LED_pin = 2
    button = Pin(Button_pin, Pin.IN, Pin.PULL_UP)
    led = Pin(LED_pin, Pin.OUT)

    Dust_sensor_LED_pin = 14
    Dust_sensor_IN_pin = 35
    Dust_sensor_V_ref_pin = 34
    Fan_PWM_pin = 26
    FAN_EN_pin = 2

    ENC_SW_pin = 27
    ENC_DT_pin = 16
    ENC_CLK_pin = 17

    settings = Settings.Settings(settings_filename=SETTINGS_FILENAME)
    main_controller = AirCleanerController.AirCleanerController(read_sensors_callback=read_sensors, settings_controller=settings)

    enc = encoder.Encoder(pin_clk=ENC_CLK_pin, pin_dt=ENC_DT_pin, pin_sw=ENC_SW_pin, pin_mode=Pin.PULL_UP, min_val=-100,
                          max_val=100, clicks=1, reverse=True, rotate_event_callback=encoder_rotate_event,
                          button_event_callback=encoder_button_event)

    fan = Fan.Fan(enpin=FAN_EN_pin, pwmpin=Fan_PWM_pin)
    dust_sensor = DustSensor.DustSensor(ledpin=Dust_sensor_LED_pin, adcpin=Dust_sensor_IN_pin,
                                        refpin=Dust_sensor_V_ref_pin)

    i2c = I2C(scl=Pin(19), sda=Pin(23), freq=200000)
    i2c2 = I2C(scl=Pin(5), sda=Pin(13))
    oled = ssd1306.SSD1306_I2C(128, 64, i2c)
    oled.contrast(1)

    bme = BME280.BME280(i2c=i2c)

    hdc1000 = HDC1000.HDC1000(i2c=i2c)
    hdc1000.turnHeaterOff()
    hdc1000.setHumidityResolution(HDC1000.HDC1000_CONFIG_HUMIDITY_RESOLUTION_8BIT)
    hdc1000.setTemperatureResolution(HDC1000.HDC1000_CONFIG_TEMPERATURE_RESOLUTION_11BIT)

    if button.value() == 0:
        oled.fill(0)
        line = 0
        oled.text("Internal I2C Devices ID:", 0, line)
        line += 8
        oled.text(','.join(map(str, i2c.scan())), 0, line)
        line += 8
        oled.text("External I2C Devices ID:", 0, line)
        line += 8
        oled.text(','.join(map(str, i2c2.scan())), 0, line)
        oled.show()
        utime.sleep(10)
        oled.fill(0)
        oled.show()
        deepsleep()
        raise SystemExit(0)

    button = button.irq(trigger=Pin.IRQ_FALLING, handler=board_button_event)

    oled.fill(0)
    line = 0
    oled.text("Connecting", 0, line)
    line += 8
    oled.text("to wifi...", 0, line)
    oled.show()
    ipadd = wifi_maintenance()

    app = picoweb.WebApp(__name__)


    @app.route("/")
    def index(req, resp):
        yield from app.sendfile(resp, 'static/index.html', 'text/html')
        yield from resp.aclose()


    @app.route("/data")
    def light(req, resp):

        if req.method == "POST":
            yield from req.read_form_data()
            data = ujson.loads(list(req.form.keys())[0])

            if data['_mode'] == 'A':
                settings.settings['mode'] = 'A'
            elif data['_mode'] == 'M':
                settings.settings['mode'] = 'M'

            settings.settings['manual_speed'] = min(100, max(0, int(data["_manual_speed"])))
            settings.settings['set_speed'] = min(100, max(0, int(data["_auto_speed"])))

        sensors_values = {"Temperature": main_controller.temperature, "Humidity": main_controller.humidity,
                          "Pressure": main_controller.air_pressure, "Dust": main_controller.dust_level,
                          "Power": main_controller.fan_power, "Fan": fan.power, "_mode": settings.settings['mode'],
                          "_manual_speed": settings.settings['manual_speed'], "_auto_speed": settings.settings['set_speed']}

        encoded = ujson.dumps(sensors_values)
        yield from picoweb.start_response(resp, content_type="application/json")
        yield from resp.awrite(encoded)


    def webserver_thread():
        app.run(debug=True, host=ipadd[0])


    _thread.start_new_thread(webserver_thread, ())
    #_thread.start_new_thread(dust_sensor_thread, ())

    dust_sensor.measure_average_quick()
    main_controller.read_sensors()
    oled.fill(0)
    oled.show()


    while True:
        ipadd = wifi_maintenance()

        main_controller.read_sensors()
        fan.set(main_controller.fan_speed())

        oled.fill(0)
        line = 0
        oled.text("{:2.2f}C   {:3.2f}%".format(main_controller.temperature, main_controller.humidity),
                  0, line)
        line += 8
        oled.text("%s" % main_controller.air_pressure, 0, line)
        line += 8
        oled.text("PM: %.1fug/m3" % main_controller.dust_level, 0, line)
        line += 8
        line += 8
        oled.text("Set:%d Fan:%d %s" % (main_controller.fan_power, fan.power, settings.settings['mode']), 0, line)
        line += 8
        line += 8
        oled.text(ipadd[0], 0, line)
        oled.show()

        utime.sleep_ms(500)
