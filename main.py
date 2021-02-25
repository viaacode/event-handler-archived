#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging

from uvicorn import Config, Server

from viaa.configuration import ConfigParser


cfg_log_level = ConfigParser().config["logging"]["level"]
# Uvicorn expects lowercase string or integer as the logging level.
LOG_LEVEL = cfg_log_level.lower() if isinstance(cfg_log_level, str) else cfg_log_level

if __name__ == "__main__":
    server = Server(
        Config(
            "app.app:app",
            host="0.0.0.0",
            port=8080,
            access_log=False,
            log_level=LOG_LEVEL,
        ),
    )

    # Remove the Uvicorn logging handlers, as our own loggers log in a JSON format.
    # Just remove them all although the access handler is already removed by "access_log=False".
    for name, logger in logging.root.manager.loggerDict.items():
        if name.startswith("uvicorn"):
            logger.handlers = []

    server.run()
