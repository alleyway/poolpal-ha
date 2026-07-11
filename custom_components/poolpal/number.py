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
    CONF_OFFSET,
    CONF_LINEAR_COEFFICIENT,
    CONF_QUAD_COEFFICIENT,
    CONF_DEVICE_IDENTIFIERS,
    CONF_DEVICE_CONNECTIONS,
    DEFAULT_OFFSET,
    DEFAULT_LINEAR_COEFFICIENT,
    DEFAULT_QUAD_COEFFICIENT,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([
        PoolPalOffset(hass, entry),
        PoolPalLinearCoefficient(hass, entry),
        PoolPalQuadCoefficient(hass, entry),
    ])


class PoolPalOffset(NumberEntity, RestoreEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:counter"
    _attr_native_min_value = -10000
    _attr_native_max_value = 10000
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_name = "Offset"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_offset"
        self._attr_native_value = entry.data.get(
            CONF_OFFSET, DEFAULT_OFFSET
        )

        identifiers_raw = entry.data.get(CONF_DEVICE_IDENTIFIERS, [])
        connections_raw = entry.data.get(CONF_DEVICE_CONNECTIONS, [])
        device_info = {}
        if identifiers_raw:
            device_info["identifiers"] = {tuple(i) for i in identifiers_raw}
        if connections_raw:
            device_info["connections"] = {tuple(c) for c in connections_raw}
        self._attr_device_info = device_info or None

        hass.data[DOMAIN][entry.entry_id][CONF_OFFSET] = self._attr_native_value

    async def async_added_to_hass(self) -> None:
        self.hass.data[DOMAIN][self._entry.entry_id]["offset_entity_id"] = self.entity_id
        state = await self.async_get_last_state()
        if state is not None and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            try:
                self._attr_native_value = float(state.state)
            except (ValueError, TypeError):
                pass
        self.hass.data[DOMAIN][self._entry.entry_id][CONF_OFFSET] = self._attr_native_value

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.hass.data[DOMAIN][self._entry.entry_id][CONF_OFFSET] = value
        self.async_write_ha_state()


class PoolPalLinearCoefficient(NumberEntity, RestoreEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:alpha-b"
    _attr_native_min_value = -1000
    _attr_native_max_value = 1000
    _attr_native_step = 0.000001
    _attr_mode = NumberMode.BOX

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_name = "Linear Coefficient"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_linear_coefficient"
        self._attr_native_value = entry.data.get(
            CONF_LINEAR_COEFFICIENT, DEFAULT_LINEAR_COEFFICIENT
        )

        identifiers_raw = entry.data.get(CONF_DEVICE_IDENTIFIERS, [])
        connections_raw = entry.data.get(CONF_DEVICE_CONNECTIONS, [])
        device_info = {}
        if identifiers_raw:
            device_info["identifiers"] = {tuple(i) for i in identifiers_raw}
        if connections_raw:
            device_info["connections"] = {tuple(c) for c in connections_raw}
        self._attr_device_info = device_info or None

        hass.data[DOMAIN][entry.entry_id][CONF_LINEAR_COEFFICIENT] = self._attr_native_value

    async def async_added_to_hass(self) -> None:
        self.hass.data[DOMAIN][self._entry.entry_id]["linear_coefficient_entity_id"] = self.entity_id
        state = await self.async_get_last_state()
        if state is not None and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            try:
                self._attr_native_value = float(state.state)
            except (ValueError, TypeError):
                pass
        self.hass.data[DOMAIN][self._entry.entry_id][CONF_LINEAR_COEFFICIENT] = self._attr_native_value

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.hass.data[DOMAIN][self._entry.entry_id][CONF_LINEAR_COEFFICIENT] = value
        self.async_write_ha_state()


class PoolPalQuadCoefficient(NumberEntity, RestoreEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:alpha-a"
    _attr_native_min_value = -1
    _attr_native_max_value = 1
    _attr_native_step = 0.000001
    _attr_mode = NumberMode.BOX

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_name = "Quadratic Coefficient"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_quad_coefficient"
        self._attr_native_value = entry.data.get(
            CONF_QUAD_COEFFICIENT, DEFAULT_QUAD_COEFFICIENT
        )

        identifiers_raw = entry.data.get(CONF_DEVICE_IDENTIFIERS, [])
        connections_raw = entry.data.get(CONF_DEVICE_CONNECTIONS, [])
        device_info = {}
        if identifiers_raw:
            device_info["identifiers"] = {tuple(i) for i in identifiers_raw}
        if connections_raw:
            device_info["connections"] = {tuple(c) for c in connections_raw}
        self._attr_device_info = device_info or None

        hass.data[DOMAIN][entry.entry_id][CONF_QUAD_COEFFICIENT] = self._attr_native_value

    async def async_added_to_hass(self) -> None:
        self.hass.data[DOMAIN][self._entry.entry_id]["quad_coefficient_entity_id"] = self.entity_id
        state = await self.async_get_last_state()
        if state is not None and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            try:
                self._attr_native_value = float(state.state)
            except (ValueError, TypeError):
                pass
        self.hass.data[DOMAIN][self._entry.entry_id][CONF_QUAD_COEFFICIENT] = self._attr_native_value

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.hass.data[DOMAIN][self._entry.entry_id][CONF_QUAD_COEFFICIENT] = value
        self.async_write_ha_state()
