# EFERGY GATEWAY 3.3.8 (191128)
This software can be used to collect measurement data from Efergy engage API and store them to the InfluxDB / send to MQTT broker

## MAIN FUNCTIONALITIES
- Store Efergy engage measurements to the Influx (multiple) databases
- Publish Efergy engage measurements MQTT (multiple) brokers
- Home assistant Auto Discovery (on restart and/or on request)

## COMMAND LINE PARAMETERS
### efergygw.py [-h] [-c <config>] [-l <logconfig>]
| optional argument | long format | parameter                 |
|:------------------|:------------|:--------------------------|
| -h                | --help      |                           |
| -c                | --config    | configuration file        |
| -l                | --logconfig | logger configuration file |


# LICENCE
MIT License is used for this software.
