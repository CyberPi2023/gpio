#-*- coding=utf-8 -*-
import time
import argparse
from utils.logger import Logger
LOG = Logger(__file__)
import RPi.GPIO as GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

def read_args():
# Usage:
# python relay_manager.py --gpio_pin_number 23 --pin_status 1
# python relay_manager.py -p 23 -s 0
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--gpio_pin_number', help="The GPIO Pin Number", type=int, required=False)
    parser.add_argument('-s', '--pin_status', help="The GPIO Pin Status, 1 for High, 0 for low", type=int, required=False)

    return parser.parse_args()

class RelayManager(object):
    def __init__(self, gpio_pin_number=24, pin_status=0):
        self.gpio_pin_number = gpio_pin_number
        self.pin_status = pin_status
        self.log_properties()

    def log_properties(self):
        LOG.info(self.__dict__)

    def setup_pin(self):
        if (self.pin_status == 1):
            GPIO.setup(self.gpio_pin_number, GPIO.OUT)
            GPIO.output(self.gpio_pin_number,GPIO.HIGH)

        elif (self.pin_status == 0):
            GPIO.setup(self.gpio_pin_number, GPIO.OUT)
            GPIO.output(self.gpio_pin_number, GPIO.LOW)

    def turn_on(self):
        self.pin_status = 1
        self.setup_pin()
        LOG.info("Change Pin<{}> On: {}".format(self.gpio_pin_number, self.pin_status))

    def turn_off(self):
        self.pin_status = 0
        self.setup_pin()
        LOG.info("Change Pin<{}> On: {}".format(self.gpio_pin_number, self.pin_status))

    def run(self):
        self.turn_on()
        time.sleep(3)
        self.turn_off()

    def destroy(self):
        # 清除树莓派引脚状态赋值
        GPIO.cleanup()  # 释放数据

if __name__ == "__main__":
    args = read_args()
    LOG.info(args)
    relay = RelayManager(gpio_pin_number=args.gpio_pin_number, pin_status=args.pin_status)
    relay.run()

