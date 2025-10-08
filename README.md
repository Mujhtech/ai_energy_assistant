# AI Energy Assistant

## Example card

```
type: custom:mushroom-template-card
entity: sensor.ai_energy_prediction
primary: AI Energy Assistant
secondary: "{{ states('sensor.ai_energy_prediction') }}"
icon: mdi:robot
icon_color: purple
multiline_secondary: true
```