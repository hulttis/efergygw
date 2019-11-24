# EFERGY GATEWAY 3.3.7 (191123)
This software can be used to collect measurement data from Efergy engage API and store them to the InfluxDB / send to MQTT broker

## MAIN FUNCTIONALITIES
- Store Efergy engage measurements to the Influx (multiple) databases
- Publish Efergy engage measurements MQTT (multiple) brokers
- Home assistant Auto Discovery (on restart and/or on request)
## CONFIGURATION
### EFERGYGW
- file: efergygw.json
- see `efergygw.json` for example configuration

| `COMMON`: [object]    | optional                                                         |
|:----------------------|:-----------------------------------------------------------------|
| `nameservers`: [list] | list of nameservers, if not given system nameserver will be used |
| `hostname`: [string]  | hostname, if not given will be detected automatically            |


| `INFLUX`: [list]                              | optional                                            |
|-----------------------------------------------|-----------------------------------------------------|
| `enable`: [boolean]                           | enable/disable InfluxDB instance (default: true)    |
| `name`: [string]                              | **unique** name of the InfluxDB instance (required) |
| `host`: [string]                              | InfluxDB host (required)                            |
| `port`: [integer]                             | InfluxDB port (default: 8086)                       |
| `ssl`: [boolean]                              | use ssl (default: false)                            |
| `ssl_verify`: [boolean]                       | verify ssl certificate (default: true)              |
| `database`: [string]                          | name of the InfluxDB database (required)            |
| `username`: [string]                          | InfluxDB username                                   |
| `password`: [string]                          | InfluxDB password                                   |
| **`POLICY`**: [object]                        |                                                     |
| &nbsp;&nbsp;&nbsp;`name`: [string]            | policy name (default: _default)                     |
| &nbsp;&nbsp;&nbsp;`   duration`: [string]     | policy duration (default: 0s - forever)             |
| &nbsp;&nbsp;&nbsp;`   replication`: [integer] | policy replication (default: 1)                     |
| &nbsp;&nbsp;&nbsp;`   default`: [boolean]     | set as default policy (default: false)              |
| &nbsp;&nbsp;&nbsp;`   alter`: [boolean]       | alter if policy exists (default: false)             |

