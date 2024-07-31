#!/usr/bin/python3
# pylint: disable=line-too-long
"""Reading the DHT11 sensor using a Raspberry Pi"""
import math
import os
import platform
import time
from datetime import datetime

import requests
from ISStreamer.Streamer import Streamer
from dotenv import load_dotenv

# pylint: disable=import-error
from RPi import GPIO
import dht11

# pylint: enable=import-error

load_dotenv()

SENSOR_ID = platform.node()

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.cleanup()
DHT11_PIN = int(os.getenv("DHT11_PIN", "24"))


CONVERT_TEMP_TO_F = True
SAMPLE_SIZE = 10
LOG_IF_CHANGED_BY = 0.1
LOG_IF_TEMPERATURE_CHANGED = True
LOG_IF_HUMIDITY_CHANGED = False

IS_BUCKET_NAME = os.getenv("IS_BUCKET_NAME", "")
IS_BUCKET_KEY = os.getenv("IS_BUCKET_KEY", "")
IS_ACCESS_KEY = os.getenv("IS_ACCESS_KEY", "")
# Force this const to False to turn off streaming to InitialState
STREAM_TO_INITIAL_STATE = bool(IS_BUCKET_NAME and IS_BUCKET_KEY and IS_ACCESS_KEY)

LOGSTASH_HOSTS = os.getenv("LOGSTASH_HOSTS", "")
LOGSTASH_DEFAULT_HTTP_PORT = "8080"

CSV_OUT_FILE_NAME = f"data_{SENSOR_ID}_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"


def parse_hosts(hosts, default_port=LOGSTASH_DEFAULT_HTTP_PORT):
    """Parse a list commas separated hosts"""
    hosts_ports = []
    for logstash_host in hosts.split(","):
        if not logstash_host:
            continue
        if logstash_host.count(":") == 1:
            host, port = logstash_host.split(":")
            hosts_ports.append((host.strip(), port.strip()))
        else:
            hosts_ports.append((logstash_host.strip(), default_port))
    return hosts_ports


def get_consts_values():
    """Print out all constants"""
    message = ["-" * 40]
    message.append(f"SENSOR_ID = {SENSOR_ID}")
    message.append(f"DHT11_PIN = {DHT11_PIN}")
    message.append(f"CONVERT_TEMP_TO_F = {CONVERT_TEMP_TO_F}")
    message.append(f"SAMPLE_SIZE = {SAMPLE_SIZE}")
    message.append(f"LOG_IF_CHANGED_BY = {LOG_IF_CHANGED_BY}")
    message.append(f"LOG_IF_HUMIDITY_CHANGED = {LOG_IF_HUMIDITY_CHANGED}")
    message.append(f"LOG_IF_TEMPERATURE_CHANGED = {LOG_IF_TEMPERATURE_CHANGED}")
    message.append(f"CSV_OUT_FILE_NAME = {CSV_OUT_FILE_NAME}")
    message.append(f"IS_BUCKET_NAME = {IS_BUCKET_NAME}")
    message.append(
        f"IS_BUCKET_KEY = {''.join([IS_BUCKET_KEY[:3], '********', IS_BUCKET_KEY[-1:]]) if IS_BUCKET_KEY else ''}"
    )
    message.append(
        f"IS_ACCESS_KEY = {''.join([IS_ACCESS_KEY[:3], '******************************', IS_ACCESS_KEY[-3:]]) if IS_ACCESS_KEY else ''}"
    )
    message.append(f"STREAM_TO_INITIAL_STATE = {STREAM_TO_INITIAL_STATE}")
    message.append(f"LOGSTASH_HOSTS = {LOGSTASH_HOSTS}")
    message.append("-" * 40)
    return message


def c2f(celsius):
    """Convert temperature degree from C to F"""
    return (celsius * 9 / 5) + 32


def read_sensor(sensor):
    """Reading value from sensor"""
    sample_total_temperature = 0.0
    sample_total_humidity = 0.0
    for _ in range(SAMPLE_SIZE):
        time.sleep(1)
        result = sensor.read()
        while not result.is_valid():
            result = sensor.read()
        sample_total_temperature += result.temperature
        sample_total_humidity += result.humidity
    temperature = sample_total_temperature / SAMPLE_SIZE
    humidity = sample_total_humidity / SAMPLE_SIZE
    return humidity, temperature


def stream_to_initialstate(temperature, humidity):
    """Stream the temperature and humidity values to Initial State bucket"""
    if STREAM_TO_INITIAL_STATE:
        streamer = Streamer(
            bucket_name=IS_BUCKET_NAME,
            bucket_key=IS_BUCKET_KEY,
            access_key=IS_ACCESS_KEY,
        )
        streamer.log(f"{SENSOR_ID}_temperature", f"{temperature:.2f}")
        streamer.log(f"{SENSOR_ID}_humidity", f"{humidity:.2f}")
        streamer.flush()
        streamer.close()


def stream_to_logstash(humidity, temperature, ls_hosts):
    """Stream the temperature and humidity values to LogStash HTTP input bucket"""
    data = {
        "temperature": temperature,
        "humidity": humidity,
        "source": SENSOR_ID,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    for host, port in ls_hosts:
        try:
            url = f"http://{host}:{port}"
            requests.post(url, json=data, timeout=2.50)
            break
        except requests.exceptions.RequestException as error_msg:
            print(
                f"Couldn't connect to Logstash host ({host}:{port}): {error_msg}"
            )
    else:
        print(
            f"Couldn't successfully connect to any Logstash host ({LOGSTASH_HOSTS})"
        )


def main():
    """
    The program main entry point to start reading data from sensor
    and stream to different services
    """
    print("Start Reading with the following configuration:")
    print("\n".join(get_consts_values()))
    if CSV_OUT_FILE_NAME:
        with open(CSV_OUT_FILE_NAME, "a", encoding="utf-8") as csv_file:
            csv_file.write("\n".join(get_consts_values()))
            csv_file.write("\n")
            csv_file.write("timestamp,temperature,humidity\n")

    sensor = dht11.DHT11(pin=DHT11_PIN)
    previous_temperature = -999.99
    previous_humidity = -999.99
    ls_hosts = parse_hosts(LOGSTASH_HOSTS)

    while True:
        humidity, temperature = read_sensor(sensor)

        if CONVERT_TEMP_TO_F:
            temperature = c2f(temperature)

        if not math.isclose(
            temperature, previous_temperature, abs_tol=LOG_IF_CHANGED_BY
        ) or (
            LOG_IF_HUMIDITY_CHANGED
            and not math.isclose(humidity, previous_humidity, abs_tol=LOG_IF_CHANGED_BY)
        ):
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            stream_to_logstash(humidity, temperature, ls_hosts)
            stream_to_initialstate(temperature, humidity)
            print(
                f"{now} {temperature:.2f}{'F' if CONVERT_TEMP_TO_F else 'C'} {humidity:.2f}%"
            )
            if CSV_OUT_FILE_NAME:
                with open(CSV_OUT_FILE_NAME, "a", encoding="utf-8") as csv_file:
                    csv_file.write(f"{now},{temperature:.2f},{humidity:.2f}\n")
            previous_temperature = temperature
            previous_humidity = humidity


if __name__ == "__main__":
    main()
