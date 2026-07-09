import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from .const import (
    DOMAIN,
    CONF_SOURCE_ENTITY,
    CONF_SUBTRACTOR,
    CONF_DIVIDER,
    CONF_DEVICE_IDENTIFIERS,
    CONF_DEVICE_CONNECTIONS,
    DEFAULT_SUBTRACTOR,
    DEFAULT_DIVIDER,
    UNIT_CM,
    DEVICE_CLASS_DISTANCE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([PoolPalSensor(hass, entry)])


class PoolPalSensor(SensorEntity):
    _attr_should_poll = False
    _attr_force_update = True
    _attr_native_unit_of_measurement = UNIT_CM
    _attr_device_class = DEVICE_CLASS_DISTANCE

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._source_entity = entry.data[CONF_SOURCE_ENTITY]
        self._attr_name = entry.data.get("name", "PoolPal Sensor")
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}"

        identifiers_raw = entry.data.get(CONF_DEVICE_IDENTIFIERS, [])
        connections_raw = entry.data.get(CONF_DEVICE_CONNECTIONS, [])
        device_info = {}
        if identifiers_raw:
            device_info["identifiers"] = {tuple(i) for i in identifiers_raw}
        if connections_raw:
            device_info["connections"] = {tuple(c) for c in connections_raw}
        self._attr_device_info = device_info or None

    def _get_subtractor(self) -> float:
        return self._entry.options.get(
            CONF_SUBTRACTOR,
            self._entry.data.get(CONF_SUBTRACTOR, DEFAULT_SUBTRACTOR),
        )

    def _get_divider(self) -> float:
        return self._entry.options.get(
            CONF_DIVIDER,
            self._entry.data.get(CONF_DIVIDER, DEFAULT_DIVIDER),
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._source_entity], self._handle_state_change
            )
        )
        state = self.hass.states.get(self._source_entity)
        if state is not None and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            try:
                raw = float(state.state)
                self._attr_native_value = (raw - self._get_subtractor()) / self._get_divider()
            except (ValueError, TypeError):
                pass

    @callback
    def _handle_state_change(self, event):
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return
        try:
            raw = float(new_state.state)
            self._attr_native_value = (raw - self._get_subtractor()) / self._get_divider()
            self.async_write_ha_state()
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Non-numeric state from %s: %s", self._source_entity, new_state.state
            )
