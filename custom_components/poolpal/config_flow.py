import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from .const import (
    DOMAIN,
    MANUFACTURER,
    CONF_SOURCE_ENTITY,
    CONF_INTERCEPT,
    CONF_SLOPE,
    CONF_DEVICE_IDENTIFIERS,
    CONF_DEVICE_CONNECTIONS,
    SOURCE_ENTITY_SUFFIX,
    DEFAULT_INTERCEPT,
    DEFAULT_SLOPE,
)


class PoolPalConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._device_id = None
        self._device_identifiers = None
        self._device_connections = None
        self._device_name = None

    async def async_step_user(self, user_input=None):
        errors = {}
        registry = dr.async_get(self.hass)

        devices = {}
        for device_id, device in registry.devices.items():
            if device.manufacturer != MANUFACTURER:
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
                self._device_id = device_id
                self._device_identifiers = [list(i) for i in device.identifiers]
                self._device_connections = [list(c) for c in device.connections]
                self._device_name = device.name_by_user or device.name or "Device"
                return await self.async_step_configure()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required("device"): vol.In(devices)}
            ),
            errors=errors,
        )

    async def async_step_configure(self, user_input=None):
        errors = {}
        entity_registry = er.async_get(self.hass)
        entities = {
            entry.entity_id: entry.name or entry.entity_id
            for entry in entity_registry.entities.values()
            if entry.device_id == self._device_id
            and entry.entity_id.endswith(SOURCE_ENTITY_SUFFIX)
        }

        if not entities:
            return self.async_abort(reason="no_entities")

        if user_input is not None:
            source = user_input[CONF_SOURCE_ENTITY]
            state = self.hass.states.get(source)
            if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                errors["base"] = "invalid_state"
            else:
                try:
                    float(state.state)
                except (ValueError, TypeError):
                    errors["base"] = "invalid_state"

            if not errors:
                return self.async_create_entry(
                    title=self._device_name,
                    data={
                        CONF_SOURCE_ENTITY: source,
                        CONF_INTERCEPT: user_input[CONF_INTERCEPT],
                        CONF_SLOPE: user_input[CONF_SLOPE],
                        CONF_DEVICE_IDENTIFIERS: self._device_identifiers or [],
                        CONF_DEVICE_CONNECTIONS: self._device_connections or [],
                        "name": user_input["name"],
                    },
                )

        return await self._show_configure_form(entities, errors)

    async def _show_configure_form(self, entities, errors=None):
        entity_id = next(iter(entities))
        entity_name = entities[entity_id].split(".", 1)[-1] if "." in entities[entity_id] else entities[entity_id]
        default_name = f"{entity_name} Water Level"
        return self.async_show_form(
            step_id="configure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SOURCE_ENTITY): vol.In(entities),
                    vol.Required(
                        CONF_INTERCEPT, default=DEFAULT_INTERCEPT
                    ): vol.Coerce(float),
                    vol.Required(
                        CONF_SLOPE, default=DEFAULT_SLOPE
                    ): vol.Coerce(float),
                    vol.Optional("name", default=default_name): str,
                }
            ),
            errors=errors or {},
        )

    @staticmethod
    async def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return PoolPalOptionsFlow(config_entry)


class PoolPalOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data=user_input,
            )

        current_intercept = self._config_entry.options.get(
            CONF_INTERCEPT,
            self._config_entry.data.get(CONF_INTERCEPT, DEFAULT_INTERCEPT),
        )
        current_slope = self._config_entry.options.get(
            CONF_SLOPE,
            self._config_entry.data.get(CONF_SLOPE, DEFAULT_SLOPE),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_INTERCEPT, default=current_intercept
                    ): vol.Coerce(float),
                    vol.Required(
                        CONF_SLOPE, default=current_slope
                    ): vol.Coerce(float),
                }
            ),
            errors=errors,
        )
