"""Sensor platform for cost."""
from __future__ import annotations
from decimal import Decimal
from datetime import datetime, timedelta
import voluptuous as vol
from croniter import croniter

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import (
    config_validation as cv,
    entity_registry as er,
)

from homeassistant.helpers.event import (
    EventStateChangedData,
    async_track_point_in_time,
    async_track_state_change_event,
)

from homeassistant.components.utility_meter.const import (
    HOURLY,
    DAILY,
    WEEKLY,
    MONTHLY,
    YEARLY,
)

from homeassistant.components.sensor import (
    RestoreSensor,
    PLATFORM_SCHEMA,
)

from homeassistant.const import (
    STATE_UNKNOWN,
    STATE_UNAVAILABLE,
    CONF_NAME,
    CONF_UNIQUE_ID,
    CONF_UNIT_OF_MEASUREMENT,
)

from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.core import Event
import homeassistant.util.dt as dt_util

from .const import CONF_SOURCE_SENSOR, CONF_ROUND_DIGITS, CONF_TARIFF_SENSOR,CONF_CRON_PATTERN




DEFAULT_ROUND = 2

PERIOD2CRON = {
    HOURLY: "{minute} * * * *",
    DAILY: "{minute} {hour} * * *",
    WEEKLY: "{minute} {hour} * * {day}",
    MONTHLY: "{minute} {hour} {day} * *",
    YEARLY: "{minute} {hour} {day} 1/12 *",
}


PLATFORM_SCHEMA = vol.All(
    PLATFORM_SCHEMA.extend(
        {
            vol.Optional(CONF_NAME): cv.string,
            vol.Optional(CONF_UNIQUE_ID): cv.string,
            vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
            vol.Required(CONF_SOURCE_SENSOR): cv.entity_id,
            vol.Required(CONF_TARIFF_SENSOR): cv.entity_id,
            vol.Optional(CONF_CRON_PATTERN): cv.string,
            vol.Optional(CONF_ROUND_DIGITS, default=DEFAULT_ROUND): vol.Coerce(int),
        }
    )
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the integration sensor."""

    cronvalue = config[CONF_CRON_PATTERN]
    cronpattern = None

    if cronvalue is not None:
        delta = timedelta(days=0)
        cronpattern = PERIOD2CRON[cronvalue].format(
                    minute=delta.seconds % 3600 // 60,
                    hour=delta.seconds // 3600,
                    day=delta.days + 1,)
    config.get(CONF_UNIT_OF_MEASUREMENT)
    cost = CostSensor(
        config[CONF_SOURCE_SENSOR],
        config[CONF_TARIFF_SENSOR],
        cronpattern,
        config.get(CONF_NAME),
        config.get(CONF_UNIQUE_ID),
        config.get(CONF_UNIT_OF_MEASUREMENT),
        config.get(CONF_ROUND_DIGITS)
        )
    async_add_entities([cost])


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""

    registry = er.async_get(hass)
    # Validate + resolve entity registry id to entity_id
    source_entity_id = er.async_validate_entity_id(
        registry, config_entry.options[CONF_SOURCE_SENSOR]
    )

    tariff_entity_id = er.async_validate_entity_id(registry, config_entry.options[CONF_TARIFF_SENSOR])

    cron = config_entry.options[CONF_CRON_PATTERN]

    cronpattern = PERIOD2CRON[cron]

    cost = CostSensor(
        source_entity_id,
        tariff_entity_id,
        cronpattern,
        "Kostnad",
        "sensor.kostnad",
        "kr",
        2
        )
    async_add_entities([cost])


class CostSensor(RestoreSensor):
    """Cost sensor class."""

    def __init__(
        self,
        source_entity: str,
        cost_entity: str,
        cron_pattern: str,
        name: str,
        unique_id: str,
        unit_of_measurement: str,
        round_digits: int,
    ):
        """Initialize the cost sensor entity."""
        self._attr_name = name
        self._unit_of_measurement = unit_of_measurement
        self._attr_unique_id = unique_id
        self._sensor_source_id = source_entity
        self._sensor_cost_id = cost_entity
        self._state = None
        self._last_reset = dt_util.utcnow()
        self._name = name
        self._cron_pattern = cron_pattern
        self._round_digits = round_digits
        self._tariff = None
        self._last_period = None

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        if (last_sensor_data := await self.async_get_last_sensor_data()) is not None:
            if last_sensor_data.native_value is not None:
                self._state = (Decimal(str(last_sensor_data.native_value)))


        @callback
        def calc_integration(event: EventType[EventStateChangedData]) -> None:
            """Calculate the new value when source sensor changes."""

            old_state = event.data["old_state"]
            new_state = event.data["new_state"]

            if old_state is None or new_state is None:
                # One of the states are missing so we cannot calculate
                return

            if old_state.state is None or new_state.state is None:
                # One of the states are missing so we cannot calculate
                return

            if old_state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE) or new_state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
                # Calculation not possible as no delta value can be calculated
                return

            tariff = self.get_tariff()
            if tariff is None:
                return

            delta = Decimal(Decimal(new_state.state) - Decimal(old_state.state))

            if self._state is None:
                self._state = Decimal(0)

            self._state += Decimal(delta * tariff)
            self.async_write_ha_state()

        def tariff_changed(event: EventType[EventStateChangedData]) -> None:
            """Calculate the new value when source sensor changes."""
            new_state = event.data["new_state"]
            if new_state is None:
                return
            self._tariff = Decimal(new_state.state)

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._sensor_source_id], calc_integration
            )
        )

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._sensor_cost_id], tariff_changed
            )
        )

        if self._cron_pattern is not None:
            self.async_on_remove(
                async_track_point_in_time(
                    self.hass,
                    self._async_reset_meter,
                    croniter(self._cron_pattern, dt_util.now()).get_next(datetime),
                )
            )


    def get_tariff(self) -> Decimal | None:
        """Retreive tariff to be used."""
        if self._tariff is not None:
            return self._tariff
        tariffstate = self.hass.states.get(self._sensor_cost_id)

        if tariffstate is not None and tariffstate.state is not None and tariffstate.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            self._tariff = Decimal(tariffstate.state)

        return self._tariff

    async def _async_reset_meter(self, _):
        """Determine cycle - Helper function for larger than daily cycles."""
        if self._cron_pattern is not None:
            self.async_on_remove(
                async_track_point_in_time(
                    self.hass,
                    self._async_reset_meter,
                    croniter(self._cron_pattern, dt_util.now()).get_next(datetime),
                )
            )
        await self.async_reset_meter()

    async def async_reset_meter(self):
        """Reset meter."""
        if self._state is None:
            return

        self._last_reset = dt_util.utcnow()
        self._last_period = Decimal(self._state) if self._state else Decimal(0)
        self._state = 0
        self.async_write_ha_state()

    @property
    def native_value(self) -> Decimal | None:
        """Return the state of the sensor."""
        if isinstance(self._state, Decimal):
            return round(self._state, self._round_digits)
        return self._state

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit the value is expressed in."""
        return self._unit_of_measurement
