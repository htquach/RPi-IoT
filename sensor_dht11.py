#!/usr/bin/python3
import math
import os
import time
from datetime import datetime

import RPi.GPIO as GPIO
import dht11
from ISStreamer.Streamer import Streamer
from dotenv import load_dotenv

load_dotenv()

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.cleanup()
DHT11_PIN = os.getenv("DHT11_PIN", 24)

IS_BUCKET_NAME = os.getenv("IS_BUCKET_NAME", "")
IS_BUCKET_KEY = os.getenv("IS_BUCKET_KEY", "")
IS_ACCESS_KEY = os.getenv("IS_ACCESS_KEY", "")
# Force this const to False to turn off streaming to InitialState
SKIP_IS_STREAM = not IS_BUCKET_NAME or not IS_BUCKET_KEY or not IS_ACCESS_KEY


def c2f(c):
    return (c * 9/5) + 32


def main():
    sensor = dht11.DHT11(pin=DHT11_PIN)
    previous_result = sensor.read()
    previous_result.temperature = 0.0
    previous_result.humidity = 0.0
    run_id = datetime.now().strftime("%Y%m%d%H%M%S")
    while True:
        result = sensor.read()
        while not result.is_valid():
            result = sensor.read()
        if not math.isclose(result.temperature, previous_result.temperature, abs_tol=0.00001):
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f = c2f(result.temperature)
            stream_to_initalstate(result)
            print("%s %.2fC %.2fF %.2f%%" % (now, result.temperature, f, result.humidity))
            with open("data/water_heater_%s.csv" % run_id, "a") as d:
                d.write("%s,%-.2f,%.2f,%.2f\n" % (now, result.temperature, f, result.humidity))
        previous_result = result
        time.sleep(1)


def stream_to_initalstate(result):
    if not SKIP_IS_STREAM and result.is_valid():
        s = Streamer(bucket_name=IS_BUCKET_NAME, bucket_key=IS_BUCKET_KEY, access_key=IS_ACCESS_KEY)
        s.log("temperature", "%.2f" % c2f(result.temperature))
        s.log("humidity", "%.2f" % result.humidity)
        s.flush()
        s.close()


if __name__ == "__main__":
    main()