| `MQTT`: [list]                                               | optional                                                                      |
|:-------------------------------------------------------------|:------------------------------------------------------------------------------|
| `enable`: [boolean]                                          | enable/disable MQTT instance (default: true)                                  |
| `name`: [string]                                             | **unique** name of the MQTT instance                                          |
| `client_id`: [string]                                        | **unique** client-id (default: `hostname-x`)                                  |
| `uri`                                                        | mqtt url (uri or host/port/username/password/ssl are needed                   |
| `host`: [string]                                             | mqtt host (required)                                                          |
| `port`: [integer]                                            | mqtt port (default: 1883 (for ssl 8883))                                      |
| `ssl`: [boolean]                                             | secure mqtt (default: False)                                                  |
| `ssl_insecure`: [boolean]                                    | allow ssl without verifying hostname in the certificate (default: False)      |
| `clean_session`: [boolean]                                   | clean session (default: False)                                                |
| `cert_verify`: [boolean]                                     | verify ssl certificates (default: True)                                       |
| `cafile`: [string]                                           | certificate file (full path)                                                  |
| `topic`: [string]                                            | mqtt publish topic                                                            |
| `qos`: [integer]                                             | quality of service (default: 1)                                               |
| `retain`: [boolean]                                          | mqtt publish retain (default: false)                                          |
| `adtopic`: [string]                                          | home assistant autodiscovery topic (default: None - no autodiscovery)         |
| `adretain`: [boolean]                                        | home assistant autodiscovery retain (default: false)                          |
| `anntopic`: [string]                                         | home assistant auto discovery announce topic (default: None - not subscribed) |
| `lwt`: [boolean]                                             | enable LWT (Last Will Testament (default: False)                              |
| `lwttopic`: [string]                                         | LWT topic (default: auto generated from client_id)                            |
|                                                              | format: `topic`/`client_id`/`lwt`                                             |
| `lwtqos`: [integer]                                          | LWT quality of service (default: 1)                                           |
| `lwtretain`: [boolean]                                       | LWT retain (default: False                                                    |
| `lwtperiod`: [integer]                                       | LWT update period in seconds (default: 60)                                    |
| `lwtonline`: [string]                                        | LWT online text (default: online)                                             |
| `lwtoffline`: [string ]                                      | LWT offline text (default: offline)                                           |
| `ADFIELDS`: [object]                                         | home assistant auto discovery fields (default: see efergygw.json)              |
| &nbsp;&nbsp;&nbsp;`<field name>`: [object]                   | name of the auto discovery field                                              |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`unit_of_meas`: [string] | unit of measurement                                                           |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`dev_cla`: [string]      | device class                                                                  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`val_tpl`: [string]      | value template                                                                |

| `EFERGY`: [object] | required                                                               |
|:-------------------|:-----------------------------------------------------------------------|
| `name`: [string]   | name of the efergy instance (default: ***efergy***)                    |
|                    | note: used also as InfluxDB measurement name                           |
| `url`              | url to efergy api (default: `https://engage.efergy.com/mobile_proxy/`) |
| `timeout`          | timeout (default: 10)                                                  |
| `OUTPUT`: [list]   | list of InfluxDB/MQTT output(s) (required)                             |
| `TOKENS`: [list]   | Efergy API tokens                                                      |
| `SCHEDULE`: [list] | Schedule to data collection from Efergy API                            |

### HOME ASSISTANT MQTT AUTO DISCOVERY
- efergygw sends auto discovery to the `adtopic` by default to the following fields: temperature, humidity, pressure and batteryVoltage
- efergygw subscribes mqtt topic defined in `anntopic` and expects mqtt payload to be `efergy`. auto discovery is sent to all found sensors during next update

### LOGGER
- see  `efergygw_logging.json` for example configuration 

## INSTALLATION
### REQUIREMENTS
- Linux (tested in Ubuntu server 18.04.03 and 2019-09-26-raspbian-buster-lite) or Windows (maybe also Mac OS). 
- at least python 3.7.x (recommended 3.8.0)
- at least pip3.7.x (recommended 3.8.0)
- virtualenv (`pip3.8 install --user virtualenv`) - if not installed
- git (`sudo apt -y install git`)
NOTE: Instructions are for Python 3.8

### DOCKER
- figure out yourself
- see `https://github.com/hulttis/efergygw-docker` for Dockerfile sample
  
### DOCKER-COMPOSE
- see `https://github.com/hulttis/efergygw-docker` for installation instructions

### LINUX SERVICE
- `sudo -i`
- create /app directory (`mkdir -p /app && cd /app`)
- create /var/log/efergygw directory (`mkdir -p /var/log/efergygw`) for logs
- clone git repository to /app directory (`git clone --single-branch https://github.com/hulttis/efergygw.git`)
- edit /app/efergygw/efergygw.json file (`nano /app/efergygw/efergygw.json`)
- create virtual environment (`cd /app/efergygw && python3.8 -m venv env`)
- activate virtual environment (`source env/bin/activate`)
- check python and pip (`which python && which pip && python -V && pip -V`)
- install requirements (`pip install -r requirements.txt`)
- deactivate virtual environment (`deactivate`)
- copy /app/efergygw/efergygw.service to /lib/systemd/system directory (`cp /app/efergygw/efergygw.service /lib/systemd/system/.`)
- reload daemons (`systemctl daemon-reload`)
- enable efergygw (`systemctl enable efergygw`)
- start efergygw (`systemctl start efergygw`)
- check efergygw status (`systemctl status efergygw`)
- check efergygw logs (`journalctl -u efergygw -b --no-pager`)

#### UPGRADE
- `sudo -i`
- stop efergygw (`systemctl stop efergygw`)
- `cd /app`
- copy config to safe location (`cp -v ./efergygw/efergygw.json . && cp -v ./efergygw/efergygw_logging.json .`)
- remove efergygw (`rm -fr ./efergygw`)
- clone git repository (`git clone --single-branch https://github.com/hulttis/efergygw.git`)
- copy old config back to efergygw (`cp -v *.json efergygw/.`)
- create virtual environment (`cd /app/efergygw && python3.8 -m venv env`)
- activate virtual environment (`source env/bin/activate`)
- install requirements (`pip install -r requirements.txt`)
- deactivate virtual environment (`deactivate`)
- empty logs (`rm -v /var/log/efergygw/*.log`)
- start efergygw (`systemctl start efergygw`)
- check efergygw status (`systemctl status efergygw`)
- check efergygw logs (`journalctl -u efergygw -b --no-pager`)
  
*or if you dare you can use do_upgrade_efergygw.sh script on your own risk*

## COMMAND LINE PARAMETERS
### efergygw.py [-h] [-c <config>] [-l <logconfig>]
| optional argument | long format | parameter                 |
|:------------------|:------------|:--------------------------|
| -h                | --help      |                           |
| -c                | --config    | configuration file        |
| -l                | --logconfig | logger configuration file |

# LICENCE
MIT License is used for this software.
