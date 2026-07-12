from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
import voluptuous as vol
from .const import (
    API_VARIANTS,
    CONF_API_VARIANT,
    CONF_SCREEN,
    DEFAULT_API_VARIANT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SCREEN,
    DOMAIN,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_API_VARIANT, default=DEFAULT_API_VARIANT): vol.In(
            API_VARIANTS
        ),
        vol.Optional(CONF_SCREEN, default=DEFAULT_SCREEN): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=15, max=3600)
        ),
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                username = user_input[CONF_USERNAME]
                password = user_input[CONF_PASSWORD]
                info = f"Stoker Cloud {username}"
                return self.async_create_entry(title=info, data=user_input)
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
