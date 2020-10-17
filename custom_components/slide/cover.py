"""Support for Slide slides."""

import logging
import voluptuous as vol

from goslideapi import GoSlideLocal
from homeassistant.components.cover import (
    ATTR_POSITION,
    DEVICE_CLASS_CURTAIN,
    PLATFORM_SCHEMA,
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPEN,
    STATE_OPENING,
    CoverEntity,
)
from homeassistant.const import ATTR_ID, CONF_HOST, CONF_PASSWORD
import homeassistant.helpers.config_validation as cv

from .const import (
    API_CLOUD,
    API_LOCAL,
    ATTR_TOUCHGO,
    CONF_INVERT_POSITION,
    DEFAULT_OFFSET,
    DOMAIN,
    SLIDES,
    SLIDES_LOCAL,
)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_HOST): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_INVERT_POSITION, default=False): cv.boolean,
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up cover(s) for Slide platform."""

    if discovery_info is None:
        # Local
        if DOMAIN not in hass.data:
            hass.data[DOMAIN] = {}

        if API_LOCAL not in hass.data[DOMAIN]:
            hass.data[DOMAIN][API_LOCAL] = GoSlideLocal()

        await hass.data[DOMAIN][API_LOCAL].slide_add(
            config.get(CONF_HOST), config.get(CONF_PASSWORD)
        )

        slide = await hass.data[DOMAIN][API_LOCAL].slide_info(config.get(CONF_HOST))

        if slide is not None:
            _LOGGER.debug(
                "Setting up Slide Local entity '%s': %s", config.get(CONF_HOST), slide
            )
            async_add_entities(
                [
                    SlideCoverLocal(
                        hass.data[DOMAIN][API_LOCAL],
                        slide,
                        config.get(CONF_HOST),
                        config.get(CONF_INVERT_POSITION),
                    )
                ]
            )
        else:
            _LOGGER.error("Unable to setup Slide Local '%s'", config.get(CONF_HOST))
    else:
        # Cloud
        entities = []

        for slide in hass.data[DOMAIN][SLIDES].values():
            _LOGGER.debug("Setting up Slide Cloud entity: %s", slide)
            entities.append(SlideCoverCloud(hass.data[DOMAIN][API_CLOUD], slide))

        async_add_entities(entities)


class SlideCoverCloud(CoverEntity):
    """Representation of a Slide Cloud API cover."""

    def __init__(self, api, slide):
        """Initialize the cover."""
        self._api = api
        self._slide = slide
        self._id = slide["id"]
        self._unique_id = slide["mac"]
        self._name = slide["name"]
        self._invert = slide["invert"]

    @property
    def unique_id(self):
        """Return the device unique id."""
        return self._unique_id

    @property
    def name(self):
        """Return the device name."""
        return self._name

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        return {ATTR_ID: self._id}

    @property
    def is_opening(self):
        """Return if the cover is opening or not."""
        return self._slide["state"] == STATE_OPENING

    @property
    def is_closing(self):
        """Return if the cover is closing or not."""
        return self._slide["state"] == STATE_CLOSING

    @property
    def is_closed(self):
        """Return None if status is unknown, True if closed, else False."""
        if self._slide["state"] is None:
            return None
        return self._slide["state"] == STATE_CLOSED

    @property
    def available(self):
        """Return False if state is not available."""
        return self._slide["online"]

    @property
    def assumed_state(self):
        """Let HA know the integration is assumed state."""
        return True

    @property
    def device_class(self):
        """Return the device class of the cover."""
        return DEVICE_CLASS_CURTAIN

    @property
    def current_cover_position(self):
        """Return the current position of cover shutter."""
        pos = self._slide["pos"]
        if pos is not None:
            if (1 - pos) <= DEFAULT_OFFSET or pos <= DEFAULT_OFFSET:
                pos = round(pos)
            if not self._invert:
                pos = 1 - pos
            pos = int(pos * 100)
        return pos

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        self._slide["state"] = STATE_OPENING
        await self._api.slide_open(self._id)

    async def async_close_cover(self, **kwargs):
        """Close the cover."""
        self._slide["state"] = STATE_CLOSING
        await self._api.slide_close(self._id)

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        await self._api.slide_stop(self._id)

    async def async_set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        position = kwargs[ATTR_POSITION] / 100
        if not self._invert:
            position = 1 - position

        if self._slide["pos"] is not None:
            if position > self._slide["pos"]:
                self._slide["state"] = STATE_CLOSING
            else:
                self._slide["state"] = STATE_OPENING

        await self._api.slide_set_position(self._id, position)


class SlideCoverLocal(CoverEntity):
    """Representation of a Slide Local API cover."""

    def __init__(self, api, slide, host, invert):
        """Initialize the cover."""
        self._api = api
        self._slide = {}
        self._slide["pos"] = None
        self._slide["state"] = None
        self._slide["online"] = False
        self._slide["touchgo"] = False
        self._unique_id = None

        self.parsedata(slide)

        self._id = host
        self._invert = invert
        self._name = host
        if self._unique_id is None:
            _LOGGER.error(
                "Unable to setup Slide Local '%s', the MAC is missing in the slide response",
                self._id,
            )
            return False

    @property
    def unique_id(self):
        """Return the device unique id."""
        return self._unique_id

    @property
    def name(self):
        """Return the device name."""
        return self._name

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        return {ATTR_ID: self._id, ATTR_TOUCHGO: self._slide["touchgo"]}

    @property
    def is_opening(self):
        """Return if the cover is opening or not."""
        return self._slide["state"] == STATE_OPENING

    @property
    def is_closing(self):
        """Return if the cover is closing or not."""
        return self._slide["state"] == STATE_CLOSING

    @property
    def is_closed(self):
        """Return None if status is unknown, True if closed, else False."""
        if self._slide["state"] is None:
            return None
        return self._slide["state"] == STATE_CLOSED

    @property
    def available(self):
        """Return False if state is not available."""
        return self._slide["online"]

    @property
    def assumed_state(self):
        """Let HA know the integration is assumed state."""
        return True

    @property
    def device_class(self):
        """Return the device class of the cover."""
        return DEVICE_CLASS_CURTAIN

    @property
    def current_cover_position(self):
        """Return the current position of cover shutter."""
        pos = self._slide["pos"]
        if pos is not None:
            if (1 - pos) <= DEFAULT_OFFSET or pos <= DEFAULT_OFFSET:
                pos = round(pos)
            if not self._invert:
                pos = 1 - pos
            pos = int(pos * 100)
        return pos

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        self._slide["state"] = STATE_OPENING
        await self._api.slide_open(self._id)

    async def async_close_cover(self, **kwargs):
        """Close the cover."""
        self._slide["state"] = STATE_CLOSING
        await self._api.slide_close(self._id)

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        await self._api.slide_stop(self._id)

    async def async_set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        position = kwargs[ATTR_POSITION] / 100
        if not self._invert:
            position = 1 - position

        if self._slide["pos"] is not None:
            if position > self._slide["pos"]:
                self._slide["state"] = STATE_CLOSING
            else:
                self._slide["state"] = STATE_OPENING

        await self._api.slide_set_position(self._id, position)

    async def async_update(self):

        slide = await self._api.slide_info(self._id)
        self.parsedata(slide)

    def parsedata(self, slide):

        self._slide["online"] = False

        if slide is None:
            _LOGGER.error("Slide '%s' returned no data (offline?)", self._id)
            return

        if "pos" in slide:
            if self._unique_id is None:
                self._unique_id = slide["slide_id"]
            oldpos = self._slide.get("pos")
            self._slide["online"] = True
            self._slide["touchgo"] = slide["touch_go"]
            self._slide["pos"] = slide["pos"]
            self._slide["pos"] = max(0, min(1, self._slide["pos"]))

            if oldpos is None or oldpos == self._slide["pos"]:
                self._slide["state"] = (
                    STATE_CLOSED
                    if self._slide["pos"] > (1 - DEFAULT_OFFSET)
                    else STATE_OPEN
                )
            elif oldpos < self._slide["pos"]:
                self._slide["state"] = (
                    STATE_CLOSED
                    if self._slide["pos"] >= (1 - DEFAULT_OFFSET)
                    else STATE_CLOSING
                )
            else:
                self._slide["state"] = (
                    STATE_OPEN
                    if self._slide["pos"] <= DEFAULT_OFFSET
                    else STATE_OPENING
                )
        else:
            _LOGGER.error("Slide '%s' has invalid data %s", self._id, str(slide))

        # The format is:
        # {
        #   "slide_id": "slide_300000000000",
        #   "mac": "300000000000",
        #   "board_rev": 1,
        #   "device_name": "",
        #   "zone_name": "",
        #   "curtain_type": 0,
        #   "calib_time": 10239,
        #   "pos": 0.0,
        #   "touch_go": true
        # }
