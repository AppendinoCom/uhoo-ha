"""Config flow for uHoo Air Quality integration."""
from __future__ import annotations

import logging

import requests
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_ANDROID_ID, DOMAIN
from .coordinator import fetch_uhoo_data

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("email"): str,
        vol.Required("password"): str,
        vol.Required(CONF_ANDROID_ID): str,
    }
)


async def _validate_credentials(hass: HomeAssistant, data: dict) -> str:
    """Try to authenticate; return a suggested entry title or raise."""
    try:
        devices = await hass.async_add_executor_job(
            fetch_uhoo_data,
            data["email"],
            data["password"],
            data[CONF_ANDROID_ID],
        )
    except requests.exceptions.HTTPError as err:
        _LOGGER.debug("uHoo auth HTTP error: %s", err)
        raise CannotConnect from err
    except requests.exceptions.RequestException as err:
        _LOGGER.debug("uHoo auth connection error: %s", err)
        raise CannotConnect from err
    except Exception as err:  # noqa: BLE001
        _LOGGER.exception("Unexpected error validating uHoo credentials")
        raise UnknownError from err

    if not devices:
        raise CannotConnect

    # Use the first device name as the title, fallback to email
    title = devices[0].get("name") or data["email"]
    return title


class CannotConnect(Exception):
    """Raised when we cannot reach uHoo API or credentials are invalid."""


class UnknownError(Exception):
    """Raised on unexpected errors."""


class UhooConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for uHoo Air Quality."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                title = await _validate_credentials(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except UnknownError:
                errors["base"] = "unknown"
            else:
                # Prevent duplicate entries for the same account
                await self.async_set_unique_id(user_input["email"].lower())
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
