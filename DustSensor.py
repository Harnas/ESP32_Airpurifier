import utime
from machine import Pin, ADC, PWM

class DustSensor:
    raw = 0
    voltage = 0
    dust = 0
    buff_size = 1500
    values = [0] * buff_size
    buff_i = 0
    buff_fill = 0
    Vref = 0
    sleep = 9700
    start = 0
    delta = 0

    def __init__(self, ledpin, adcpin, refpin):
        self.led = Pin(ledpin, Pin.OPEN_DRAIN)
        Vs = Pin(adcpin)
        self.adc = ADC(Vs)
        Vo = Pin(refpin)
        self.ref = ADC(Vo)
        # self.adc.atten(self.adc.ATTN_0DB)
        self.led.value(1)
        self.start = utime.ticks_us()

    def read_nowait(self):
        #self.delta = utime.ticks_diff(utime.ticks_us(), self.start)
        self.led.value(0)
        utime.sleep_us(270)
        self.raw = self.adc.read()
        self.Vref = self.ref.read()
        self.led.value(1)

        self.raw = self.raw * 1980 / self.Vref
        self.start = utime.ticks_us()
        return self.raw

    def read(self):
        self.read_nowait()
        utime.sleep_us(9700)
        return self.raw
        # return res

    def measure_avg(self, num_samples):
        adc_total = 0
        for x in range(0, num_samples):
            adc = self.read()
            adc_total = adc_total + adc

        return adc_total / num_samples

    def get_average(self):
        self.raw = sum(self.values) / self.buff_fill  # tuple([sum(x) / self.buff_fill for x in zip(*self.values)])
        self.voltage = self.raw * (1.1 / 1024.0)
        self.dust = 200 * (self.voltage - 0.6)

        return self.raw, self.voltage, self.dust

    def measure_average(self, num_samples):
        self.values[self.buff_i] = self.measure_avg(num_samples)
        self.buff_i = (self.buff_i + 1) % self.buff_size

        if self.buff_fill < self.buff_size:
            self.buff_fill = self.buff_fill + 1

    def measure_average_quick(self):
        self.values[self.buff_i] = self.read_nowait()
        self.buff_i = (self.buff_i + 1) % self.buff_size

        if self.buff_fill < self.buff_size:
            self.buff_fill = self.buff_fill + 1