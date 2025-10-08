import logging
from openai import AsyncOpenAI
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from datetime import timedelta
from .const import DOMAIN, CONF_API_KEY, CONF_PROVIDER

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    api_key = config_entry.data[CONF_API_KEY]
    provider = config_entry.data[CONF_PROVIDER]

    coordinator = AIEnergyCoordinator(hass, api_key, provider)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([AIEnergyPredictionSensor(coordinator)], True)


class AIEnergyCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api_key, provider):
        super().__init__(hass, _LOGGER, name="AI Energy Assistant", update_interval=timedelta(hours=1))
        self.api_key = api_key
        self.provider = provider

        # Initialize OpenAI client for both providers
        if provider == "openai":
            self.client = AsyncOpenAI(api_key=api_key)
            self.model = "gpt-4o-mini"
        elif provider == "gemini":
            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
            )
            self.model = "gemini-2.0-flash-exp"
        else:
            self.client = None
            self.model = None

    async def _async_update_data(self):
        # Example: Gather Home Assistant sensor states
        solar_today = self.hass.states.get("sensor.growatt_solar_energy_today")
        load_pct = self.hass.states.get("sensor.growatt_load_percentage")
        battery_soc = self.hass.states.get("sensor.growatt_battery_soc")

        prompt = f"""
        My solar system data today:
        - Solar Energy Today: {solar_today.state if solar_today else "unknown"} kWh
        - Load Percentage: {load_pct.state if load_pct else "unknown"} %
        - Battery SOC: {battery_soc.state if battery_soc else "unknown"} %

        Please analyze and explain my daily energy usage and give prediction for tomorrow.
        """

        return await self.call_llm(prompt)

    async def call_llm(self, prompt: str):
        try:
            if not self.client:
                return "Provider not supported"

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert energy analyst specializing in solar power systems. Analyze energy data, provide insights on consumption patterns, identify optimization opportunities, and make accurate predictions based on historical trends and current conditions."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            _LOGGER.error(f"Error calling {self.provider}: {e}")
            return f"Error: {str(e)}"


class AIEnergyPredictionSensor(CoordinatorEntity, Entity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "AI Energy Prediction"
        self._attr_unique_id = "ai_energy_prediction"

    @property
    def state(self):
        return self.coordinator.data