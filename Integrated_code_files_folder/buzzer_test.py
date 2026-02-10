import RPi.GPIO as GPIO
import time

PIN = 25
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.OUT)

print("Buzzer ON")
GPIO.output(PIN, GPIO.HIGH) # 给高电平
time.sleep(1)               # 持续 1 秒
GPIO.output(PIN, GPIO.LOW)  # 关掉

GPIO.cleanup()