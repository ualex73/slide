"""Component for the Go Slide API."""

import logging
from datetime import timedelta

import voluptuous as vol

from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, \
                                CONF_SCAN_INTERVAL
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.event import async_track_time_interval
from .const import (DOMAIN, SLIDES, API, COMPONENT)

_LOGGER = logging.getLogger(__name__)

DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL):
            cv.time_period,
    })
}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass, config):
    """Set up the GoSlide platform."""
    async def update_slides(now):
        """Update slide information."""
        result = await hass.data[DOMAIN][API].slidesoverview()

        if result is None:
            _LOGGER.error("GoSlide API does not work or returned an error")
            return

        if result:
            _LOGGER.debug("GoSlide API returned %d slide(s)", len(result))
        else:
            _LOGGER.warning("GoSlide API returned 0 slides")

        for key in hass.data[DOMAIN][SLIDES]:
            hass.data[DOMAIN][SLIDES][key]['pos'] = None

        for slide in result:
            if 'device_id' in slide:
                uid = slide['device_id'].replace('slide_', '')
                slidenew = {}
                slidenew['mac'] = uid
                slidenew['id'] = slide['id']
                slidenew['name'] = slide['device_name']
                slidenew['pos'] = slide['device_info']['pos']
                hass.data[DOMAIN][SLIDES][uid] = slidenew

                if hass.data[DOMAIN][SLIDES][uid]['pos'] is not None:
                    if hass.data[DOMAIN][SLIDES][uid]['pos'] < 0:
                        hass.data[DOMAIN][SLIDES][uid]['pos'] = 0
                    elif hass.data[DOMAIN][SLIDES][uid]['pos'] > 1:
                        hass.data[DOMAIN][SLIDES][uid]['pos'] = 1
            else:
                _LOGGER.error("Found invalid GoSlide entry, 'device_id' is "
                              "missing. Entry=%s", slide)

    if DOMAIN not in config:
        return True

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][SLIDES] = {}

    username = config[DOMAIN][CONF_USERNAME]
    password = config[DOMAIN][CONF_PASSWORD]
    scaninterval = config[DOMAIN][CONF_SCAN_INTERVAL]

    from goslideapi import GoSlideCloud

    hass.data[DOMAIN][API] = GoSlideCloud(username, password)

    result = await hass.data[DOMAIN][API].login()

    if result is None:
        _LOGGER.error("GoSlide API returned unknown error during "
                      "authentication")
        return False
    elif result is False:
        _LOGGER.error("GoSlide authentication failed, check "
                      "username/password")
        return False

    await update_slides(None)

    hass.async_create_task(
        async_load_platform(hass, COMPONENT, DOMAIN, {}, config))

    async_track_time_interval(hass, update_slides, scaninterval)

    return True
