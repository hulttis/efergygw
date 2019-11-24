# coding=utf-8
#-------------------------------------------------------------------------------
# Name:        defaults.py
# Purpose:     default values
# Copyright:   (c) 2019 TK
# Licence:     MIT
#-------------------------------------------------------------------------------
from multiprocessing import cpu_count
import os
import sys

PROGRAM_NAME = 'Efergy Gateway'
LONG_PROGRAM_NAME = 'Efergy InfluxDB/MQTT Gateway'
PROGRAM_PY = 'efergygw.py'
VERSION = '3.3.7 (191123)'
PROGRAM_COPYRIGHT = '(c)TK 2019'

CFGFILE = 'efergygw.json'
if not sys.platform.startswith('linux') or os.environ.get('CI') == 'True': 
    LOG_CFGFILE = 'efergygw_logging_win.json'
else:
    LOG_CFGFILE = 'efergygw_logging.json'
print (f'### DEFAULT LOG CONFIG FILE:{LOG_CFGFILE}')

SEPARATOR_LENGTH = 64

# COMMON
COMMON_START_DELAY = 2.0
COMMON_DOCKER_ENV = False
COMMON_SCHEDULER_MAXINSTANCES = 10
COMMON_NAMESERVERS = None
COMMON_HOSTNAME = ''
# INFLUX
INFLUX_ENABLE = True
INFLUX_NAME = 'influx_default'
INFLUX_LOAD_BALANCER = False
INFLUX_WORKERS = cpu_count()
INFLUX_SUPERVISION_INTERVAL = 20
INFLUX_HOST = 'localhost'
INFLUX_PORT = 8086
INFLUX_SSL = False 
INFLUX_SSL_VERIFY = True 
INFLUX_USERNAME = ''
INFLUX_PASSWORD = ''
INFLUX_DATABASE = '_default' 
INFLUX_TIMEOUT = 2.0 
INFLUX_RETRIES = 2
INFLUX_POLICY_NAME = '_default'
INFLUX_POLICY_DURATION = '365d'
INFLUX_POLICY_REPLICATION = 1
INFLUX_POLICY_DEFAULT = False
INFLUX_POLICY_ALTER = False
INFLUX_POLICY = {
    "name": INFLUX_POLICY_NAME,
    "duration": INFLUX_POLICY_DURATION,
    "replication": INFLUX_POLICY_REPLICATION,
    "default": INFLUX_POLICY_DEFAULT,
    "alter": INFLUX_POLICY_ALTER
    }
INFLUX_QUEUE_SIZE = 100

# MQTT
MQTT_ENABLE = True
MQTT_DEBUG = False
MQTT_TOPIC = 'test'
# MQTT_ADTOPIC = None
# MQTT_ANNTOPIC = None
MQTT_NAME = ''
MQTT_HOST = 'localhost'
MQTT_PORT = 1883
MQTT_SSLPORT = 8883
MQTT_SSL = False
MQTT_SSL_INSECURE = False
MQTT_CERT_VERIFY = True
MQTT_KEEPALIVE = 15
MQTT_CLIENT_ID = 'mqtt'
# MQTT_CAFILE = ''
# MQTT_CAPATH = ''
# MQTT_CADATA = ''
MQTT_LWT= False
MQTT_LWTTOPIC = 'lwt'
MQTT_LWTOFFLINE = 'offline'
MQTT_LWTONLINE = 'online'
MQTT_LWTRETAIN = False
MQTT_LWTQOS = 1
MQTT_LWTPERIOD = 60
MQTT_USERNAME = ''
MQTT_PASSWORD = ''
MQTT_QOS = 1
MQTT_RETAIN = False
MQTT_CLEAN_SESSION = False
MQTT_ADQOS = 1
MQTT_ADRETAIN = False
MQTT_ANNQOS = 1
MQTT_SUPERVISION_INTERVAL = 10
MQTT_QUEUE_SIZE = 100
MQTT_ADFIELDS = {
    "day": {
        "consumption": {
        "unit_of_meas": "kW",
        "dev_cla": "power",
        "val_tpl": "{{ value_json.consumption | float | round(2) }}"
        }
    },
    "week": {
        "consumption": {
        "unit_of_meas": "kWh",
        "dev_cla": "power",
        "val_tpl": "{{ value_json.consumption | float | round(2) }}"
        }
    },
    "month": {
        "consumption": {
        "unit_of_meas": "kWh",
        "dev_cla": "power",
        "val_tpl": "{{ value_json.consumption | float | round(2) }}"
        }
    },
    "year": {
        "consumption": {
        "unit_of_meas": "kWh",
        "dev_cla": "power",
        "val_tpl": "{{ value_json.consumption | float | round(2) }}"
        }
    }
} 


#EFERGY
EFERGY_NAME = "efergy" 
EFERGY_URL = "https://engage.efergy.com/mobile_proxy/"
EFERGY_TIMEOUT = 10
EFERGY_QUEUE_MAXSIZE = 100
EFERGY_TIMEFMT = '%Y-%m-%dT%H:%M:%S.%f%z'
