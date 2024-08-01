"""Support for Slide slides."""

import logging
from typing import Any

import voluptuous as vol
from goslideapi import GoSlideCloud, GoSlideLocal, goslideapi

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverDeviceClass,
    CoverEntity,
    PLATFORM_SCHEMA,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_ID,
    CONF_HOST,
    CONF_PASSWORD,
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPEN,
    STATE_OPENING,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    API_CLOUD,
    API_LOCAL,
    ATTR_STRENGTH,
    ATTR_TOUCHGO,
    CONF_API_VERSION,
    CONF_INVERT_POSITION,
    DEFAULT_OFFSET,
    DOMAIN,
    SERVICE_CALIBRATE,
    SERVICE_STRENGTH,
    SERVICE_TOUCHGO,
    SLIDES,
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_HOST): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_INVERT_POSITION, default=False): cv.boolean,
        vol.Optional(CONF_API_VERSION, default=2): cv.byte,
    },
    extra=vol.ALLOW_EXTRA,
)

SERVICE_SCHEMA_CALIBRATE = {
    vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
}

SERVICE_SCHEMA_STRENGTH = {
    vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
    vol.Required(ATTR_STRENGTH): cv.string,
}

SERVICE_SCHEMA_TOUCHGO = {
    vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
    vol.Required(ATTR_TOUCHGO): cv.boolean,
}

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up cover(s) for Slide platform."""

    _LOGGER.debug("Initializing Slide cover(s)")

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_CALIBRATE,
        SERVICE_SCHEMA_CALIBRATE,
        "async_calibrate",
    )

    platform.async_register_entity_service(
        SERVICE_STRENGTH,
        SERVICE_SCHEMA_STRENGTH,
        "async_strength",
    )

    platform.async_register_entity_service(
        SERVICE_TOUCHGO,
        SERVICE_SCHEMA_TOUCHGO,
        "async_touchgo",
    )

    if discovery_info is None:
        # Local
        if DOMAIN not in hass.data:
            hass.data[DOMAIN] = {}

        cover = config

        if API_LOCAL not in hass.data[DOMAIN]:
            hass.data[DOMAIN][API_LOCAL] = GoSlideLocal()

        _LOGGER.debug(
            "Trying to setup Slide '%s', config=%s",
            cover[CONF_HOST],
            str(cover),
        )

        await hass.data[DOMAIN][API_LOCAL].slide_add(
            cover[CONF_HOST], cover[CONF_PASSWORD], cover[CONF_API_VERSION]
        )

        try:
            slide_info = await hass.data[DOMAIN][API_LOCAL].slide_info(cover[CONF_HOST])
        except (goslideapi.ClientConnectionError, goslideapi.ClientTimeoutError) as err:
            # https://developers.home-assistant.io/docs/integration_setup_failures/
            raise PlatformNotReady(
                f"Unable to setup Slide '{cover[CONF_HOST]}': {err}"
            ) from err

        if slide_info is not None:
            _LOGGER.debug("Setup Slide '%s' successful", cover[CONF_HOST])

            async_add_entities(
                [
                    SlideCoverLocal(
                        hass.data[DOMAIN][API_LOCAL],
                        slide_info,
                        cover[CONF_HOST],
                        cover[CONF_INVERT_POSITION],
                    )
                ]
            )
        else:
            _LOGGER.error("Unable to setup Slide '%s'", cover[CONF_HOST])
    else:
        # Cloud
        entities = []

        for slide in hass.data[DOMAIN][SLIDES].values():
            _LOGGER.debug("Setting up Slide Cloud entity: %s", slide)
            entities.append(SlideCoverCloud(hass.data[DOMAIN][API_CLOUD], slide))

        async_add_entities(entities)


class SlideCoverCloud(CoverEntity):
    """Representation of a Slide Cloud API cover."""

    _attr_assumed_state = True
    _attr_device_class = CoverDeviceClass.CURTAIN

    def __init__(self, api: GoSlideCloud, slide: dict[str, Any]):
        """Initialize the cover."""
        self._api = api
        self._slide = slide
        self._id = slide["id"]
        self._unique_id = slide["mac"]
        self._name = slide["name"]
        self._invert = slide["invert"]

    @property
    def unique_id(self) -> str | None:
        """Return the device unique id."""
        return self._unique_id

    @property
    def name(self) -> str:
        """Return the device name."""
        return self._name

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return device specific state attributes."""
        return {ATTR_ID: self._id}

    @property
    def is_opening(self) -> bool:
        """Return if the cover is opening or not."""
        return self._slide["state"] == STATE_OPENING

    @property
    def is_closing(self) -> bool:
        """Return if the cover is closing or not."""
        return self._slide["state"] == STATE_CLOSING

    @property
    def is_closed(self) -> bool:
        """Return None if status is unknown, True if closed, else False."""
        if self._slide["state"] is None:
            return None
        return self._slide["state"] == STATE_CLOSED

    @property
    def available(self) -> bool:
        """Return False if state is not available."""
        return self._slide["online"]

    @property
    def current_cover_position(self) -> int | None:
        """Return the current position of cover shutter."""
        pos = self._slide["pos"]
        if pos is not None:
            if (1 - pos) <= DEFAULT_OFFSET or pos <= DEFAULT_OFFSET:
                pos = round(pos)
            if not self._invert:
                pos = 1 - pos
            pos = int(pos * 100)
        return pos

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        self._slide["state"] = STATE_OPENING
        await self._api.slide_open(self._id)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        self._slide["state"] = STATE_CLOSING
        await self._api.slide_close(self._id)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        await self._api.slide_stop(self._id)

    async def async_set_cover_position(self, **kwargs: Any) -> None:
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

    async def async_calibrate(self) -> None:
        """Calibrate the Slide."""
        await self._api.slide_calibrate(self._id)


