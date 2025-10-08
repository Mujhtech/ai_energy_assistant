import logging
from openai import AsyncOpenAI
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.components.recorder import get_instance, history
from datetime import timedelta, datetime
from .const import DOMAIN, CONF_API_KEY, CONF_PROVIDER, CONF_PANEL_SIZE

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    api_key = config_entry.data[CONF_API_KEY]
    provider = config_entry.data[CONF_PROVIDER]
    panel_size = config_entry.data.get(CONF_PANEL_SIZE, 0)

    coordinator = AIEnergyCoordinator(hass, api_key, provider, panel_size)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([AIEnergyPredictionSensor(coordinator)], True)


class AIEnergyCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api_key, provider, panel_size=0):
        super().__init__(hass, _LOGGER, name="AI Energy Assistant", update_interval=timedelta(hours=1))
        self.api_key = api_key
        self.provider = provider
        self.panel_size = panel_size

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
        # Gather current Home Assistant sensor states
        solar_today = self.hass.states.get("sensor.growatt_solar_energy_today")
        load_pct = self.hass.states.get("sensor.growatt_load_percentage")
        battery_soc = self.hass.states.get("sensor.growatt_battery_soc")

        # Extract current state values
        solar_value = solar_today.state if solar_today and solar_today.state not in ["unknown", "unavailable"] else None
        load_value = load_pct.state if load_pct and load_pct.state not in ["unknown", "unavailable"] else None
        battery_value = battery_soc.state if battery_soc and battery_soc.state not in ["unknown", "unavailable"] else None

        # Get weather data
        weather_data = self._get_weather_data()

        # Fetch 7 days of historical data
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)

        historical_data = await self._fetch_historical_data(
            ["sensor.growatt_solar_energy_today", "sensor.growatt_load_percentage", "sensor.growatt_battery_soc"],
            start_time,
            end_time
        )

        # Format historical data for prompt
        history_summary = self._format_historical_data(historical_data)

        # Build system information
        system_info = ""
        if self.panel_size and self.panel_size > 0:
            system_info = f"\n**System Configuration:**\n- Solar Panel System Size: {self.panel_size} kW\n"

        prompt = f"""Analyze my solar energy system data and provide a concise summary with prediction for tomorrow.
{system_info}
**Current Data (Today):**
- Solar Energy Production: {solar_value} kWh
- Load Percentage: {load_value}%
- Battery State of Charge: {battery_value}%

**Weather Information:**
{weather_data}

**Historical Data (Past 7 Days):**
{history_summary}

Please provide:
1. Brief analysis of today's performance compared to the past week (2-3 sentences)
2. Trends and patterns observed (1-2 key insights)
3. Tomorrow's prediction based on historical trends (1-2 sentences)
4. One specific actionable recommendation

Keep the response under 500 words and focus on actionable insights based on the data trends."""

        return await self.call_llm(prompt)

    async def _fetch_historical_data(self, entity_ids, start_time, end_time):
        """Fetch historical data for specified entities."""
        try:
            historical_states = await get_instance(self.hass).async_add_executor_job(
                history.state_changes_during_period,
                self.hass,
                start_time,
                end_time,
                None,
                entity_ids,
                False,
                True,
                None
            )
            return historical_states
        except Exception as e:
            _LOGGER.error(f"Error fetching historical data: {e}")
            return {}

    def _format_historical_data(self, historical_data):
        """Format historical data into a readable summary."""
        if not historical_data:
            return "No historical data available."

        summary_lines = []

        # Process each sensor's historical data
        for entity_id, states in historical_data.items():
            if not states:
                continue

            sensor_name = entity_id.replace("sensor.growatt_", "").replace("_", " ").title()

            # Extract numeric values and calculate statistics
            values = []
            for state in states:
                try:
                    if state.state not in ["unknown", "unavailable", "None"]:
                        values.append(float(state.state))
                except (ValueError, AttributeError):
                    continue

            if values:
                avg_value = sum(values) / len(values)
                min_value = min(values)
                max_value = max(values)

                summary_lines.append(
                    f"- {sensor_name}: Avg={avg_value:.2f}, Min={min_value:.2f}, Max={max_value:.2f}"
                )

        return "\n".join(summary_lines) if summary_lines else "Insufficient historical data for analysis."

    def _get_weather_data(self):
        """Get current weather and forecast data from Home Assistant."""
        weather_info = []

        # Try to get weather entity (common entity IDs)
        weather_entities = [
            "weather.home",
            "weather.forecast_home",
            "weather.openweathermap",
            "weather.met_no",
            "weather.accuweather"
        ]

        weather_entity = None
        for entity_id in weather_entities:
            entity = self.hass.states.get(entity_id)
            if entity:
                weather_entity = entity
                break

        if not weather_entity:
            # Try to find any weather entity
            for entity_id in self.hass.states.async_entity_ids("weather"):
                weather_entity = self.hass.states.get(entity_id)
                if weather_entity:
                    break

        if weather_entity:
            # Current weather
            condition = weather_entity.state
            attrs = weather_entity.attributes

            weather_info.append(f"Current Condition: {condition}")

            if "temperature" in attrs:
                weather_info.append(f"Temperature: {attrs['temperature']}°C")

            if "humidity" in attrs:
                weather_info.append(f"Humidity: {attrs['humidity']}%")

            if "cloud_coverage" in attrs:
                weather_info.append(f"Cloud Coverage: {attrs['cloud_coverage']}%")

            # Forecast
            if "forecast" in attrs and attrs["forecast"]:
                forecast = attrs["forecast"]
                if len(forecast) > 0:
                    tomorrow = forecast[0]
                    weather_info.append(f"\nTomorrow's Forecast:")
                    weather_info.append(f"- Condition: {tomorrow.get('condition', 'Unknown')}")
                    if "temperature" in tomorrow:
                        weather_info.append(f"- Temperature: {tomorrow['temperature']}°C")
                    if "precipitation" in tomorrow:
                        weather_info.append(f"- Precipitation: {tomorrow['precipitation']}mm")
                    if "cloud_coverage" in tomorrow:
                        weather_info.append(f"- Cloud Coverage: {tomorrow['cloud_coverage']}%")

        return "\n".join(weather_info) if weather_info else "Weather data unavailable"

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
        self._attr_icon = "mdi:solar-power"

    @property
    def state(self):
        """Return a short state summary."""
        if self.coordinator.data:
            # Extract first sentence or first 250 chars as state
            full_text = self.coordinator.data
            first_sentence = full_text.split('.')[0] if '.' in full_text else full_text[:250]
            return first_sentence[:250] + "..." if len(first_sentence) > 250 else first_sentence
        return "No data"

    @property
    def extra_state_attributes(self):
        """Return the full analysis as an attribute."""
        if self.coordinator.data:
            return {
                "full_analysis": self.coordinator.data,
                "provider": self.coordinator.provider,
                "model": self.coordinator.model,
            }
        return {}