#-*- coding=utf-8 -*-
import time
import argparse
from utils.logger import Logger
from motor_manager import MotorManager
from relay_manager import RelayManager
from recognizer import Recognizer

LOG = Logger(__file__)
PULSE_STD = 1600
ROAD_PAULSE_COUNT = 1600 * 12.63

class Crane(object):
    def __init__(self):
        # 电机 A：控制上下悬臂
        self.motor_a = MotorManager(pul_negative_pin_number=20, pul_positive_pin_number=21, dir_negative_pin_number=12, dir_positive_pin_number=13)
        # 电机 B：控制旋转角度
        self.motor_b = MotorManager(pul_negative_pin_number=22, pul_positive_pin_number=23, dir_negative_pin_number=16, dir_positive_pin_number=17)
        # 电机 C：控制轨道
        self.motor_c = MotorManager(pul_negative_pin_number=26, pul_positive_pin_number=27, dir_negative_pin_number=4, dir_positive_pin_number=5)
        # 气泵
        self.relay_pump = RelayManager(gpio_pin_number=24)
        # 气阀
        self.relay_valve = RelayManager(gpio_pin_number=25)
        self.recognizer = Recognizer()
        self.road_pulse = ROAD_PAULSE_COUNT
        self.box_count = 0
        self.cans_count = 0
        self.log_properties()

    @staticmethod
    def pulse_angle(angle):
        return angle * 10 / 360 * PULSE_STD
    @staticmethod
    def pulse_distance(distance):
        return distance / 21.75 * PULSE_STD

    def log_properties(self):
        LOG.info(self.__dict__)

    def suck_cargo(self):
        self.relay_pump.turn_on() # 气泵通电，吸取
        self.relay_valve.turn_off() # 气阀断电，不放气
        time.sleep(3)

    def release_cargo(self):
        self.relay_pump.turn_off() # 气泵断电，释放
        self.relay_valve.turn_on() # 气阀通电，放气
        time.sleep(3)

    def clean_pins(self):
        self.motor_a.destroy()
        self.motor_b.destroy()
        self.relay_pump.destroy()
        self.relay_valve.destroy()

    def init_position(self):
        # 初始化装置位置
        LOG.info("Initialize Crane Pozition")
        self.motor_a.upward(Crane.pulse_distance(130))
        self.motor_c.forward(self.road_pulse * 0.126)
        self.motor_b.clockwise(Crane.pulse_angle(86))
        self.recognizer.recognize()

    def carry_cargo(self, object_name):
        i = 0
        search_count = 0
        while self.recognizer.object_name != object_name and search_count < 3 or self.recognizer.object_name == object_name and self.recognizer.object_score < 91 and search_count < 3:
            # 旋转悬臂直到找到目标物体，搜索三遍
            if i < 5:
                self.motor_b.clockwise(Crane.pulse_angle(36))
                i = i + 1
            else:
                search_count = search_count + 1
                self.motor_b.anticlockwise(Crane.pulse_angle(36*i))
                i = 0
            self.recognizer.recognize()
            LOG.info("Current Recognize: {} - {}%%".format(self.recognizer.object_name, self.recognizer.object_score))
            LOG.info("Search {} {} times, offset: {}".format(object_name, search_count, i))
        if self.recognizer.object_name == object_name and self.recognizer.object_score >= 91:
            # 若为目标物体，并且置信度在 91% 以上，则吸取物体
            LOG.info("Suck: {}".format(object_name))
            self.suck_cargo()
            self.motor_a.downward(Crane.pulse_distance(6.5))
            time.sleep(1)
            self.motor_a.upward(Crane.pulse_distance(230))
        self.motor_c.backward(self.road_pulse)
        self.motor_b.anticlockwise(Crane.pulse_angle(36*i + 90)) # 根据查找工位的坐标计算偏离角度
        time.sleep(1)
        LOG.info("Release: {}".format(object_name))
        self.release_cargo()
        # 释放目标物体后，等待三秒回到初始位置
        self.motor_c.forward(self.road_pulse)
        self.motor_b.clockwise(Crane.pulse_angle(90))
        self.motor_a.downward(Crane.pulse_distance(75))

    def run(self):
        LOG.info("Start Crane")
        self.init_position()
        while self.box_count < 3 or self.cans_count < 3:
            if self.box_count < 3:
                # 优先吸取保鲜盒
                LOG.info("Prepare to carry box")
                self.carry_cargo(object_name="box")
                self.box_count = self.box_count + 1
            else:
                LOG.info("Prepare to carry cans")
                self.carry_cargo(object_name="cans")
                self.cans_count = self.cans_count + 1
            LOG.info("Box: {}; Cans: {}".format(self.box_count, self.cans_count))
            LOG.info("Manual Cancel")
        self.clean_pins()
        exit(0)

if __name__ == "__main__":
    crane = Crane()
    crane.run()
