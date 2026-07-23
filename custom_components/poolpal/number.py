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
    CONF_RAW_EMPTY,
    CONF_GIVEN_LEVEL,
    CONF_RAW_GIVEN,
    CONF_DEVICE_IDENTIFIERS,
    CONF_DEVICE_CONNECTIONS,
    DEFAULT_INTERCEPT,
    DEFAULT_SLOPE,
    DEFAULT_RAW_EMPTY,
    DEFAULT_GIVEN_LEVEL,
    DEFAULT_RAW_GIVEN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    intercept = PoolPalIntercept(hass, entry)
    slope = PoolPalSlope(hass, entry)
    data["_intercept_entity"] = intercept
    data["_slope_entity"] = slope
    async_add_entities([
        intercept,
        slope,
        PoolPalRawEmpty(hass, entry),
        PoolPalGivenLevel(hass, entry),
        PoolPalRawGiven(hass, entry),
    ])


class PoolPalIntercept(NumberEntity, RestoreEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:counter"
    _attr_native_min_value = 0
    _attr_native_max_value = 10000
    _attr_native_step = 0.01
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
    _attr_native_min_value = 0
    _attr_native_max_value = 1000
    _attr_native_step = 0.0000001
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


class _CalibrationEntity(NumberEntity, RestoreEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry

        identifiers_raw = entry.data.get(CONF_DEVICE_IDENTIFIERS, [])
        connections_raw = entry.data.get(CONF_DEVICE_CONNECTIONS, [])
        device_info = {}
        if identifiers_raw:
            device_info["identifiers"] = {tuple(i) for i in identifiers_raw}
        if connections_raw:
            device_info["connections"] = {tuple(c) for c in connections_raw}
        self._attr_device_info = device_info or None

    def _recalc_slope_intercept(self) -> None:
        data = self.hass.data[DOMAIN][self._entry.entry_id]
        raw_empty = data.get(CONF_RAW_EMPTY, DEFAULT_RAW_EMPTY)
        given_level = data.get(CONF_GIVEN_LEVEL, DEFAULT_GIVEN_LEVEL)
        raw_given = data.get(CONF_RAW_GIVEN, DEFAULT_RAW_GIVEN)

        denom = raw_given - raw_empty
        if denom == 0:
            return

        new_slope = given_level / denom
        new_intercept = new_slope * raw_empty

        data[CONF_SLOPE] = new_slope
        data[CONF_INTERCEPT] = new_intercept

        intercept_ent = data.get("_intercept_entity")
        slope_ent = data.get("_slope_entity")
        if slope_ent is not None:
            slope_ent._attr_native_value = new_slope
            slope_ent.async_write_ha_state()
        if intercept_ent is not None:
            intercept_ent._attr_native_value = new_intercept
            intercept_ent.async_write_ha_state()


class PoolPalRawEmpty(_CalibrationEntity):
    _attr_icon = "mdi:counter"
    _attr_native_min_value = 0
    _attr_native_max_value = 100000
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX
    _attr_name = "Raw Capacitance (Empty)"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry)
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_raw_empty"
        self._attr_native_value = entry.data.get(CONF_RAW_EMPTY, DEFAULT_RAW_EMPTY)
        hass.data[DOMAIN][entry.entry_id][CONF_RAW_EMPTY] = self._attr_native_value

    async def async_added_to_hass(self) -> None:
        state = await self.async_get_last_state()
        if state is not None and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            try:
                self._attr_native_value = float(state.state)
            except (ValueError, TypeError):
                pass
        self.hass.data[DOMAIN][self._entry.entry_id][CONF_RAW_EMPTY] = self._attr_native_value

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.hass.data[DOMAIN][self._entry.entry_id][CONF_RAW_EMPTY] = value
        self._recalc_slope_intercept()
        self.async_write_ha_state()


class PoolPalGivenLevel(_CalibrationEntity):
    _attr_icon = "mdi:ruler"
    _attr_native_min_value = 0
    _attr_native_max_value = 10000
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = "cm"
    _attr_mode = NumberMode.BOX
    _attr_name = "Given Level"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry)
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_given_level"
        self._attr_native_value = entry.data.get(CONF_GIVEN_LEVEL, DEFAULT_GIVEN_LEVEL)
        hass.data[DOMAIN][entry.entry_id][CONF_GIVEN_LEVEL] = self._attr_native_value

    async def async_added_to_hass(self) -> None:
        state = await self.async_get_last_state()
        if state is not None and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            try:
                self._attr_native_value = float(state.state)
            except (ValueError, TypeError):
                pass
        self.hass.data[DOMAIN][self._entry.entry_id][CONF_GIVEN_LEVEL] = self._attr_native_value

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.hass.data[DOMAIN][self._entry.entry_id][CONF_GIVEN_LEVEL] = value
        self._recalc_slope_intercept()
        self.async_write_ha_state()


class PoolPalRawGiven(_CalibrationEntity):
    _attr_icon = "mdi:counter"
    _attr_native_min_value = 0
    _attr_native_max_value = 100000
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX
    _attr_name = "Raw Capacitance @ Given Level"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry)
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_raw_given"
        self._attr_native_value = entry.data.get(CONF_RAW_GIVEN, DEFAULT_RAW_GIVEN)
        hass.data[DOMAIN][entry.entry_id][CONF_RAW_GIVEN] = self._attr_native_value

    async def async_added_to_hass(self) -> None:
        state = await self.async_get_last_state()
        if state is not None and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            try:
                self._attr_native_value = float(state.state)
            except (ValueError, TypeError):
                pass
        self.hass.data[DOMAIN][self._entry.entry_id][CONF_RAW_GIVEN] = self._attr_native_value

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.hass.data[DOMAIN][self._entry.entry_id][CONF_RAW_GIVEN] = value
        self._recalc_slope_intercept()
        self.async_write_ha_state()
