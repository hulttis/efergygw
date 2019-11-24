# coding=utf-8
#-------------------------------------------------------------------------------
# Name:        efergy_influx.py
# Purpose:     efergy specific influx
# Copyright:   (c) 2019 TK
# Licence:     MIT
#-------------------------------------------------------------------------------
import logging
logger = logging.getLogger('influx')

from influx_aioclient import influx_aioclient as _influx

# ==================================================================================

class efergy_influx(_influx):
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
        self._funcs['execute_efergy'] = self._execute_dict

        logger.info(f'{self._name} done')

#-------------------------------------------------------------------------------


