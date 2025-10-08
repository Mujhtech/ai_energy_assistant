# AI Energy Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

An intelligent Home Assistant integration that uses AI to analyze your solar energy system data and provide insights and predictions for your energy usage.

## Features

- 🤖 AI-powered energy analysis using OpenAI or Google Gemini
- ☀️ Solar energy monitoring and predictions
- 🔋 Battery state of charge tracking
- 📊 Daily energy usage insights
- 🔮 Next-day energy predictions
- ⚡ Automatic hourly updates

## Supported AI Providers

- **OpenAI** (GPT-4o-mini)
- **Google Gemini** (Gemini Pro)

## Installation

### HACS Installation (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add `https://github.com/mujhtech/ai_energy_assistant` as a custom repository
6. Select "Integration" as the category
7. Click "Add"
8. Search for "AI Energy Assistant" and install

### Manual Installation

1. Copy the `custom_components/ai_energy_assistant` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant
3. Go to Configuration → Integrations
4. Click "+ Add Integration"
5. Search for "AI Energy Assistant"

## Configuration

1. Select your AI provider (OpenAI or Gemini)
2. Enter your API key:
   - For OpenAI: Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
   - For Gemini: Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

## Usage

Once configured, the integration creates a sensor entity:

- `sensor.ai_energy_prediction` - Displays AI-generated analysis and predictions

### Example Dashboard Cards

#### Simple Summary Card (Mushroom)

```yaml
type: custom:mushroom-template-card
entity: sensor.ai_energy_prediction
primary: AI Energy Assistant
secondary: "{{ states('sensor.ai_energy_prediction') }}"
icon: mdi:solar-power
icon_color: orange
multiline_secondary: true
```

#### Detailed Analysis Card

```yaml
type: markdown
content: |
  ## 🌞 AI Energy Assistant

  **Summary:** {{ states('sensor.ai_energy_prediction') }}

  ### 📊 Today's Performance
  {{ state_attr('sensor.ai_energy_prediction', 'today_performance') }}

  ### 📈 Trends
  {{ state_attr('sensor.ai_energy_prediction', 'trends') }}

  ### 🔮 Tomorrow's Prediction
  {{ state_attr('sensor.ai_energy_prediction', 'tomorrow_prediction') }}
  *Confidence: {{ state_attr('sensor.ai_energy_prediction', 'confidence') }}*

  ### 💡 Recommendation
  {{ state_attr('sensor.ai_energy_prediction', 'recommendation') }}
```

#### Advanced: Multiple Cards

```yaml
type: vertical-stack
cards:
  - type: custom:mushroom-template-card
    entity: sensor.ai_energy_prediction
    primary: Energy Summary
    secondary: "{{ states('sensor.ai_energy_prediction') }}"
    icon: mdi:solar-power
    icon_color: orange

  - type: markdown
    content: |
      **Tomorrow:** {{ state_attr('sensor.ai_energy_prediction', 'tomorrow_prediction') }}

      **💡 Tip:** {{ state_attr('sensor.ai_energy_prediction', 'recommendation') }}
```

### Available Attributes

The sensor provides the following attributes:

- `summary` - Brief overview (displayed as sensor state, max 250 chars)
- `today_performance` - Analysis of today's performance vs. past week
- `trends` - Key trends and patterns observed
- `efficiency` - System efficiency assessment
- `tomorrow_prediction` - Prediction for tomorrow
- `confidence` - Prediction confidence level (high/medium/low)
- `recommendation` - Actionable recommendation
- `provider` - AI provider used (openai/gemini)
- `model` - AI model used
- `full_data` - Complete JSON response for advanced automation

## Monitored Sensors

The integration monitors the following Growatt solar system sensors (customize these in `sensor.py` for your setup):

- `sensor.growatt_solar_energy_today` - Daily solar energy production
- `sensor.growatt_load_percentage` - Current load percentage
- `sensor.growatt_battery_soc` - Battery state of charge

## Data Update Frequency

The integration polls the AI service once per hour to analyze your energy data and provide updated predictions.

## Requirements

- Home Assistant 2023.1.0 or newer
- An API key from OpenAI or Google Gemini
- Solar energy sensors configured in Home Assistant

## Privacy & Data

- Your sensor data is sent to the selected AI provider for analysis
- No data is stored by this integration beyond the latest prediction
- Review the privacy policies of your chosen AI provider:
  - [OpenAI Privacy Policy](https://openai.com/privacy)
  - [Google Privacy Policy](https://policies.google.com/privacy)

## Support

For issues, feature requests, or contributions, please visit the [GitHub repository](https://github.com/mujhtech/ai_energy_assistant).

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This integration is not affiliated with OpenAI, Google, Growatt, or Home Assistant. Use at your own risk.
