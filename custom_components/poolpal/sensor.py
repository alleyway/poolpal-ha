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
    _attr_suggested_display_precision = 1

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

    def _get_data(self, key: str, default: float) -> float:
        return self.hass.data.get(DOMAIN, {}).get(
            self._entry.entry_id, {}
        ).get(key, default)

    def _get_subtractor(self) -> float:
        return self._get_data(CONF_SUBTRACTOR, DEFAULT_SUBTRACTOR)

    def _get_divider(self) -> float:
        return self._get_data(CONF_DIVIDER, DEFAULT_DIVIDER)

    async def async_added_to_hass(self) -> None:
        entity_ids = [self._source_entity]
        data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id, {})
        for key in ("subtractor_entity_id", "divider_entity_id"):
            if key in data:
                entity_ids.append(data[key])

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, entity_ids, self._handle_state_change
            )
        )

        self._recalculate()

    @callback
    def _handle_state_change(self, event):
        self._recalculate()

    def _recalculate(self):
        state = self.hass.states.get(self._source_entity)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return
        try:
            raw = float(state.state)
            self._attr_native_value = (raw - self._get_subtractor()) / self._get_divider()
            self.async_write_ha_state()
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Non-numeric state from %s: %s", self._source_entity, state.state
            )
