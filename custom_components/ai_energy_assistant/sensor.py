import logging
import httpx
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
        headers = {"Authorization": f"Bearer {self.api_key}"}

        if self.provider == "gemini":
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, headers={"x-goog-api-key": self.api_key}, json={"contents": [{"parts": [{"text": prompt}]}]})
                if resp.status_code == 200:
                    return resp.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "No response")
                return f"Error: {resp.text}"

        elif self.provider == "openai":
            url = "https://api.openai.com/v1/chat/completions"
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
                return f"Error: {resp.text}"

        return "Provider not supported"


class AIEnergyPredictionSensor(CoordinatorEntity, Entity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "AI Energy Prediction"
        self._attr_unique_id = "ai_energy_prediction"

    @property
    def state(self):
        return self.coordinator.data