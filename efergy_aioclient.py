# coding=utf-8
#-------------------------------------------------------------------------------
# Name:        efergy_aioclient.py
# Purpose:     efergy engage api - asyncio
# Copyright:   (c) 2019 TK
# Licence:     MIT
#-------------------------------------------------------------------------------
import logging
logger = logging.getLogger('efergy')

import asyncio 
import aiohttp
from aiohttp.client_exceptions import (
    ClientConnectorCertificateError, 
    ClientConnectorError, 
    ServerTimeoutError, 
    ServerDisconnectedError,
    ClientConnectionError
)

import time
import json
import queue
import logging
from datetime import datetime as _dt
from datetime import timezone
from datetime import timedelta
from collections import defaultdict
from multiprocessing import Event
from apscheduler.triggers.cron import CronTrigger

from mixinQueue import mixinAioQueue as _mixinQueue
import defaults as _def

# ==================================================================================

class efergy_aioclient(_mixinQueue):
    EFERGY_JOB_DELAY = 1.0
    QUEUE_PUT_TIMEOUT = 0.2
    _lasttime = defaultdict(int)
    _cnt = defaultdict(int)
    _error = defaultdict(bool)
    _func = 'execute_efergy'
#-------------------------------------------------------------------------------
    def __init__(self, *,
        cfg,
        hostname,
        outqueues,
        loop,
        scheduler,
        nameservers
    ):
        super().__init__()

        if not cfg:
           logger.error('cfg None')
           raise ValueError('cfg cannot be None')

        self._name = cfg.get('name', _def.EFERGY_NAME)
        logger.debug(f'{self._name} enter')        

        self._cfg = cfg

        self._outqueues = outqueues
        self._queue_maxsize = cfg.get('queue_maxsize', _def.EFERGY_QUEUE_MAXSIZE)

        self._loop = loop
        self._stop_event = asyncio.Event()
        self._nameservers = nameservers
        self._scheduler = scheduler
        self._schedule(scheduler=scheduler)
        self._hostname = hostname
        self._session = self._aiohttp_session()

        logger.debug(f'{self._name} exit')

#-------------------------------------------------------------------------------
    def _aiohttp_session(self):
        try:
            l_resolver = aiohttp.resolver.AsyncResolver(
                loop = self._loop,
                nameservers=self._nameservers
            ) if self._nameservers else None
            l_connector = aiohttp.TCPConnector(
                limit=10, 
                limit_per_host=0, 
                use_dns_cache=True,
                ttl_dns_cache=180, 
                resolver=l_resolver
            )
            l_timeout = self._cfg.get('timeout', _def.EFERGY_TIMEOUT)
            l_session = aiohttp.ClientSession(
                loop = self._loop,
                timeout = aiohttp.ClientTimeout(connect=l_timeout, total=l_timeout),
                connector = l_connector
            )
            return l_session
        except:
            # logger.exception('*** exception')
            return None

#-------------------------------------------------------------------------------
    def shutdown(self):
        logger.warning(f'{self._name} enter')
        self._stop_event.set()

#-------------------------------------------------------------------------------
    def _schedule(self, *, scheduler):
        logger.info(f'{self._name}')

        try:
            l_efergy = self._cfg
            l_tokens = l_efergy.get('TOKENS', None)
            l_schedules = l_efergy.get('SCHEDULE', None)

            l_cnt = 1
            for l_token in l_tokens:
                for l_schedule in l_schedules:
                    l_url = self._make_url(
                        url=l_efergy.get('url', _def.EFERGY_URL),
                        token=l_token.get('token', None),
                        func=l_schedule.get('func', None)
                    )
                    if l_url:
                        l_loc = l_token.get('location', None)
                        l_series = l_schedule.get('series', None)
                        l_cron = l_schedule.get('cron', None)
                        if l_loc and l_series and l_cron:
                            l_jobid = f'{self._name}_{l_loc}_{l_series}_{l_cnt}'
                            self._error[l_jobid] = False
                            scheduler.add_job(
                                self._do_job, 
                                CronTrigger.from_crontab(str(l_cron)), 
                                kwargs = {
                                    'location': l_loc, 
                                    'series': l_series, 
                                    'url': l_efergy.get('url', _def.EFERGY_URL), 
                                    'token': l_token.get('token', None), 
                                    'func': l_schedule.get('func', None),
                                    'jobid': l_jobid
                                }, 
                                id = l_jobid,
                                replace_existing = True,
                                max_instances = 1,
                                coalesce = True,
                                next_run_time = _dt.now() +timedelta(seconds=(self.EFERGY_JOB_DELAY*l_cnt))
                            )
                            l_cnt += 1
                            logger.info(f'{self._name} {l_jobid} job added')
                        else:
                            logger.error(f'{self._name} invalid configuration location:{l_loc} series:{l_series} cron:{l_cron}')
                    else:
                        logger.error('{0} invalid configuration url:{1} token:{2} func:{3}'.format(self._name,
                            l_efergy.get('url', _def.EFERGY_URL),l_token.get('token', None),l_schedule.get('func', None)))
        except:
            logger.exception(f'*** {self._name} exception')

