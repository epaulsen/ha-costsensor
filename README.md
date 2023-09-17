# Cost sensor

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]


[![Community Forum][forum-shield]][forum]

_Creates a new platform to track cost of individual sensors._

**This integration will set up the following platforms.**

Platform | Description
-- | --
`cost` | Tracks cost for a sensor based on a tariff.

## Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new folder called `cost`.
1. Download _all_ the files from the `custom_components/cost/` directory (folder) in this repository.
1. Place the files you downloaded in the new directory (folder) you created.
1. Restart Home Assistant
1. Add a new sensor to your yaml config, see examples and schema below.

## Sensor schema

| Name | Type | Default | Since | Description |
|------|------|---------|-------|-------------|
| name | string | **required** | v0.0.1 | Name of sensor |
| source | entity | **required** | v0.0.1 | Increasing sensor, for example energy sensor |
| tariff | entity | **required** | v0.0.1 | Sensor for cost per unit of source sensor |
| unit_of_measurement | string | **required** | v0.0.1 | Output unit of measurement for this sensor |
| cron | string | optional | v0.0.1 | How often sensor resets.  Allowed values are hourly, daily, weekly, monthly or yearly. |

If `cron` does not have any value, the sensor will never reset it's value, and can that way be used to keep
track of lifetime costs.

Example:
```yaml
  - platform: cost
    source: sensor.your_energy_sensor_here_kwh
    tariff: sensor.power_cost_usd_kwh
    name: "Cost of something per hour"
    unit_of_measurement: "USD"
    cron: hourly
```
The above yaml will create a new sensor that will track cost for sensor given in `source`.
Source sensor should be a sensor that increases it's value over time, for example an energy sensor(kWh, m^3 and so on).
The cost sensor is calculated based on delta values for the `source` sensor multiplied with the tariff sensor.
Tariff sensor input is a sensor that tracks cost per unit of source sensor, for example electricity cost per kWh.

**Caution**
The platform entity does no validation of sensor types and units, you are responsible for ensuring that the tariff sensors unit_of_measurement matches the delta values produced by the source sensor.

<!---->

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[integration_blueprint]: https://github.com/ludeeus/integration_blueprint
[buymecoffee]: https://www.buymeacoffee.com/epaulsen
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/epaulsen/ha-costsensor.svg?style=for-the-badge
[commits]: https://github.com/epaulsen/ha-costsensor/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/epaulsen/ha-costsensor.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/epaulsen/ha-costsensor.svg?style=for-the-badge
[releases]: https://github.com/epaulsen/ha-costsensor/releases
