# coding=utf-8
# !/usr/bin/python3
# Name:         Efergy InfluxDB / MQTT gateway
# Copyright:    (c) 2019 TK
# Licence:      MIT
#
# API           http://napi.hbcontent.com/document/index.php
# Required:     influxdb                                // pipenv install influxdb
#               apscheduler                             // pipenv install apscheduler
#               aiohttp                                 // pipenv install aiohttp
#               aiomqtt                                 // pipenv install aiomqtt
#               asyncio
# dev:          pylint                                  // pipenv install -d pylint
# -------------------------------------------------------------------------------

import defaults as _def

import logging
_LOG_CFGFILE = _def.LOG_CFGFILE
from logger_config import logger_config
logger = None 

_PROGRAM_NAME = _def.LONG_PROGRAM_NAME
_PROGRAM_PY = _def.PROGRAM_PY
_VERSION = _def.VERSION
_CFGFILE = _def.CFGFILE

import os
import sys
import time
import signal
import argparse
import platform 
import traceback
from datetime import datetime as _dt
from datetime import timedelta
from multiprocessing import cpu_count
from apscheduler.schedulers.asyncio import AsyncIOScheduler as _scheduler
from apscheduler.events import EVENT_ALL

import asyncio
import functools
from contextlib import suppress

from config import config_reader as _config
from efergy_aioclient import efergy_aioclient as _efergy
from efergy_influx import efergy_influx as _influx
from efergy_mqtt import efergy_mqtt as _mqtt
from efergy_dataclasses import procItem, procDict
from mixinSchedulerEvent import mixinSchedulerEvent

# ==============================================================================
class main_class(mixinSchedulerEvent):
    SLEEP_TIME = 1.0
    _run = True
#-------------------------------------------------------------------------------
    def __init__(self, *,
        config_file = _CFGFILE,
        logconfig_file = _LOG_CFGFILE
    ):
        super().__init__()

        global logger
        logger_config(logconfig_file)
        logger = logging.getLogger('efergygw')

        # read config
        try:
            self._cfgh = _config(configfile=config_file)
        except Exception as l_e:
            print('*** exception:{0} traceback:{1}'.format(l_e, traceback.format_exc()))
            print('*** failed to read configuration file: {0:s} - terminating'.format(config_file))
            sys.exit()

        self._cfgh.print()
        # sys.exit()

        # setup logger
        logger.info(f'{_PROGRAM_NAME} {_VERSION}')
        logger.info('### logger ready')

        # set class variables
        self._procs = procDict()  
        l_common = self._cfgh.get_cfg(section='COMMON')
        if l_common:
            l_maxinstances = l_common.get('scheduler_max_instances', _def.COMMON_SCHEDULER_MAXINSTANCES)
        else:
            l_maxinstances = _def.COMMON_SCHEDULER_MAXINSTANCES
        self._scheduler = _scheduler(
            max_instances = l_maxinstances
        )
        self._scheduler.add_listener(self._job_event, mask=EVENT_ALL)
        self._scheduler.add_job(
            self._ticktak,
            'interval',
            seconds = 1,
            id = str('_ticktak_'),
            replace_existing = True,
            max_instances = 1,
            coalesce = True,
            next_run_time = _dt.now()+timedelta(seconds=5)
        )
        self._loop = None

#-------------------------------------------------------------------------------
    def _ticktak(self):
        pass

#-------------------------------------------------------------------------------
    def main_func(self):
        logger.info(f'started: {_dt.now()}')

        self._scheduler.start()
        self._loop = asyncio.get_event_loop()
        try:
            for l_signame in {'SIGINT', 'SIGTERM'}:
                self._loop.add_signal_handler(
                    getattr(signal, l_signame), 
                    functools.partial(self._stop, l_signame)
                )
            logger.info('signals registered')
        except:
            logger.warning('registering signals failed')
            pass

        l_influx = self._start_influx()
        l_mqtt = self._start_mqtt()
        if not l_influx and not l_mqtt:
            self._run = False
            logger.critical(f'Starting INFLUX and MQTT failed. Check configuration !')
        self._run = self._start_efergy()

        if self._run:
            try:
                self._loop.run_forever()
            except (KeyboardInterrupt, SystemExit):
                logger.warning('KeyboardInterrupt/SystemExit')
            finally:
                self._scheduler.shutdown()
                self._shutdown()
                self._loop.stop()
                self._loop.close()

        logger.warning(f'finished:{str(_dt.now())}')

