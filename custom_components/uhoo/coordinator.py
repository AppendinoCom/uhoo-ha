"""Data update coordinator for uHoo Air Quality integration."""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta

import requests
from Crypto.Cipher import AES

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_V2, AUTH_BASE, DEFAULT_SCAN_INTERVAL, DOMAIN, SALT

_LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pure functions – run in executor (blocking I/O)
# ---------------------------------------------------------------------------

def _get_client_id(android_id: str) -> str:
    return f"Android_{android_id}_MU"


def _hash_password(uid: str, password: str) -> str:
    raw = f"{uid}{password}{SALT}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _pkcs5_encrypt(code: str, plain_text: str) -> str:
    key = hashlib.md5(code.encode("utf-8")).digest()  # noqa: S324
    cipher = AES.new(key, AES.MODE_ECB)
    raw = plain_text.encode("utf-8")
    pad_len = 16 - (len(raw) % 16)
    encrypted = cipher.encrypt(raw + bytes([pad_len]) * pad_len)
    return encrypted.hex().lower()


def _parse_payload(payload: dict) -> list[dict]:
    """Convert raw API payload to a normalised list of device dicts."""
    devices: list[dict] = []
    for device in payload.get("devices", []):
        sensor_data = device.get("data") or {}
        last_update_ts = sensor_data.get("timestamp")
        last_update_iso: str | None = None
        if isinstance(last_update_ts, (int, float)):
            last_update_iso = datetime.fromtimestamp(last_update_ts).isoformat()

        sensors: dict[str, dict] = {}
        for key, value in sensor_data.items():
            if isinstance(value, dict) and "value" in value and "color" in value:
                sensors[key] = {
                    "value": value.get("value"),
                    "color": value.get("color"),
                }

        devices.append(
            {
                "name": device.get("name") or device.get("serialNumber") or "uHoo",
                "serialNumber": device.get("serialNumber"),
                "last_update_timestamp": last_update_ts,
                "last_update_iso": last_update_iso,
                "sensors": sensors,
            }
        )
    return devices


def fetch_uhoo_data(email: str, password: str, android_id: str) -> list[dict]:
    """Authenticate with uHoo and return parsed device/sensor data.

    This is a *blocking* function – always call via async_add_executor_job.
    """
    client_id = _get_client_id(android_id)

    session = requests.Session()
    session.verify = False  # uHoo API does not always present a valid cert chain
    session.headers.update(
        {
            "Accept": "*/*",
            "User-Agent": "uHoo/9.1 (iPhone; XS; iOS 14.4; Scale/3.00)",
            "Accept-Language": "en-UK;q=1.0",
            "Accept-Encoding": "gzip;q=1.0, compress;q=0.5",
            "Connection": "close",
            "Content-Type": "application/x-www-form-urlencoded",
        }
    )

    # Step 1: GET /user → obtain uId
    resp = session.get(f"{AUTH_BASE}/user", timeout=30)
    resp.raise_for_status()
    uid = resp.json().get("uId")
    if not uid:
        raise UpdateFailed("uHoo auth: could not obtain uId")

    # Step 2: POST /verifyemail → obtain one-time code
    resp = session.post(
        f"{AUTH_BASE}/verifyemail",
        data={"username": email, "clientId": client_id},
        timeout=30,
    )
    resp.raise_for_status()
    verify = resp.json()
    code = verify.get("code")
    login_client_id = verify.get("id") or client_id

    # Step 3: Hash + AES-ECB encrypt password
    hashed = _hash_password(uid, password)
    encrypted = _pkcs5_encrypt(code, hashed)

    # Step 4: POST /login → obtain refreshToken
    resp = session.post(
        f"{AUTH_BASE}/login",
        data={
            "username": email,
            "password": encrypted,
            "clientId": login_client_id,
        },
        timeout=30,
    )
    resp.raise_for_status()
    login = resp.json()
    refresh_token = login.get("refreshToken")
    if not refresh_token:
        raise UpdateFailed("uHoo auth: login succeeded but no refreshToken returned")

    # Step 5: GET /v2/allconsumerdata
    session.headers.update(
        {
            "Authorization": f"Bearer {refresh_token}",
            "Content-Type": "application/json; charset=utf-8",
            "Cache-control": "no-cache",
        }
    )
    resp = session.get(f"{API_V2}/allconsumerdata", timeout=30)
    resp.raise_for_status()

    return _parse_payload(resp.json())


# ---------------------------------------------------------------------------
# Coordinator
# ---------------------------------------------------------------------------

class UhooDataUpdateCoordinator(DataUpdateCoordinator[list[dict]]):
    """Coordinator that authenticates and fetches data from uHoo every N seconds."""

    def __init__(
        self,
        hass: HomeAssistant,
        email: str,
        password: str,
        android_id: str,
    ) -> None:
        self.email = email
        self.password = password
        self.android_id = android_id
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> list[dict]:
        try:
            return await self.hass.async_add_executor_job(
                fetch_uhoo_data,
                self.email,
                self.password,
                self.android_id,
            )
        except UpdateFailed:
            raise
        except requests.exceptions.RequestException as err:
            raise UpdateFailed(f"Network error while fetching uHoo data: {err}") from err
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Unexpected error fetching uHoo data: {err}") from err
