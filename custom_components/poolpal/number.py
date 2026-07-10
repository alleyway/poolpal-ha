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
    CONF_SUBTRACTOR,
    CONF_DIVIDER,
    CONF_DEVICE_IDENTIFIERS,
    CONF_DEVICE_CONNECTIONS,
    DEFAULT_SUBTRACTOR,
    DEFAULT_DIVIDER,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([
        PoolPalSubtractor(hass, entry),
        PoolPalDivider(hass, entry),
    ])


class PoolPalSubtractor(NumberEntity, RestoreEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:minus"
    _attr_native_min_value = 0
    _attr_native_max_value = 10000
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_name = "Subtractor"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_subtractor"
        self._attr_native_value = entry.data.get(
            CONF_SUBTRACTOR, DEFAULT_SUBTRACTOR
        )

        identifiers_raw = entry.data.get(CONF_DEVICE_IDENTIFIERS, [])
        connections_raw = entry.data.get(CONF_DEVICE_CONNECTIONS, [])
        device_info = {}
        if identifiers_raw:
            device_info["identifiers"] = {tuple(i) for i in identifiers_raw}
        if connections_raw:
            device_info["connections"] = {tuple(c) for c in connections_raw}
        self._attr_device_info = device_info or None

        hass.data[DOMAIN][entry.entry_id][CONF_SUBTRACTOR] = self._attr_native_value

    async def async_added_to_hass(self) -> None:
        self.hass.data[DOMAIN][self._entry.entry_id]["subtractor_entity_id"] = self.entity_id
        state = await self.async_get_last_state()
        if state is not None and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            try:
                self._attr_native_value = float(state.state)
            except (ValueError, TypeError):
                pass
        self.hass.data[DOMAIN][self._entry.entry_id][CONF_SUBTRACTOR] = self._attr_native_value

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.hass.data[DOMAIN][self._entry.entry_id][CONF_SUBTRACTOR] = value
        self.async_write_ha_state()


class PoolPalDivider(NumberEntity, RestoreEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:division"
    _attr_native_min_value = 0.01
    _attr_native_max_value = 1000
    _attr_native_step = 0.01
    _attr_mode = NumberMode.BOX

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_name = "Divider"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_divider"
        self._attr_native_value = entry.data.get(
            CONF_DIVIDER, DEFAULT_DIVIDER
        )

        identifiers_raw = entry.data.get(CONF_DEVICE_IDENTIFIERS, [])
        connections_raw = entry.data.get(CONF_DEVICE_CONNECTIONS, [])
        device_info = {}
        if identifiers_raw:
            device_info["identifiers"] = {tuple(i) for i in identifiers_raw}
        if connections_raw:
            device_info["connections"] = {tuple(c) for c in connections_raw}
        self._attr_device_info = device_info or None

        hass.data[DOMAIN][entry.entry_id][CONF_DIVIDER] = self._attr_native_value

    async def async_added_to_hass(self) -> None:
        self.hass.data[DOMAIN][self._entry.entry_id]["divider_entity_id"] = self.entity_id
        state = await self.async_get_last_state()
        if state is not None and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            try:
                self._attr_native_value = float(state.state)
            except (ValueError, TypeError):
                pass
        self.hass.data[DOMAIN][self._entry.entry_id][CONF_DIVIDER] = self._attr_native_value

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.hass.data[DOMAIN][self._entry.entry_id][CONF_DIVIDER] = value
        self.async_write_ha_state()
