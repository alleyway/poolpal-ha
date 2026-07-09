import asyncio
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.components import mqtt
from .const import (
    DOMAIN,
    CONF_MQTT_TOPIC,
    CONF_CALIBRATION_FACTOR,
    CONF_DEVICE_IDENTIFIERS,
    CONF_DEVICE_CONNECTIONS,
    DEFAULT_CALIBRATION_FACTOR,
)

ALL_MANUFACTURERS = "All manufacturers"


class PoolPalConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._manufacturer = None
        self._device_identifiers = None
        self._device_connections = None
        self._device_name = None

    async def async_step_user(self, user_input=None):
        errors = {}
        registry = dr.async_get(self.hass)
        manufacturers = sorted(
            {
                device.manufacturer
                for device in registry.devices.values()
                if device.manufacturer
            }
        )
        if not manufacturers:
            return self.async_abort(reason="no_devices")

        manufacturers = [ALL_MANUFACTURERS] + manufacturers

        if user_input is not None:
            selected = user_input["manufacturer"]
            self._manufacturer = None if selected == ALL_MANUFACTURERS else selected
            return await self.async_step_device()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required("manufacturer"): vol.In(manufacturers)}
            ),
            errors=errors,
        )

    async def async_step_device(self, user_input=None):
        errors = {}
        registry = dr.async_get(self.hass)

        devices = {}
        for device_id, device in registry.devices.items():
            if self._manufacturer and device.manufacturer != self._manufacturer:
                continue
            label = device.name_by_user or device.name
            if not label:
                continue
            if device.model:
                label += f" ({device.model})"
            if device.manufacturer:
                label += f" by {device.manufacturer}"
            devices[device_id] = label

        if not devices:
            return self.async_abort(reason="no_devices")

        if user_input is not None:
            device_id = user_input["device"]
            device = registry.devices.get(device_id)
            if device is None:
                errors["base"] = "unknown_device"
            else:
                self._device_identifiers = [list(i) for i in device.identifiers]
                self._device_connections = [list(c) for c in device.connections]
                self._device_name = device.name_by_user or device.name or "Device"
                return await self.async_step_configure()

        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema(
                {vol.Required("device"): vol.In(devices)}
            ),
            errors=errors,
        )

    async def async_step_configure(self, user_input=None):
        errors = {}
        if user_input is not None:
            topic = user_input[CONF_MQTT_TOPIC]

            try:
                received = asyncio.Event()

                @callback
                def _message_received(msg):
                    received.set()

                unsub = await mqtt.async_subscribe(
                    self.hass, topic, _message_received, qos=0
                )
                try:
                    await asyncio.wait_for(received.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    unsub()
                    errors["base"] = "invalid_topic"
                    return await self._show_configure_form(
                        errors, user_input.get("name")
                    )
                unsub()
            except Exception:
                errors["base"] = "invalid_topic"
                return await self._show_configure_form(
                    errors, user_input.get("name")
                )

            return self.async_create_entry(
                title=self._device_name,
                data={
                    CONF_MQTT_TOPIC: topic,
                    CONF_CALIBRATION_FACTOR: user_input[CONF_CALIBRATION_FACTOR],
                    CONF_DEVICE_IDENTIFIERS: self._device_identifiers or [],
                    CONF_DEVICE_CONNECTIONS: self._device_connections or [],
                    "name": user_input["name"],
                },
            )

        return await self._show_configure_form()

    async def _show_configure_form(self, errors=None, name=None):
        default_name = name or f"{self._device_name} - PoolPal"
        return self.async_show_form(
            step_id="configure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MQTT_TOPIC): str,
                    vol.Required(
                        CONF_CALIBRATION_FACTOR, default=DEFAULT_CALIBRATION_FACTOR
                    ): vol.Coerce(float),
                    vol.Optional("name", default=default_name): str,
                }
            ),
            errors=errors or {},
        )
