#!/usr/bin/env python
# -*- coding: utf8 -*-
# Author: li_yun@vobile.cn
# Date: 2014-02-17 13:53:06

import os
import sys
import time
from ConfigParser import ConfigParser

__filedir__ = os.path.dirname(os.path.abspath(__file__))
__HOME__ = os.path.dirname(__filedir__)
print __HOME__

def load_qfairy_config():
    config_file = os.path.normpath(os.path.join(__HOME__, "config", "Qconfig"))
    config = ConfigParser()
    config_dict = {}
    config.read(config_file)
    config_dict["VIDEO_PATH"] = config.get("Qconfig", "VIDEO_PATH") # TODO set a default path
    config_dict["CACHE_PATH "] = config.get("Qconfig", "CACHE_PATH") # TODO set a default path
    config_dict["TIMEOUT"] = config.get("Qconfig", "TIMEOUT") # TODO set a default path
    config_dict["RECORD "] = config.get("Qconfig", "RECORD") # FIXME use database instead it
    return config_dict

