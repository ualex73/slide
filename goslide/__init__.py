"""Component for the Go Slide API."""

import logging
import datetime

import voluptuous as vol

from homeassistant.const import (CONF_USERNAME, CONF_PASSWORD, CONF_SCAN_INTERVAL)
from homeassistant.helpers import discovery
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'goslide'
COMPONENT = 'cover'
API = 'api'
SLIDES = 'slides'

DEFAULT_SCAN_INTERVAL = datetime.timedelta(seconds=10)

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
        
        result = await hass.data[DOMAIN][API].slidesoverview()

        if result == None:
            _LOGGER.error('GoSlide API does not work or returned an error')
            return

        """Set the pos to None first, otherwise we don't know if the API fails."""
        for key in hass.data[DOMAIN][SLIDES]:
            hass.data[DOMAIN][SLIDES][key]['pos'] = None

        for slide in result:
            if 'device_id' in slide:
                """Found a valid slide entry, remove 'slide_' from the id, we keep the MAC..."""
                uid = slide['device_id'].replace('slide_', '')
                if uid not in hass.data[DOMAIN][SLIDES]:
                    hass.data[DOMAIN][SLIDES][uid] = {}
                hass.data[DOMAIN][SLIDES][uid]['mac'] = uid
                hass.data[DOMAIN][SLIDES][uid]['id'] = slide['id']
                hass.data[DOMAIN][SLIDES][uid]['name'] = slide['device_name']
                hass.data[DOMAIN][SLIDES][uid]['pos'] = slide['device_info']['pos']
                
            else:
                _LOGGER.error('Found invalid goslide entry, "device_id" is missing') 

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

    if result == None:
        _LOGGER.error('Unknown error')
        return False
    elif result == False:
        _LOGGER.error('Authentication failed')
        return False

    await update_slides(None)

    hass.async_create_task(
        discovery.async_load_platform(hass, COMPONENT, DOMAIN, {}, config))

    async_track_time_interval(hass, update_slides, scaninterval)

    return True

