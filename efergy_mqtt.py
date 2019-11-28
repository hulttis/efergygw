# coding=utf-8
#-------------------------------------------------------------------------------
# Name:        efergy_mqtt.py
# Purpose:     efergy specific mqtt
# Copyright:   (c) 2019 TK
# Licence:     MIT
#-------------------------------------------------------------------------------
import logging
logger = logging.getLogger('mqtt')

import asyncio
from collections import defaultdict
from datetime import datetime as _dt
from datetime import timezone
import ciso8601

from mqtt_aioclient import mqtt_aioclient as _mqtt
import defaults as _def

# ==================================================================================

class efergy_mqtt(_mqtt):
    _adlock = asyncio.Lock()
#-------------------------------------------------------------------------------
    def __init__(self, *,
        cfg,
        hostname,
        inqueue,
        loop,
        scheduler,
        nameservers=None
    ):
        super().__init__(
            cfg=cfg,
            hostname=hostname,
            inqueue=inqueue,
            loop=loop,
            scheduler=scheduler,
            nameservers=nameservers
        )
        self._funcs['execute_efergy'] = self._execute_efergy
        # logger.debug(f'{self._name} funcs:{self._funcs}')

        self._adtopic = cfg.get('adtopic', None)
        self._adqos = cfg.get('adqos', _def.MQTT_ADQOS)
        self._adretain = cfg.get('adretain', _def.MQTT_ADRETAIN)
        self._adfields = cfg.get('ADFIELDS', _def.MQTT_ADFIELDS)
        self._anntopic = cfg.get('anntopic', None)
        self._annqos = cfg.get('annqos', _def.MQTT_ANNQOS)
        self._message_callback = self._efergy_message

        self._announce = defaultdict(dict)
        self._hostname = hostname

        logger.info(f'{self._name} done')

#-------------------------------------------------------------------------------
    async def _connect(self, *, cfg):
        logger.debug(f'{self._name} cfg:{cfg}')

        if await super()._connect(cfg=cfg):
            if self._anntopic:
                await self._subscribe(
                    topic=self._anntopic, 
                    qos=self._annqos
                )
            return True
        return False

#-------------------------------------------------------------------------------
    async def _disconnect(self):
        logger.debug(f'{self._name}')

        if self._client:
            if self._anntopic:
                await self._unsubscribe(topic=self._anntopic)   
            await super()._disconnect()

#-------------------------------------------------------------------------------
    def _set_announce(self, *, key):
        logger.debug(f'{self._name} addata:{self._announce}')
        try:
            l_rc = self._announce[key]
        except:
            l_rc = False
        self._announce[key] = True
        return l_rc

#-------------------------------------------------------------------------------
    async def _efergy_announce(self, *, item, topic):
        logger.debug(f'{self._name} type:{type(item)} item:{item}')
        l_ignore = ['prev24']

        if self._adtopic:
            try:
                l_tags = item['tags']
                l_meas = item['measurement']
                l_loc = l_tags['loc']
                l_name = l_loc + '-' + l_meas
                if not self._set_announce(key=l_name):
                    l_fields = item['fields']
                    l_dev = {
                        'ids': [l_name],
                        'name': 'Efergy ' + l_name,
                        'mdl': _def.PROGRAM_NAME,
                        'sw': _def.VERSION,
                        'mf': _def.PROGRAM_COPYRIGHT
                    }
                    logger.info(f'{self._name} auto discovery:{l_name}')
                    for l_key, _ in l_fields.items():
                        if l_key not in l_ignore:
                            l_adtopic = self._adtopic + '/' + l_name + '-' + l_key + '/config' 
                            await self._publish(topic=l_adtopic, payload=b'', retain=False)

                            l_admeas = self._adfields.get(l_meas, None)
                            if l_admeas:
                                l_adfields = l_admeas.get(l_key, None)
                                if l_adfields:
                                    l_payload = {
                                        'dev': l_dev,
                                        'name': l_name + ' ' + l_key,
                                        'stat_t': topic,
                                        'val_tpl': l_adfields.get('val_tpl', ''),
                                        'unique_id': l_name + '-' + l_key,
                                        'qos':  self._adqos,
                                        'unit_of_meas': l_adfields.get('unit_of_meas', ''),
                                        'dev_cla': l_adfields.get('dev_cla', '')
                                    }
                                    await self._publish(
                                        topic=l_adtopic, 
                                        payload=str(l_payload).replace('\'', '\"').encode(), 
                                        qos=self._adqos,
                                        retain=self._adretain
                                    )
            except:
                logger.exception(f'*** {self._name}')

#-------------------------------------------------------------------------------
    async def _efergy_message(self, *, message):
        logger.debug(f'{self._name}')

        if message:
            if isinstance(message.payload, bytes):
                l_payload = message.payload.decode()
            else:
                l_payload = message.payload
            logger.debug(f'{self._name} topic:{message.topic} payload:{l_payload}')
            if l_payload == 'efergy':
                logger.info(f'{self._name} announce received')
                self._announce.clear()

#-------------------------------------------------------------------------------
    async def _get_newest(self, *, item):
        logger.debug(f'{self._name} type:{type(item)} {item}')

        l_newest_item = None
        l_newest_ts = _dt(1970,1,1,tzinfo=timezone.utc)
        if isinstance(item, list):
            for l_item in item:

                l_time = l_item.get('time', None)
                if l_time:
                    l_ts = ciso8601.parse_datetime(l_time).replace(tzinfo=timezone.utc)
                    if l_ts > l_newest_ts:
                        l_newest_item = l_item
                        l_newest_ts = l_ts
        else:
            l_newest_item = item

        logger.debug(f'item: {l_newest_item}')
        return l_newest_item

#-------------------------------------------------------------------------------
    async def _execute_efergy(self, *, topic, item):
        logger.debug(f'{self._name} type:{type(item)}')
        if not item:
            logger.error(f'{self._name} topic:{topic} item: {item}')
            return

        try:
            l_jobid = item.get('jobid', None)
            l_item = await self._get_newest(item = item['json'])
            if l_item:
                l_topic = topic + '/' + l_item['tags']['loc'] + '/' + l_item['measurement']
                async with efergy_mqtt._adlock:
                    await self._efergy_announce(item=l_item, topic=l_topic)
                l_payload = None
                if not self._cfg.get('fulljson', _def.MQTT_FULLJSON):
                    l_payload = l_item['fields']
                    try:
                        del l_payload['time']
                    except:
                        pass
                else:
                    l_payload = l_item
                if not await self._publish(topic=l_topic, payload=str(l_payload).replace('\'', '\"').encode(), retain=self._retain):
                    logger.debug(f'{self._name} jobid:{l_jobid} publish failed topic:{l_topic} payload:{l_payload}')
        except Exception:
            logger.exception(f'***')
            return