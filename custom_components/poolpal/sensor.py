import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components import mqtt
from .const import (
    DOMAIN,
    CONF_MQTT_TOPIC,
    CONF_CALIBRATION_FACTOR,
    CONF_DEVICE_IDENTIFIERS,
    CONF_DEVICE_CONNECTIONS,
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
        self._topic = entry.data[CONF_MQTT_TOPIC]
        self._calibration = entry.data[CONF_CALIBRATION_FACTOR]
        self._attr_name = entry.data.get("name", "PoolPal Sensor")
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}"
        self._unsub_mqtt = None

        identifiers_raw = entry.data.get(CONF_DEVICE_IDENTIFIERS, [])
        connections_raw = entry.data.get(CONF_DEVICE_CONNECTIONS, [])
        device_info = {}
        if identifiers_raw:
            device_info["identifiers"] = {tuple(i) for i in identifiers_raw}
        if connections_raw:
            device_info["connections"] = {tuple(c) for c in connections_raw}
        self._attr_device_info = device_info or None

    async def async_added_to_hass(self) -> None:
        @callback
        def message_received(msg):
            try:
                raw = float(msg.payload)
                self._attr_native_value = raw * self._calibration
                self.async_write_ha_state()
            except (ValueError, TypeError):
                _LOGGER.warning(
                    "Non-numeric payload on %s: %s", self._topic, msg.payload
                )

        self._unsub_mqtt = await mqtt.async_subscribe(
            self.hass, self._topic, message_received, qos=0
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub_mqtt:
            self._unsub_mqtt()
            self._unsub_mqtt = None
