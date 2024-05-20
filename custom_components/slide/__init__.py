"""Component for the Slide API."""

from datetime import timedelta
import logging

import voluptuous as vol

from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPEN,
    STATE_OPENING,
)

from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.reload import async_setup_reload_service

# from homeassistant.helpers.event import async_call_later, async_track_time_interval

from .const import (
    COMPONENT_PLATFORM,
    CONF_API_VERSION,
    CONF_COVER,
    CONF_INVERT_POSITION,
    DEFAULT_OFFSET,
    DEFAULT_RETRY,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)

COVER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PASSWORD, default=""): cv.string,
        vol.Optional(CONF_INVERT_POSITION, default=False): cv.boolean,
        vol.Optional(CONF_API_VERSION, default=2): cv.byte,
    },
    extra=vol.ALLOW_EXTRA,
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(cv.ensure_list, [vol.Any(COVER_SCHEMA)]),
    },
    extra=vol.ALLOW_EXTRA,
)

#################################################################
async def async_setup(hass, config):
    """Set up the local Slide platform."""

    #await async_setup_reload_service(hass, DOMAIN, ["cover"])
    #platform = entity_platform.current_platform.get()
    #hass.services.async_register( DOMAIN, SERVICE_RESTART, async_restart, schema=SERVICE_RESTART_SCHEMA)
    #platform.async_register_entity_service(SERVICE_CALIBRATE, {}, "async_calibrate")

    # Setup reload service
    await async_setup_reload_service(hass, DOMAIN, [DOMAIN])

    if not DOMAIN in config:
        _LOGGER.info("Slide not configured")
        return True

    _LOGGER.debug("Initializing Slide platform")

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][COMPONENT_PLATFORM] = False

    hass.async_create_task(
        async_load_platform(hass, COMPONENT_PLATFORM, DOMAIN, config[DOMAIN], config)
    )

    return True

#################################################################
async def async_reset_platform(hass: HomeAssistant, integration_name: str) -> None:
    """Reload the integration."""
    if DOMAIN not in hass.data:
        _LOGGER.error("Slide not loaded")
        return

    _LOGGER.error("here-in-reset-platform")