class SlideCoverLocal(CoverEntity):
    """Representation of a Slide Local API cover."""

    _attr_assumed_state = True
    _attr_device_class = CoverDeviceClass.CURTAIN

    def __init__(
        self, api: GoSlideLocal, slide_info: dict[str, Any], host: str, invert: bool
    ) -> None:
        """Initialize the cover."""
        self._api = api
        self._slide: dict[str, Any] = {}
        self._slide["pos"] = None
        self._slide["state"] = None
        self._slide["online"] = False
        self._slide["touchgo"] = False
        self._unique_id = None

        self.parsedata(slide_info)

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
    def unique_id(self) -> str | None:
        """Return the device unique id."""
        return self._unique_id

    @property
    def name(self) -> str:
        """Return the device name."""
        return self._name

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return device specific state attributes."""
        return {ATTR_ID: self._id, ATTR_TOUCHGO: self._slide["touchgo"]}

    @property
    def is_opening(self) -> bool:
        """Return if the cover is opening or not."""
        return self._slide["state"] == STATE_OPENING

    @property
    def is_closing(self) -> bool:
        """Return if the cover is closing or not."""
        return self._slide["state"] == STATE_CLOSING

    @property
    def is_closed(self) -> bool:
        """Return None if status is unknown, True if closed, else False."""
        if self._slide["state"] is None:
            return None
        return self._slide["state"] == STATE_CLOSED

    @property
    def available(self) -> bool:
        """Return False if state is not available."""
        return self._slide["online"]

    @property
    def current_cover_position(self) -> int | None:
        """Return the current position of cover shutter."""
        pos = self._slide["pos"]
        if pos is not None:
            if (1 - pos) <= DEFAULT_OFFSET or pos <= DEFAULT_OFFSET:
                pos = round(pos)
            if not self._invert:
                pos = 1 - pos
            pos = int(pos * 100)
        return pos

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        self._slide["state"] = STATE_OPENING
        await self._api.slide_open(self._id)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        self._slide["state"] = STATE_CLOSING
        await self._api.slide_close(self._id)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        await self._api.slide_stop(self._id)

    async def async_set_cover_position(self, **kwargs: Any) -> None:
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

    async def async_update(self) -> None:
        """Update slide information."""

        slide_info = None

        try:
            slide_info = await self._api.slide_info(self._id)
            self.parsedata(slide_info)
        except (goslideapi.ClientConnectionError, goslideapi.ClientTimeoutError) as err:
            # Set Slide to unavailable
            self._slide["online"] = False

            _LOGGER.error(
                "Unable to get information from Slide '%s': %s",
                self._id,
                str(err),
            )

    def parsedata(self, slide_info) -> None:

        self._slide["online"] = False

        if slide_info is None:
            _LOGGER.error("Slide '%s' returned no data (offline?)", self._id)
            return

        if "pos" in slide_info:
            if self._unique_id is None:
                self._unique_id = slide_info["slide_id"]
            oldpos = self._slide.get("pos")
            self._slide["online"] = True
            self._slide["touchgo"] = slide_info["touch_go"]
            self._slide["pos"] = slide_info["pos"]
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
            _LOGGER.error("Slide '%s' has invalid data %s", self._id, str(slide_info))

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

    async def async_calibrate(self) -> None:
        """Calibrate the Slide."""
        await self._api.slide_calibrate(self._id)

    async def async_strength(self, **kwargs) -> None:
        """Motor strength for the Slide. Value can be light, medium or strong."""

        if kwargs[ATTR_STRENGTH] == "light":
            await self._api.slide_set_motor_strength(
                self._id, maxcurrent=900, calib_current=850
            )
        elif kwargs[ATTR_STRENGTH] == "medium":
            await self._api.slide_set_motor_strength(
                self._id, maxcurrent=1250, calib_current=1200
            )
        elif kwargs[ATTR_STRENGTH] == "strong":
            await self._api.slide_set_motor_strength(
                self._id, maxcurrent=1500, calib_current=1450
            )
        else:
            _LOGGER.error(
                "Slide '%s' length '%s' is invalid. Only 'light', 'medium' or 'string' is supported",
                self._id,
                kwargs[ATTR_STRENGTH],
            )

    async def async_touchgo(self, **kwargs) -> None:
        """TouchGo the Slide."""
        await self._api.slide_set_touchgo(self._id, kwargs[ATTR_TOUCHGO])
