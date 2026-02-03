"""Frontend for Solar Router integration."""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

FRONTEND_SCRIPT_URL = "/solar_router/solar-router-flow-card.js"


async def async_setup_frontend(hass: HomeAssistant) -> None:
    """Set up the Solar Router frontend resources."""
    # Get the path to the frontend files
    www_path = Path(__file__).parent.parent.parent / "www"

    if www_path.exists():
        # Register the static path
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    "/solar_router",
                    str(www_path),
                    cache_headers=False,
                )
            ]
        )

        # Add the JavaScript file to the frontend
        add_extra_js_url(hass, FRONTEND_SCRIPT_URL)

        _LOGGER.info("Solar Router frontend resources registered")
    else:
        _LOGGER.warning("Solar Router www folder not found at %s", www_path)
