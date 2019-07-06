"""Support for Go Slide slides."""

import logging

from homeassistant.util import slugify
from homeassistant.components.cover import (
    ENTITY_ID_FORMAT,
    SUPPORT_CLOSE, SUPPORT_OPEN, SUPPORT_SET_POSITION, SUPPORT_STOP, 
    STATE_OPEN, STATE_CLOSED, STATE_OPENING, STATE_CLOSING,
    DEVICE_CLASS_CURTAIN, CoverDevice)
from . import (DOMAIN, SLIDES, API)

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(
        hass, config, async_add_entities, discovery_info=None):
    """Set up cover(s) for Go Slide platform."""

    entities = []

    for key in hass.data[DOMAIN][SLIDES]:
        _LOGGER.debug('Adding GoSlide entity: %s', hass.data[DOMAIN][SLIDES][key])
        entities.append(GoSlideCover(hass, hass.data[DOMAIN][SLIDES][key]['mac'], hass.data[DOMAIN][SLIDES][key]['id'], hass.data[DOMAIN][SLIDES][key]['name']))
    async_add_entities(entities)


class GoSlideCover(CoverDevice):
    """Representation of a Go Slide cover."""

    def __init__(self, hass, mac, id, name):
        """Initialize the cover."""
        self._hass = hass
        self._mac = mac
        self._id = id
        self._name = name

    @property
    def entity_id(self):
        """Return the entity id of the cover."""
        return ENTITY_ID_FORMAT.format(slugify('goslide_' + self._mac.lower()))

    @property
    def name(self):
        """Return the name of the cover."""
        return self._name

    @property
    def state(self):
        """Return the state of the cover."""

        if self._hass.data[DOMAIN][SLIDES][self._mac]['pos'] == None:
            return None
        else:
            pos = int(self._hass.data[DOMAIN][SLIDES][self._mac]['pos'] * 100)
            if pos > 95:
                return STATE_CLOSED
            else:
                return STATE_OPEN

    #@property
    #def available(self):
    #    """Return True if entity is available."""
    #    return self._available

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        return None

    @property
    def assumed_state(self):
        """Let HA know the integration is assumed state."""
        return True

    async def async_close_cover(self, **kwargs):
        """Close the cover."""
        return await self._hass.data[DOMAIN][API].slideclose(self._id)

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        return await self._hass.data[DOMAIN][API].slideopen(self._id)

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        return await self._hass.data[DOMAIN][API].slidestop(self._id)

    async def async_set_cover_position(self, position):
        """Move the cover to a specific position."""
        position = position / 100
        return await self._hass.data[DOMAIN][API].slidesetposition(self._id, position)

    @property
    def current_cover_position(self):
        """Return the current position of cover shutter."""

        if self._hass.data[DOMAIN][SLIDES][self._mac]['pos'] == None:
            pos = None
        else:
            pos = int(self._hass.data[DOMAIN][SLIDES][self._mac]['pos'] * 100)

        return pos

    @property
    def device_class(self):
        return DEVICE_CLASS_CURTAIN

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_OPEN | SUPPORT_CLOSE | \
            SUPPORT_SET_POSITION | SUPPORT_STOP