#-------------------------------------------------------------------------------
    def _stop(self, signame):
        logger.warning(f'enter {signame}')
        raise KeyboardInterrupt

#-------------------------------------------------------------------------------
    def _start_influx(self):
        logger.debug('enter')

        if not self._run:
            return False

        l_res = True
        l_common = self._cfgh.get_cfg(section='COMMON')
        l_influxs = self._cfgh.get_cfg(section='INFLUX')
        if l_influxs:
            for l_influx in l_influxs:
                if l_influx.get('enable', _def.INFLUX_ENABLE):
                    try:
                        l_inqueue = asyncio.Queue(maxsize=l_influx.get('queue_size', _def.INFLUX_QUEUE_SIZE))
                        l_proc = _influx(
                            cfg = l_influx,
                            hostname = l_common.get('hostname', _def.COMMON_HOSTNAME),
                            inqueue = l_inqueue,
                            loop = self._loop,
                            scheduler = self._scheduler,
                            nameservers = l_common.get('nameservers', _def.COMMON_NAMESERVERS)
                        )
                        l_task = self._loop.create_task(l_proc.run())
                        self._procs.add(l_influx.get('name', _def.INFLUX_NAME), procItem(proc=l_proc, queue=l_inqueue, task=l_task))
                        logger.info('Task:{0:s} created'.format(l_influx.get('name', _def.INFLUX_NAME)))
                        logger.debug('Proc:{0} Task:{1}'.format(l_proc, l_task))
                    except Exception:
                        logger.exception('failed to add task:{0:s}'.format(l_influx.get('name', _def.INFLUX_NAME)))
                        l_res = False
                else:
                    logger.warning('INFLUX:{0} disabled'.format(l_influx.get('name', _def.INFLUX_NAME)))
        else:
            logger.error('INFLUX configuration missing')
            l_res = False

        return l_res

#-------------------------------------------------------------------------------
    def _start_mqtt(self):
        logger.debug('enter')

        if not self._run:
            return False

        l_res = True
        l_common = self._cfgh.get_cfg(section='COMMON')
        l_mqtts = self._cfgh.get_cfg(section='MQTT')
        if l_mqtts:
            for l_mqtt in l_mqtts:
                if l_mqtt.get('enable', _def.MQTT_ENABLE):
                    try:
                        l_inqueue = asyncio.Queue(maxsize=l_mqtt.get('queue_size', _def.MQTT_QUEUE_SIZE))
                        l_proc = _mqtt(
                            cfg = l_mqtt,
                            hostname = l_common.get('hostname', _def.COMMON_HOSTNAME),
                            inqueue = l_inqueue,
                            loop = self._loop,
                            scheduler = self._scheduler,
                            nameservers = l_common.get('nameservers', _def.COMMON_NAMESERVERS)
                        )
                        l_task = self._loop.create_task(l_proc.run())
                        self._procs.add(l_mqtt.get('name', _def.MQTT_NAME), procItem(proc=l_proc, queue=l_inqueue, task=l_task))
                        logger.info('Task:{0:s} created'.format(l_mqtt.get('name', _def.MQTT_NAME)))
                        logger.debug('Proc:{0} Task:{1}'.format(l_proc, l_task))
                    except Exception:
                        logger.exception('failed to add task:{0:s}'.format(l_mqtt.get('name', _def.MQTT_NAME)))
                        l_res = False
                else:
                    logger.warning('MQTT:{0} disabled'.format(l_mqtt.get('name', _def.MQTT_NAME)))
        else:
            logger.error('MQTT configuration missing')
            l_res = False

        return l_res

