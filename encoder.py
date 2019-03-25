# -*- coding: utf-8 -*-
"""
Library for rotary encoder based on https://github.com/SpotlightKid/micropython-stm-lib/blob/master/encoder/encoder.py
"""
from machine import Pin

ENC_STATES = (
    0,  # 00 00
    -1,  # 00 01
    1,  # 00 10
    0,  # 00 11
    1,  # 01 00
    0,  # 01 01
    0,  # 01 10
    -1,  # 01 11
    -1,  # 10 00
    0,  # 10 01
    0,  # 10 10
    1,  # 10 11
    0,  # 11 00
    1,  # 11 01
    -1,  # 11 10
    0  # 11 11
)
ACCEL_THRESHOLD = 5


class Encoder(object):
    def __init__(self, pin_clk, pin_dt, pin_sw, pin_mode=None, clicks=1,
                 min_val=0, max_val=100, accel=0, reverse=False, rotate_event_callback=None,
                 button_event_callback=None):
        self.pin_clk = (pin_clk if isinstance(pin_clk, Pin) else
                        Pin(pin_clk, Pin.IN, pin_mode))
        self.pin_dt = (pin_dt if isinstance(pin_dt, Pin) else
                       Pin(pin_dt, Pin.IN, pin_mode))
        self.pin_sw = (pin_sw if isinstance(pin_sw, Pin) else
                       Pin(pin_sw, Pin.IN, pin_mode))

        self.min_val = min_val * clicks
        self.max_val = max_val * clicks
        self.accel = int((max_val - min_val) / 100 * accel)
        self.max_accel = int((max_val - min_val) / 2)
        self.clicks = clicks
        self.reverse = 1 if reverse else -1
        self.rotate_event_callback = rotate_event_callback
        self.button_event_callback = button_event_callback

        # The following variables are assigned to in the interrupt callback,
        # so we have to allocate them here.
        self._value = 0
        self._readings = 0
        self._state = 0
        self.cur_accel = 0

        self.set_callbacks(self._callback)

    def _callback_sw(self, line):
        self.button_event_callback()

    def _callback(self, line):
        self._readings = (self._readings << 2 | self.pin_clk.value() << 1 |
                          self.pin_dt.value()) & 0x0f

        self._state = ENC_STATES[self._readings] * self.reverse

        if self._state:
            self.cur_accel = min(self.max_accel, self.cur_accel + self.accel)

            self._value = min(self.max_val, max(self.min_val, self._value +
                                                (1 + (self.cur_accel >> ACCEL_THRESHOLD)) *
                                                self._state))

            if self.rotate_event_callback is not None:
                self.rotate_event_callback()

    def set_callbacks(self, callback=None):
        mode = Pin.IRQ_RISING | Pin.IRQ_FALLING
        self.irq_clk = self.pin_clk.irq(trigger=mode, handler=callback)
        self.irq_dt = self.pin_dt.irq(trigger=mode, handler=callback)
        if self.button_event_callback is not None:
            self.pin_sw = self.pin_sw.irq(trigger=mode, handler=self._callback_sw)

    def close(self):
        self.set_callbacks(None)
        mode = Pin.IRQ_RISING | Pin.IRQ_FALLING
        self.pin_sw = self.pin_sw.irq(trigger=mode, handler=None)
        self.irq_clk = self.irq_dt = self.pin_sw = None

    @property
    def value(self):
        return self._value // self.clicks

    @property
    def pressed(self):
        return True if self.pin_sw.value() == 0 else False

    def reset(self):
        self._value = 0
