# Home-Assistant Custom Component for Go Slide

My custom component home-assistant (http://www.home-assistant.io) to control the Go Slide (https://nl.goslide.io). At this moment the component only support the Cloud option, because the local API hasn't been released yet (it planned to be included when released).

## Go Slide

### Installation

- Copy directory `goslide` `<config dir>/custom_components` directory.
- Configure with config below.
- Restart Home-Assistant.

### Usage
To use this component in your installation, add the following to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry

goslide:
  username: goslide@somedomain.com
  password: secret
  scan_interval: 30
```

Configuration variables:

- **username** (*Required*): The e-mail used to register your account with api.goslide.io, with your iPhone/Android App
- **password** (*Required*): The password of your account with api.goslide.io
- **scan_interval** (*Optional*): Number of seconds between polls. (default = 30)

