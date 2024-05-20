# Home-Assistant Custom Component for Slide

This custom component home-assistant (http://www.home-assistant.io) can control the Slide (https://slide.store).

## Slide

### Requirements
- Home Assistant 0.94+

### Custom Component vs Integration

The `slide` integration is included into the Home Assistant and it is based on this custom component. The custom component will contain newer features then the standard integrated one, until it is hopefully merged into Home Assistant. At this moment the local API will only be available in the custom component. Also Home Assistant dictates that integrations should move to the GUI integration instead of the YAML file, which is difficult/impossible with the local API configuration.

### Installation

- Copy directory `slide` `<config dir>/custom_components` directory.
- Configure with config below.
- Restart Home-Assistant.

### Switch between Cloud and Local API

By default the Slide connects to the cloud API, but it is possible to use the local API too (only 1 of them can be active). To switch between the cloud and local API, do the following step:

- Press the reset button 2x

LED flashes 5x fast: cloud API disabled, local API enabled  
LED flashes 2x slow: local API disabled, cloud API enabled

NOTE: If a new Slide is installed, it could be the firmware is too old. Configure it via the cloud API and wait a few days (or contact Slide support to push a newer firmware).

![alt text](https://github.com/ualex73/slide/blob/master/screenshots/slide-bottom.png?raw=true "Screenshot Slide Bottom")

### Usage
To use this component in your installation for the Cloud API, add the following to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry

slide:
  username: slide@somedomain.com
  password: secret
  scan_interval: 30
  invert_position: False
  verify_ssl: True
```

Configuration variables:

- **username** (*Required*): The e-mail used to register your account with api.goslide.io, with your iPhone/Android App
- **password** (*Required*): The password of your account with api.goslide.io
- **scan_interval** (*Optional*): Number of seconds between polls (default = 30)
- **invert_position** (*Optional*): If the position should be inverted e.g. 0% -> 100% and 100% -> 0% (default = False)
- **verify_ssl** (*Optional*): If the SSL certificate should be checked (default = True)

To use this component in your installation With the Local API, add the following to your `configuration.yaml` file for each Slide:

```yaml
# Example yaml entry

cover:
  - platform: slide
    host: 192.168.1.1
    password: 12345678
    api_version: 2
```

Configuration variables:

- **host** (*Required*): The IP address or hostname of your local Slide
- **password** (*Required*): The device code of your Slide (inside of the Slide or in the box, length is 8 characters). NOTE: With *api_version: 2* you can fill in anything here, it is not used by the local API
- **invert_position** (*Optional*): If the position should be inverted e.g. 0% -> 100% and 100% -> 0% (default = False)
- **api_version** (*Optional*): 1 or 2. 1 is pre Aug-2023 firmware. 2 is for Aug-2023 or later (default = 2)

### Services

- slide.calibrate - It is possible to call this service to calibrate your Slide

### Debugging

It is possible to debug the Slide component and API library, this can be done by adding the following lines to the `configuration.yaml` file:

```yaml
logger:
  logs:
    goslideapi: debug
    custom_components.slide: debug
    homeassistant.components.slide: debug
```
