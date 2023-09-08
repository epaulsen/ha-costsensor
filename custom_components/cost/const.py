"""Constants for cost platform."""
from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

NAME = "Cost"
DOMAIN = "cost"
VERSION = "0.0.0"

CONF_ROUND_DIGITS = "round"
CONF_SOURCE_SENSOR = "source"
CONF_TARIFF_SENSOR = "tariff"
CONF_CRON_PATTERN = "cron"
