# RPi-IoT
A collection of RPi projects

## How to use this

### Setup the Raspberry Pi
Install the Raspbian OS.  Using the OS without the Desktop version appears to be more stable than the version with Desktop. Connect the DHT11 sensor `data` pin to the pin specified in the `DHT11_PIN` (24).  The `+` pin to 3.3v and `-` pin to a ground pin on the Raspberry Pi.


### Reading data 
1. `sudo apt-get update && sudo apt-get upgrade`
2. `sudo apt-get install -y git python3-pip screen`
3. `git clone https://github.com/htquach/RPi-IoT`
4. `cd RPi-IoT/`
5. `pip3 install -r requirements.txt`
6. `screen -S RPi-IoT python3 sensor_dht11.py`

### Stream data to InitialState
1. Login to https://initialstate.com
2. Create a new bucket
3. Create a `.env` file at the project root with the following key-value pairs:
   * IS_BUCKET_NAME=[the IS bucket name]
   * IS_BUCKET_KEY=[the IS bucket key]
   * IS_ACCESS_KEY=[the IS access key]

### Push data to a Logstash instance
1. Create a `.env` file at the project root with the following key-value pairs:
   * LOGSTASH_HOSTS="127.0.0.1:5000,127.0.0.2:5000"
      * The Logstash port will default to 8080 if none is provided

### Install sensor_dht11.py as a service
1. Copy the sensor_dht11 service file to the /etc/systemd/system directory
2. Run systemctl daemon-reload as root
3. Run systemctl start sensor_dht11.service as root
