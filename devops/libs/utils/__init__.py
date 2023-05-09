# coding: utf-8
from .common import *
from .db import Hub
from django.conf import settings
import pymysql

db = Hub(pymysql)
for alias, config in settings.DATABASES.items():
    db.add_pool(alias,
                host=config['HOST'],
                port=int(config.get('PORT', 3306)),
                user=config['USER'],
                passwd=config['PASSWORD'],
                db=config['NAME'],
                charset='utf8',
                autocommit=True,
                pool_size=settings.DB_POOL_SIZE,
                wait_timeout=settings.DB_WAIT_TIMEOUT,
                )
