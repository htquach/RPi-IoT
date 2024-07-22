# RPi-IoT
A collection of RPi projects

## Reading Data from a DHT11 Sensor

### Setup the Raspberry Pi
Install the Raspbian OS.  Using the OS without the Desktop version appears to be more stable than the version with Desktop. Connect the DHT11 sensor `data` pin to the pin specified in the `DHT11_PIN` (24).  The `+` pin to 3.3v and `-` pin to a ground pin on the Raspberry Pi.

### Configuration

Streaming data to Initial State or Logstash are option.  To enable either one, simply define their environment variables.  The `.env` file is supported by the `python-dotenv` module.

#### Stream data to InitialState
   * IS_BUCKET_NAME=[the IS bucket name]
   * IS_BUCKET_KEY=[the IS bucket key]
   * IS_ACCESS_KEY=[the IS access key]

#### Stream data to Logstash
   * LOGSTASH_HOSTS=[the list of LogStash hosts]
     
Example:  
`
LOGSTASH_HOSTS="127.0.0.1:8080,127.0.0.2:8080"
`

### Update OS and install tools

```sh
sudo apt-get update && sudo apt-get upgrade
sudo apt-get install -y git python3-pip screen
```

### Reading data
```sh
git clone https://github.com/htquach/RPi-IoT
cd RPi-IoT/
pip3 install -r requirements.txt -r requirements_raspi.txt
screen -S RPi-IoT python3 sensor_dht11.py
```

### Install sensor_dht11.py as a service

Run the following commands as root `sudo -i`

```sh
cp sensor_dht11.service /etc/systemd/system/
systemctl daemon-reload
systemctl start sensor_dht11.service
systemctl status sensor_dht11.service
systemctl enable sensor_dht11.service
```