#-------------------------------------------------------------------------------
    async def run(self):
        logger.info(f'{self._name} enter')
        # self.start_event.set()

        try:
            await self._stop_event.wait()
        except asyncio.CancelledError:
            logger.warning(f'{self._name} CancelledError')

        await self._session.close()
        logger.warning(f'{self._name} exit')
        return True

#-------------------------------------------------------------------------------
    def _make_url(self, *, url, token, func) -> str:
        if not url or not token or not func:
            return None
        return str(url+func+'?token='+token)

#-------------------------------------------------------------------------------
    async def _do_job(self, *, jobid, location, series, url, token, func):
        logger.debug(f'{self._name} {jobid} lasttime:{self._lasttime} cnt:{self._cnt} error:{self._error}')

        l_jsondata = None
        if self._session:
            l_url = self._make_url(url=url, token=token, func=func)
            try:
                l_jsondata = await self._get_json(jobid=jobid, session=self._session, url=l_url)
            except asyncio.CancelledError:
                logger.warning(f'{self._name} {jobid} CancelledError')

            if l_jsondata:
                await self._handle_data(jobid=jobid, location=location, series=series, token=token, jsondata=l_jsondata)
                if self._error[jobid]:
                    logger.info(f'{self._name} {jobid} get_json succesful')
                    self._error[jobid] = False
            else:
                logger.error(f'{self._name} {jobid} get_json failed')
                self._lasttime[jobid] = 0 # next time store all to the influx
                self._error[jobid] = True
        else:
            logger.error(f'{self._name} {jobid} session:{self._session}')

#-------------------------------------------------------------------------------
    async def _get(self, *, jobid, session, url ) -> str:
        logger.debug(f'{self._name} {jobid} url:{url}')

        try:
            async with session.get(url) as l_resp:
                if l_resp.status == 200:
                    return await l_resp.text()
        except asyncio.CancelledError:
            logger.warning(f'{self._name} {jobid} CancelledError')
        except asyncio.TimeoutError:
            logger.error(f'{self._name} {jobid} TimeoutError')
        except ClientConnectorCertificateError:
            logger.critical(f'{self._name} {jobid} ClientConnectorCertificateError. set ssl_verify: false or get authentic ssl certificate')
        except ClientConnectorError:
            logger.error(f'{self._name} {jobid} ClientConnectorError')
        except ServerTimeoutError:
            logger.error(f'{self._name} {jobid} ServerTimeoutError')
        except ServerDisconnectedError:
            logger.error(f'{self._name} {jobid} ServerDisconnectedError')
        except ClientConnectionError:
            logger.exception(f'{self._name} {jobid} ClientConnectionError')
        except:
            logger.error(f'{self._name} {jobid} failed url:{url}')
            logger.exception(f'*** {self._name} {jobid} exception')
        return None

#-------------------------------------------------------------------------------
    async def _get_json(self, *, jobid, session, url) -> dict:
        logger.debug(f'{self._name} {jobid} url:{url}')

        try:
            l_s = time.perf_counter_ns()
            l_resp = await self._get(jobid=jobid, session=session, url=url)
            if l_resp:
                l_jsondata = json.loads(l_resp)
                l_e = time.perf_counter_ns()
                # logger.debug(f'{self._name} url:{url} elapsed:{(l_e-l_s)/1000000:.0f}ms json:{l_jsondata}')
                # check json status
                try:
                    if l_jsondata['status'] == 'ok':
                        return l_jsondata
                    else:        
                        logger.warning('{0} {1} json status:{2}'.format(self._name, jobid, l_jsondata['status']))
                except:
                    logger.warning(f'{self._name} {jobid} json status does not exist')
        except asyncio.CancelledError:
            logger.warning(f'{self._name} {jobid} CancelledError')
        except:
            logger.exception(f'*** {self._name} {jobid} exception')            
        
        return None

