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

CONVERT_TEMP_TO_F = True
SAMPLE_SIZE = 10
LOG_IF_CHANGED_BY = 0.05
LOG_IF_TEMPERATURE_CHANGED = True
LOG_IF_HUMIDITY_CHANGED = False

IS_BUCKET_NAME = os.getenv("IS_BUCKET_NAME", "")
IS_BUCKET_KEY = os.getenv("IS_BUCKET_KEY", "")
IS_ACCESS_KEY = os.getenv("IS_ACCESS_KEY", "")
# Force this const to False to turn off streaming to InitialState
SKIP_IS_STREAM = not IS_BUCKET_NAME or not IS_BUCKET_KEY or not IS_ACCESS_KEY

CSV_OUT_FILE_NAME = "data_%s.csv" % datetime.now().strftime("%Y%m%d%H%M%S")
if CSV_OUT_FILE_NAME:
    with open(CSV_OUT_FILE_NAME, "w") as c:
        c.write("timestamp,temperature,humidity")


def show_consts():
    print("-"*40)
    print("DHT11_PIN = %s" % eval("DHT11_PIN"))
    print("CONVERT_TEMP_TO_F = %s" % eval("CONVERT_TEMP_TO_F"))
    print("SAMPLE_SIZE = %s" % eval("SAMPLE_SIZE"))
    print("LOG_IF_CHANGED_BY = %s" % eval("LOG_IF_CHANGED_BY"))
    print("LOG_IF_HUMIDITY_CHANGED = %s" % eval("LOG_IF_HUMIDITY_CHANGED"))
    print("LOG_IF_TEMPERATURE_CHANGED = %s" % eval("LOG_IF_TEMPERATURE_CHANGED"))
    print("CSV_OUT_FILE_NAME = %s" % eval("CSV_OUT_FILE_NAME"))
    print("-"*40)

IS_BUCKET_NAME = os.getenv("IS_BUCKET_NAME", "")
IS_BUCKET_KEY = os.getenv("IS_BUCKET_KEY", "")
IS_ACCESS_KEY = os.getenv("IS_ACCESS_KEY", "")
# Force this const to False to turn off streaming to InitialState
SKIP_IS_STREAM = not IS_BUCKET_NAME or not IS_BUCKET_KEY or not IS_ACCESS_KEY

def c2f(c):
    return (c * 9/5) + 32


def read_sensor(sensor):
    sample_total_temperature = 0.0
    sample_total_humidity = 0.0
    for i in range(SAMPLE_SIZE):
        time.sleep(1)
        result = sensor.read()
        while not result.is_valid():
            result = sensor.read()
        sample_total_temperature += result.temperature
        sample_total_humidity += result.humidity
    temperature = sample_total_temperature / SAMPLE_SIZE
    humidity = sample_total_humidity / SAMPLE_SIZE
    return humidity, temperature


def stream_to_initalstate(temperature, humidity):
    if not SKIP_IS_STREAM:
        s = Streamer(bucket_name=IS_BUCKET_NAME, bucket_key=IS_BUCKET_KEY, access_key=IS_ACCESS_KEY)
        s.log("temperature", "%.2f" % temperature)
        s.log("humidity", "%.2f" % humidity)
        s.flush()
        s.close()


def main():
    print("Start Reading with the following configuration:")
    show_consts()
    sensor = dht11.DHT11(pin=DHT11_PIN)
    previous_temperature = -999.99
    previous_humidity = -999.99
    while True:
        humidity, temperature = read_sensor(sensor)

        if CONVERT_TEMP_TO_F:
            temperature = c2f(temperature)

        if not math.isclose(temperature, previous_temperature, abs_tol=LOG_IF_CHANGED_BY) \
                or (LOG_IF_HUMIDITY_CHANGED and not math.isclose(humidity, previous_humidity, abs_tol=LOG_IF_CHANGED_BY)):
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            stream_to_initalstate(temperature, humidity)
            print("%s %.2f%s %.2f%%" % (now, temperature, "F" if CONVERT_TEMP_TO_F else "C", humidity))
            if CSV_OUT_FILE_NAME:
                with open(CSV_OUT_FILE_NAME, "a") as d:
                    d.write("%s,%-.2f,%.2f\n" % (now, temperature, humidity))

        previous_temperature = temperature
        previous_humidity = humidity


if __name__ == "__main__":
    main()