#-------------------------------------------------------------------------------
    def _start_efergy(self):
        logger.debug('enter')

        if not self._run:
            return False

        l_res = True
        l_common = self._cfgh.get_cfg(section='COMMON')
        l_efergys = self._cfgh.get_cfg(section='EFERGY')
        if l_efergys:
            l_instance = 0
            for l_cfg in l_efergys:
                try:
                    l_queues = self._find_queue(queuenames=l_cfg.get('OUTPUT', None))
                    logger.debug(f'queues {l_queues}')
                    l_proc = _efergy(
                        cfg = l_cfg,
                        hostname = l_common.get('hostname', _def.COMMON_HOSTNAME),
                        outqueues = l_queues,
                        loop = self._loop,
                        scheduler = self._scheduler,
                        nameservers = l_common.get('nameservers', _def.COMMON_NAMESERVERS)
                    )
                    l_task = self._loop.create_task(l_proc.run())
                    self._procs.add(l_cfg.get('name', _def.EFERGY_NAME), procItem(proc=l_proc, queue=None, task=l_task))
                    logger.info('Task:{0:s} created'.format(l_cfg.get('name', _def.EFERGY_NAME)))
                    logger.debug('Proc:{0} Task:{1}'.format(l_proc, l_task))
                except (Exception) as l_e:
                    logger.exception('failed to add task:{0:s}'.format(l_cfg.get('name', _def.EFERGY_NAME)))
                    l_res = False
        else:
            logger.error('EFERGY configuration missing')
            l_res = False

        return l_res

#-------------------------------------------------------------------------------
    def _shutdown(self):
        logger.debug(f'procs:{self._procs}')

        if self._procs:
            for l_key, l_proc in self._procs.procs.items():
                l_task = l_proc.task
                if l_task and not l_task.cancelled():
                    logger.warning(f'shutdown task:{l_key}')
                    if l_proc.proc and hasattr(l_proc.proc, 'shutdown'):
                        l_proc.proc.shutdown()
                    l_task.cancel()
                    with suppress(asyncio.CancelledError):
                        self._loop.run_until_complete(l_task)                    
        else:
            logger.warning('no procs')

# ------------------------------------------------------------------------------
    def _find_queue(self, *, queuenames=None):
        if not queuenames:
            return None

        if isinstance(queuenames, list):
            l_queues = {}
            for l_queuename in queuenames:
                l_proc = self._procs.get(l_queuename)
                if l_proc:
                    l_queues[l_queuename] = l_proc.queue
                else:
                    logger.error(f'queue {l_queuename} cannot be found')
            if len(l_queues):
                return l_queues
        else:
            l_proc = self._procs.get(queuenames)
            if l_proc:
                return l_proc.queue
        return None

# ------------------------------------------------------------------------------
if __name__ == '__main__':

    l_parser = argparse.ArgumentParser(prog=_PROGRAM_PY, description=_PROGRAM_NAME)
    l_parser.add_argument('-c', '--config',  help='<config> ..... configuration file', default=_CFGFILE, required=False,
        type=str, dest='cfgfile', metavar='<config>')
    l_parser.add_argument('-l', '--logconfig',  help='<logconfig> ..... logger configuration file', default=_LOG_CFGFILE, required=False,
        type=str, dest='logcfgfile', metavar='<logconfig>')
    l_parser.add_argument('-t', '--test',    help='<test> ....... test mode', action='store_true', dest='testmode')
    l_args = l_parser.parse_args()

    print('')
    print ('--- {0:s} STARTED {1:s} ---'.format(_PROGRAM_NAME.upper(), str(_dt.now())))
    print('')
    print('version:                {0}'.format(_VERSION))
    print('python:                 {0}'.format(platform.python_version()))
    print('cpu count:              {0}'.format(cpu_count()))
    print('parent pid:             {0}'.format((os.getpid())))

    print('')
    print('COMMANDLINE ARGUMENTS')
    print('-'*21)
    print('configuration file:     {0}'.format(l_args.cfgfile))
    print('logger config:          {0}'.format(l_args.logcfgfile))
    print('test mode:              {0}'.format(l_args.testmode))

    l_main = main_class(
        config_file = l_args.cfgfile,
        logconfig_file = l_args.logcfgfile
    )
    try:
        if l_args.testmode:
            import profile
            profile.run('l_main.main_func()', sort=1)
        else:
            sys.exit(l_main.main_func())
        
    except (Exception) as l_e:
        print('*** {0} traceback:{1}'.format(l_e, traceback.format_exc()))

# ==============================================================================
