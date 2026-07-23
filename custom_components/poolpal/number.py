import logging
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.restore_state import RestoreEntity
from .const import (
    DOMAIN,
    CONF_INTERCEPT,
    CONF_SLOPE,
    CONF_DEVICE_IDENTIFIERS,
    CONF_DEVICE_CONNECTIONS,
    DEFAULT_INTERCEPT,
    DEFAULT_SLOPE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([
        PoolPalIntercept(hass, entry),
        PoolPalSlope(hass, entry),
    ])


class PoolPalIntercept(NumberEntity, RestoreEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:counter"
    _attr_native_min_value = -10000
    _attr_native_max_value = 10000
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_name = "Intercept"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_intercept"
        self._attr_native_value = entry.data.get(
            CONF_INTERCEPT, DEFAULT_INTERCEPT
        )

        identifiers_raw = entry.data.get(CONF_DEVICE_IDENTIFIERS, [])
        connections_raw = entry.data.get(CONF_DEVICE_CONNECTIONS, [])
        device_info = {}
        if identifiers_raw:
            device_info["identifiers"] = {tuple(i) for i in identifiers_raw}
        if connections_raw:
            device_info["connections"] = {tuple(c) for c in connections_raw}
        self._attr_device_info = device_info or None

        hass.data[DOMAIN][entry.entry_id][CONF_INTERCEPT] = self._attr_native_value

    async def async_added_to_hass(self) -> None:
        self.hass.data[DOMAIN][self._entry.entry_id]["intercept_entity_id"] = self.entity_id
        state = await self.async_get_last_state()
        if state is not None and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            try:
                self._attr_native_value = float(state.state)
            except (ValueError, TypeError):
                pass
        self.hass.data[DOMAIN][self._entry.entry_id][CONF_INTERCEPT] = self._attr_native_value

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.hass.data[DOMAIN][self._entry.entry_id][CONF_INTERCEPT] = value
        self.async_write_ha_state()


class PoolPalSlope(NumberEntity, RestoreEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:alpha-b"
    _attr_native_min_value = -1000
    _attr_native_max_value = 1000
    _attr_native_step = 0.000001
    _attr_mode = NumberMode.BOX

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_name = "Slope"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_slope"
        self._attr_native_value = entry.data.get(
            CONF_SLOPE, DEFAULT_SLOPE
        )

        identifiers_raw = entry.data.get(CONF_DEVICE_IDENTIFIERS, [])
        connections_raw = entry.data.get(CONF_DEVICE_CONNECTIONS, [])
        device_info = {}
        if identifiers_raw:
            device_info["identifiers"] = {tuple(i) for i in identifiers_raw}
        if connections_raw:
            device_info["connections"] = {tuple(c) for c in connections_raw}
        self._attr_device_info = device_info or None

        hass.data[DOMAIN][entry.entry_id][CONF_SLOPE] = self._attr_native_value

    async def async_added_to_hass(self) -> None:
        self.hass.data[DOMAIN][self._entry.entry_id]["slope_entity_id"] = self.entity_id
        state = await self.async_get_last_state()
        if state is not None and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            try:
                self._attr_native_value = float(state.state)
            except (ValueError, TypeError):
                pass
        self.hass.data[DOMAIN][self._entry.entry_id][CONF_SLOPE] = self._attr_native_value

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.hass.data[DOMAIN][self._entry.entry_id][CONF_SLOPE] = value
        self.async_write_ha_state()
