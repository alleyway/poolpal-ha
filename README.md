# PoolPal

Home Assistant custom integration that adds a calibrated sensor (cm) to an existing MQTT device.

## How it works

1. Install via HACS as a custom repository
2. Add the PoolPal integration via Settings → Devices & Services → Add Integration
3. **Step 1**: Select a manufacturer to filter the device list
4. **Step 2**: Choose an existing device from your HA device registry
5. **Step 3**: Enter the MQTT topic for raw data and a calibration factor

The integration subscribes to the MQTT topic and creates a sensor entity on the selected device:

```
calibrated_value (cm) = mqtt_raw_value × calibration_factor
```

## Example

If a device publishes `150` on topic `pool/pump/flow_raw` and you set a calibration factor of `0.1`, the sensor will report `15 cm`.

## Installation

1. Add this repository to HACS as a custom integration repository
2. Install PoolPal from HACS
3. Restart Home Assistant
4. Go to Settings → Devices & Services → Add Integration → PoolPal
