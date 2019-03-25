from machine import Pin, PWM

class Fan:
    a = -95.1140873015873
    b = 1149.92931547619

    V_fan_max = 12.1
    V_fan_min = 6
    PWM_max_duty = 1023

    def __init__(self, enpin, pwmpin):
        self.en_pin = Pin(enpin, Pin.OUT)
        self.pwm = PWM(Pin(pwmpin))
        self.pwm.freq(312500)

        self.duty = 0
        self.power = 0

    def set_pwm(self, val):
        self.en_pin.value(1)
        self.pwm.duty(val)
        self.duty = val
        return val

    def set(self, val):
        if val > 100:
            val = 100
        if val < self.V_fan_min * 100 / self.V_fan_max:
            val = 0

        self.power = int(val)

        voltage = val * self.V_fan_max / 100
        if voltage > self.V_fan_min:
            PWM_value = (voltage * self.a + self.b)
            if PWM_value > self.PWM_max_duty:
                PWM_value = self.PWM_max_duty

            self.set_pwm(int(PWM_value))
        else:
            self.off()

    def max(self):
        self.en_pin.value(1)
        self.pwm.duty(0)

    def off(self):
        self.en_pin.value(0)
        self.pwm.duty(self.PWM_max_duty)