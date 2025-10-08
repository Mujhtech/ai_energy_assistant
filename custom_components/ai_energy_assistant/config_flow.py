import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_API_KEY, CONF_PROVIDER, DEFAULT_PROVIDER, SUPPORTED_PROVIDERS

class AIEnergyAssistantConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="AI Energy Assistant", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_API_KEY): str,
            vol.Optional(CONF_PROVIDER, default=DEFAULT_PROVIDER): vol.In(SUPPORTED_PROVIDERS)
        })

        return self.async_show_form(step_id="user", data_schema=schema)