#-------------------------------------------------------------------------------
    def _update_cnt(self, *, jobid) -> int:
        logger.debug(f'cnt:{self._cnt}')

        try:
            l_cnt = self._cnt[jobid]
        except:
            l_cnt = 0
        self._cnt[jobid] = (l_cnt + 1)
        return l_cnt

#-------------------------------------------------------------------------------
    def _reduce_json(self, *, jobid, location, series, token, jsondata) -> list:
        logger.debug(f'{self._name} {jobid} lasttime:{self._lasttime}')
        l_s = time.perf_counter_ns()

        try:
            l_lasttime = self._lasttime[jobid]
        except:
            self._lasttime[jobid] = 0
            l_lasttime = int(0)

        if 'data' not in jsondata:
            return None

        l_jsonlist = []
        for l_time, l_values in jsondata['data'].items():
            l_ts = int(l_time)
            # l_utc = _dt.utcfromtimestamp(int(l_ts/1000)).replace(tzinfo=timezone.utc).strftime(_def.EFERGY_TIMEFMT)
            # print(f'ts:{l_ts} utc:{l_utc}')

            l_add = True
            l_fields = {}
            if l_ts > l_lasttime:
                if len(l_values) >= 2:
                    try:
                        if 'undef' not in str(l_values[0]):
                            l_fields['consumption'] = float(l_values[0])
                        else:
                            logger.debug(f'{self._name} {jobid} consumption undef (2) time:{l_time} values:{l_values}')
                            l_add = False
                    except:
                        pass
                    try:
                        if 'undef' not in str(l_values[1]):
                            l_fields['prev24'] = float(l_values[1])
                        else:
                            logger.debug(f'{self._name} {jobid} prev24 undef (2) time:{l_time} values:{l_values}')
                    except:
                        pass
                elif len(l_values) == 1:
                    try:
                        if 'undef' not in str(l_values[0]):
                            l_fields['consumption'] = float(l_values[0])
                        else:
                            logger.debug(f'{self._name} {jobid} consumption undef (1) time:{l_time} values:{l_values}')
                            l_add = False
                    except:
                        pass
                else:
                    logger.debug(f'{self._name} {jobid} no values time:{l_time}')
                    l_add = False

                if l_add:
                    l_jsonlist.append(
                        {
                            'measurement': series,
                            'fields': l_fields,
                            'tags': {
                                'loc': location,
                                'hostname': self._hostname
                            },
                            'time': _dt.utcfromtimestamp(int(l_ts/1000)).replace(tzinfo=timezone.utc).strftime(_def.EFERGY_TIMEFMT)
                        }
                    )
                    if l_ts > self._lasttime[jobid]:
                        self._lasttime[jobid] = l_ts
            else:
                pass

        if not len(l_jsonlist):
            logger.debug(f'{self._name} {jobid} empty jsonlist')
            return None

        l_e = time.perf_counter_ns()
        logger.debug(f'{self._name} {jobid} elapsed:{(l_e-l_s)} jsonlist:{l_jsonlist}')
        return l_jsonlist

#-------------------------------------------------------------------------------
    async def _handle_data(self, *, jobid, location, series, token, jsondata):
        # logger.debug(f'{self._name} {jobid}')

        l_jsonlist = self._reduce_json(jobid=jobid, location=location, series=series, token=token, jsondata=jsondata)
        # print(f'type:{type(l_jsondata)} data:{l_jsonlist}')

        if l_jsonlist:
            l_data = {
                'jobid': jobid,
                'func': self._func,
                'json': l_jsonlist
            }
            await self._queue_output(jobid=jobid, data=l_data)
            self._update_cnt(jobid=jobid)

#-------------------------------------------------------------------------------
    async def _queue_output(self, *, jobid, data):
        # self._logger.debug(f'{self._name} {jobid} data: {data}')

        if self._outqueues:
            if isinstance(self._outqueues, dict):
                for l_qname, l_queue in self._outqueues.items():
                    if not await self.queue_put(outqueue=l_queue, data=data):
                        return False
                return True
            else:
                return await self.queue_put(outqueue=self._outqueues, data=data)
        return False

