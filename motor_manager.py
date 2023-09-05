#-*- coding=utf-8 -*-
import RPi.GPIO as GPIO
import time
import argparse
import math
from utils.logger import Logger
LOG = Logger(__file__)

def read_args():
# Usage:
    parser = argparse.ArgumentParser()
    parser.add_argument('-pn', '--pul_negative_pin_number', help="The PUL- GPIO Pin Number", type=int, required=False)
    parser.add_argument('-pp', '--pul_positive_pin_number', help="The PUL+ GPIO Pin Number", type=int, required=False)
    parser.add_argument('-dn', '--dir_negative_pin_number', help="The DIR- GPIO Pin Number", type=int, required=False)
    parser.add_argument('-dp', '--dir_positive_pin_number', help="The DIR+ GPIO Pin Number", type=int, required=False)
    parser.add_argument('-t', '--delay_time', help="The Delay Time", type=int, required=False)

    return parser.parse_args()

class MotorManager(object):
    def __init__(self, pul_negative_pin_number=20, pul_positive_pin_number=21, dir_negative_pin_number=12, dir_positive_pin_number=16, delay=0.0001):
        self.pul_negative_pin_number = pul_negative_pin_number
        self.pul_positive_pin_number = pul_positive_pin_number
        self.dir_negative_pin_number = dir_negative_pin_number
        self.dir_positive_pin_number = dir_positive_pin_number
        self.delay = delay
        self.setup()
        self.log_properties()

    def log_properties(self):
        LOG.info(self.__dict__)

    def setup(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pul_negative_pin_number, GPIO.OUT)
        GPIO.setup(self.pul_positive_pin_number, GPIO.OUT)
        GPIO.setup(self.dir_negative_pin_number, GPIO.OUT)
        GPIO.setup(self.dir_positive_pin_number, GPIO.OUT)

    def set_voltage(self, pul_n=GPIO.HIGH, pul_p=GPIO.LOW, dir_n=GPIO.HIGH, dir_p=GPIO.LOW):
        GPIO.output(self.pul_negative_pin_number, pul_n)
        GPIO.output(self.pul_positive_pin_number, pul_p)
        GPIO.output(self.dir_negative_pin_number, dir_n)
        GPIO.output(self.dir_positive_pin_number, dir_p)

    def stop(self):
        self.set_voltage(pul_n=GPIO.LOW,pul_p=GPIO.LOW,dir_n=GPIO.LOW,dir_p=GPIO.LOW)

    def backward(self, pulse_count, action_name="backward"):
        LOG.info("{}: {}".format(action_name, pulse_count))
        for i in range(0, math.ceil(pulse_count)):
            self.set_voltage(GPIO.HIGH, GPIO.LOW, GPIO.HIGH, GPIO.LOW)
            time.sleep(self.delay)
            self.set_voltage(GPIO.LOW, GPIO.HIGH, GPIO.HIGH, GPIO.LOW)
            time.sleep(self.delay)
            self.set_voltage(GPIO.LOW, GPIO.HIGH, GPIO.LOW, GPIO.HIGH)
            time.sleep(self.delay)
            self.set_voltage(GPIO.HIGH, GPIO.LOW, GPIO.LOW, GPIO.HIGH)
            time.sleep(self.delay)

    def forward(self, pulse_count, action_name="forward"):
        LOG.info("{}: {}".format(action_name, pulse_count))
        for i in range(0, math.ceil(pulse_count)):
            self.set_voltage(GPIO.HIGH, GPIO.LOW, GPIO.LOW, GPIO.HIGH)
            time.sleep(self.delay)
            self.set_voltage(GPIO.LOW, GPIO.HIGH, GPIO.LOW, GPIO.HIGH)
            time.sleep(self.delay)
            self.set_voltage(GPIO.LOW, GPIO.HIGH, GPIO.HIGH, GPIO.LOW)
            time.sleep(self.delay)
            self.set_voltage(GPIO.HIGH, GPIO.LOW, GPIO.HIGH, GPIO.LOW)
            time.sleep(self.delay)

    def upward(self, pulse_count):
        self.forward(pulse_count=pulse_count, action_name="upward")

    def downward(self, pulse_count):
        self.backward(pulse_count=pulse_count, action_name="downward")

    def clockwise(self, pulse_count):
        self.forward(pulse_count=pulse_count, action_name="clockwise")

    def anticlockwise(self, pulse_count):
        self.backward(pulse_count=pulse_count, action_name="anticlockwise")

    def destroy(self):
        # 清除树莓派引脚状态赋值
        GPIO.cleanup()  # 释放数据

    def run(self):
        self.forword()

if __name__ == "__main__":
    args = read_args()
    LOG.info(args)
    motor = MotorManager()
    motor.run()
