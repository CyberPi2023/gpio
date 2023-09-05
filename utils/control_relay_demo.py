#!/usr/bin/python
import sys
import RPi.GPIO as GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
args = sys.argv
pin = 24 # GPIO PIN 17
ctl = args[1] #Argument 1 for ON/OFF
if (int(ctl) == 1):
  GPIO.setup(pin, GPIO.OUT)
  GPIO.output(pin,GPIO.HIGH)

if (int(ctl) == 0):
  GPIO.setup(pin, GPIO.OUT)
  GPIO.output(pin, GPIO.LOW)
