import RPi.GPIO as GPIO
import time

# w1,w2,w3,w4,w5,w6 = 0,1,0,0,0,0,0   细分400，电流3.5A，电压24V
IN1 = 20  # 接PUL-
IN2 = 21  # 接PUL+
IN3 = 12  # 接DIR-
IN4 = 16  # 接DIR+

def setStep(w1, w2, w3, w4):
    GPIO.output(IN1, w1)
    GPIO.output(IN2, w2)
    GPIO.output(IN3, w3)
    GPIO.output(IN4, w4)

def stop():
    setStep(0, 0, 0, 0)

# 正转
# 控制电机旋转的快慢和圈数 delay越小转得越快，1600为一圈
def forward(delay, steps):
    for i in range(0, steps):
        setStep(1, 0, 1, 0)
        time.sleep(delay)
        setStep(0, 1, 1, 0)
        time.sleep(delay)
        setStep(0, 1, 0, 1)
        time.sleep(delay)
        setStep(1, 0, 0, 1)
        time.sleep(delay)

# 控制电机一直旋转
def yizhi(delay):
    while True:
        setStep(1, 0, 1, 0)
        time.sleep(delay)
        setStep(0, 1, 1, 0)
        time.sleep(delay)
        setStep(0, 1, 0, 1)
        time.sleep(delay)
        setStep(1, 0, 0, 1)
        time.sleep(delay)


# 反转
# 控制电机旋转的快慢和圈数 delay越小转得越快，1600为一圈
def backward(delay, steps):
    for i in range(0, steps):
        setStep(1, 0, 0, 1)
        time.sleep(delay)
        setStep(0, 1, 0, 1)
        time.sleep(delay)
        setStep(0, 1, 1, 0)
        time.sleep(delay)
        setStep(1, 0, 1, 0)
        time.sleep(delay)

# 初始化树莓派引脚，设置树莓派的引脚为输出状态
def setup():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(IN1, GPIO.OUT)
    GPIO.setup(IN2, GPIO.OUT)
    GPIO.setup(IN3, GPIO.OUT)
    GPIO.setup(IN4, GPIO.OUT)

# 带异常处理
# 控制电机正转一圈
def hhh():
    setup()
    try:
         forward(0.0001,1600)
    except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child function destroy() will be  executed.
         destroy()


# 带异常处理
# 控制电机一直旋转
def zzz():
    setup()
    try:
         yizhi(0.0001)
    except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child function destroy() will be  executed.
         destroy()

# 检测正转和反转
def loop():
    while True:
        i=int(input("1、正转\t2、反转\t3、退出\n请输入数字： "))
        if i==1:
            b = int(input("请输入脉冲个数（1600个脉冲为一圈）："))
            forward(0.0001, b)
            print("请等待3秒...")
            time.sleep(3)
            print("stop...")
            stop()
        elif i==2:
            a=int(input("请输入脉冲个数（1600个脉冲为一圈）："))
            backward(0.0001, a)  # 发射脉冲时间间隔0.0001（单位秒）   脉冲个数a 如果编码器的设置是8细分 那么1600冲就转360度
            print("请等待3秒...")
            time.sleep(3)
            print("stop...")
            stop()  # stop
        else:
            destroy()
            return

# 清除树莓派引脚状态赋值
def destroy():
    GPIO.cleanup()  # 释放数据

if __name__ == '__main__':  # Program start from here
   setup()
   try:
        loop()
   except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child function destroy() will be  executed.
        destroy()
