# Home-Assistant Custom Component for Slide

This custom component home-assistant (http://www.home-assistant.io) can control the Slide (https://slide.store).

## Slide

### Requirements
- Home Assistant 0.94+

### Installation

- Copy directory `slide` `<config dir>/custom_components` directory.
- Configure with config below.
- Restart Home-Assistant.

### Usage
To use this component in your installation for the Cloud API, add the following to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry

slide:
  username: slide@somedomain.com
  password: secret
  scan_interval: 30
  invert_position: false
```

Configuration variables:

- **username** (*Required*): The e-mail used to register your account with api.goslide.io, with your iPhone/Android App
- **password** (*Required*): The password of your account with api.goslide.io
- **scan_interval** (*Optional*): Number of seconds between polls (default = 30)
- **invert_position** (*Optional*): If the position should be inverted e.g. 0% -> 100% and 100% -> 0% (default = false)

To use this component in your installation With the Local API, add the following to your `configuration.yaml` file for each Slide:

```yaml
# Example yaml entry

cover:
  - platform: slide
    host: 192.168.1.1
    password: 12345678
```

Configuration variables:

- **host** (*Required*): The IP address or hostname of your local Slide
- **password** (*Required*): The device code of your Slide (inside of the Slide or in the box, length is 8 characters)
- **invert_position** (*Optional*): If the position should be inverted e.g. 0% -> 100% and 100% -> 0% (default = false)

### Debugging

It is possible to debug the Slide component and API library, this can be done by adding the following lines to the `configuration.yaml` file:

```yaml
logger:
  logs:
    goslideapi: debug
    custom_components.slide: debug
    homeassistant.components.slide: debug
```

### TO DO

- Add calibration as a service

