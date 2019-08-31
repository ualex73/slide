# Home-Assistant Custom Component for Slide

*** NOTE - The component has been renamed from 'goslide' to 'slide' on request of 'Innovation in Motion' ***
*** NOTE - Configuration items timeout and retry are removed ***

This custom component home-assistant (http://www.home-assistant.io) can control the Slide (https://nl.goslide.io). At this moment the component only support the Cloud option, because the local API hasn't been released yet (it planned to be included when released).

## Slide

### Requirements
- Home Assistant 0.94+

### Installation

- Copy directory `goslide` `<config dir>/custom_components` directory.
- Configure with config below.
- Restart Home-Assistant.

### Usage
To use this component in your installation, add the following to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry

slide:
  username: slide@somedomain.com
  password: secret
  scan_interval: 30
```

Configuration variables:

- **username** (*Required*): The e-mail used to register your account with api.goslide.io, with your iPhone/Android App
- **password** (*Required*): The password of your account with api.goslide.io
- **scan_interval** (*Optional*): Number of seconds between polls. (default = 30)

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

- Add local API support, when released

