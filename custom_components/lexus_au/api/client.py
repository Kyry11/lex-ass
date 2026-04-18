"""Async client for Lexus Connected Australia."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode, urlparse, parse_qs

import httpx

from .const import (
    ACCESS_TOKEN_PATH,
    API_BASE_URL,
    APP_LABEL,
    APP_VERSION,
    AUTH_BASE_URL,
    AUTHENTICATE_PATH,
    AUTHORIZE_PATH,
    BRAND,
    CHANNEL,
    CLIENT_ID,
    COMMAND_DOOR_LOCK,
    COMMAND_DOOR_UNLOCK,
    COMMAND_ENGINE_START,
    COMMAND_ENGINE_STOP,
    COMMAND_HAZARD_OFF,
    COMMAND_HAZARD_ON,
    COMMAND_VALUE_OFF,
    COMMAND_VALUE_ON,
    DEVICE_MODEL,
    DEVICE_STATUS_PATH,
    DEVICE_TIMEZONE,
    DEVICE_TYPE,
    LOCALE,
    OPENIDM_BASE_URL,
    OS_NAME,
    OS_VERSION,
    PASSWORD_CHECK_PATH,
    REDIRECT_URI,
    REMOTE_COMMAND_PATH,
    REMOTE_REFRESH_PATH,
    REMOTE_STATUS_PATH,
    TOKEN_BASIC_AUTH,
    USER_AGENT,
    VEHICLE_GUID_PATH,
)
from .exceptions import LexusAUAuthError, LexusAUProtocolError, LexusAURequestError
from .models import LexusAUSnapshot, LexusAUStatus, LexusAUToken, LexusAUVehicleOverview
from .redact import redact_mapping

LOGGER = logging.getLogger(__name__)

_PKCE_CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
_TRIAL_HAZARD_FLASH_DURATION_SECONDS = 1.0


class LexusAUClient:
    """Client for the reverse-engineered Lexus Australia cloud API."""

    def __init__(
        self,
        *,
        username: str,
        password: str,
        vin: str,
        device_id: str,
        api_key: str,
        x_api_key: str,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the Lexus AU client."""
        self._username = username
        self._password = password
        self._vin = vin.upper()
        self._device_id = device_id
        self._api_key = api_key
        self._x_api_key = x_api_key
        self._timeout = timeout

        self._http = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            follow_redirects=False,
            headers={"User-Agent": USER_AGENT},
        )
        self._token: LexusAUToken | None = None
        self._device_registered = False
        self._vehicle_overview = LexusAUVehicleOverview(vin=self._vin)

    async def async_close(self) -> None:
        """Close underlying HTTP resources."""
        await self._http.aclose()

    @property
    def device_id(self) -> str:
        """Return the configured emulated mobile device ID."""
        return self._device_id

    @property
    def vin(self) -> str:
        """Return the configured VIN."""
        return self._vin

    async def async_test_connection(self) -> LexusAUStatus:
        """Validate credentials and status access."""
        return await self.async_get_remote_status()

    async def async_get_snapshot(self) -> LexusAUSnapshot:
        """Fetch the current vehicle snapshot for Home Assistant."""
        status = await self.async_get_remote_status()

        if self._vehicle_overview.raw == {}:
            try:
                self._vehicle_overview = await self.async_get_vehicle_overview()
            except LexusAURequestError:
                LOGGER.debug("Vehicle overview request failed; falling back to VIN only")

        return LexusAUSnapshot(vehicle=self._vehicle_overview, status=status)

    async def async_get_vehicle_overview(self) -> LexusAUVehicleOverview:
        """Fetch vehicle metadata and cache it."""
        payload = await self._async_api_request(
            "GET",
            VEHICLE_GUID_PATH,
            include_vin_header=False,
        )
        self._vehicle_overview = LexusAUVehicleOverview.from_guid_payload(
            payload, self._vin
        )
        return self._vehicle_overview

    async def async_get_remote_status(self) -> LexusAUStatus:
        """Return the last known remote vehicle status."""
        payload = await self._async_api_request(
            "GET",
            REMOTE_STATUS_PATH,
            include_vin_header=True,
        )
        return LexusAUStatus.from_payload(payload)

    async def async_refresh_remote_status(self) -> dict[str, Any]:
        """Ask the vehicle to upload fresh state."""
        await self.async_login()
        return await self._async_api_request(
            "POST",
            REMOTE_REFRESH_PATH,
            include_vin_header=True,
            json_body={
                "guid": self._require_token().subject,
                "vin": self._vin,
                "deviceId": self._device_id,
                "deviceType": DEVICE_TYPE,
            },
        )

    async def async_lock_doors(self) -> dict[str, Any]:
        """Send the confirmed AU door lock command."""
        return await self.async_send_remote_command(
            COMMAND_DOOR_LOCK, value=COMMAND_VALUE_ON
        )

    async def async_unlock_doors(self) -> dict[str, Any]:
        """Send the confirmed AU door unlock command."""
        return await self.async_send_remote_command(
            COMMAND_DOOR_UNLOCK, value=COMMAND_VALUE_OFF
        )

    async def async_start_engine_inferred(self) -> dict[str, Any]:
        """Send an inferred engine start command.

        This is inferred from the cross-region comparison and not yet confirmed
        with an AU capture.
        """
        return await self.async_send_remote_command(
            COMMAND_ENGINE_START, value=COMMAND_VALUE_ON
        )

    async def async_stop_engine_inferred(self) -> dict[str, Any]:
        """Send an inferred engine stop command."""
        return await self.async_send_remote_command(
            COMMAND_ENGINE_STOP, value=COMMAND_VALUE_OFF
        )

    async def async_hazard_on_inferred(self) -> dict[str, Any]:
        """Send an inferred hazards-on command.

        This is intentionally not exposed in Home Assistant until captured.
        """
        return await self.async_send_remote_command(
            COMMAND_HAZARD_ON, value=COMMAND_VALUE_ON
        )

    async def async_hazard_off_inferred(self) -> dict[str, Any]:
        """Send an inferred hazards-off command."""
        return await self.async_send_remote_command(
            COMMAND_HAZARD_OFF, value=COMMAND_VALUE_OFF
        )

    async def async_flash_hazards(self) -> dict[str, Any]:
        """Flash hazards using the confirmed AU/EU-style command pattern."""
        return await self._async_flash_hazards(
            on_command=COMMAND_HAZARD_ON,
            off_command=COMMAND_HAZARD_OFF,
        )

    async def _async_flash_hazards(
        self,
        *,
        on_command: str,
        off_command: str,
        on_value: int | None = None,
        off_value: int | None = None,
    ) -> dict[str, Any]:
        """Send a short on/off hazard sequence."""
        on_response = await self.async_send_remote_command(on_command, value=on_value)
        await asyncio.sleep(_TRIAL_HAZARD_FLASH_DURATION_SECONDS)
        off_response = await self.async_send_remote_command(
            off_command,
            value=off_value,
        )
        return {"on": on_response, "off": off_response}

    async def async_send_remote_command(
        self, command: str, *, value: int | None = None
    ) -> dict[str, Any]:
        """Send a remote vehicle command."""
        body: dict[str, Any] = {"command": command}
        if value is not None:
            body["value"] = value

        return await self._async_api_request(
            "POST",
            REMOTE_COMMAND_PATH,
            include_vin_header=True,
            json_body=body,
        )

    async def async_login(self, *, force: bool = False) -> None:
        """Authenticate and ensure device registration."""
        if not force and self._token and not self._token.should_refresh:
            return

        if not force and self._token and self._token.refresh_token:
            try:
                await self._async_refresh_tokens(self._token.refresh_token)
                await self._async_register_device()
                return
            except LexusAUAuthError as err:
                LOGGER.debug("Refresh-token login failed, falling back to password flow: %s", err)

        await self._async_full_login()
        await self._async_register_device()

    async def _async_full_login(self) -> None:
        """Run the captured callback login + PKCE flow."""
        code_verifier = _generate_pkce_code_verifier()
        code_challenge = _generate_pkce_code_challenge(code_verifier)

        first_auth_id = await self._async_auth_step_1()
        second_auth_id = await self._async_auth_step_2(first_auth_id)
        token_id = await self._async_auth_step_3(second_auth_id)
        code = await self._async_auth_step_4(token_id, code_challenge)
        token_payload = await self._async_auth_step_5(code, code_verifier)

        try:
            access_token = token_payload["access_token"]
            id_token = token_payload["id_token"]
        except KeyError as err:
            raise LexusAUProtocolError("Token payload missing required fields") from err

        refresh_token = token_payload.get("refresh_token")
        expires_in = token_payload.get("expires_in", 3600)
        subject = _decode_jwt_claim(access_token, "sub")

        self._token = LexusAUToken(
            access_token=access_token,
            id_token=id_token,
            refresh_token=refresh_token,
            subject=subject,
            expires_at=datetime.now(UTC) + timedelta(seconds=int(expires_in)),
        )
        self._device_registered = False

        try:
            await self._async_password_check(access_token)
        except LexusAUAuthError as err:
            LOGGER.debug("OpenIDM password check failed but token was accepted: %s", err)

    async def _async_refresh_tokens(self, refresh_token: str) -> None:
        """Attempt an inferred standard OneApp refresh-token grant."""
        headers = self._auth_headers("application/x-www-form-urlencoded")
        headers["Authorization"] = TOKEN_BASIC_AUTH

        body = urlencode(
            {
                "client_id": CLIENT_ID,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            }
        )

        response = await self._http.post(
            f"{AUTH_BASE_URL}{ACCESS_TOKEN_PATH}",
            headers=headers,
            content=body,
        )
        if response.status_code != httpx.codes.OK:
            raise LexusAUAuthError(
                f"Refresh-token exchange failed: {response.status_code} {response.text}"
            )

        token_payload = response.json()
        access_token = token_payload.get("access_token")
        id_token = token_payload.get("id_token", self._token.id_token if self._token else "")
        if not access_token or not id_token:
            raise LexusAUProtocolError("Refresh-token exchange returned incomplete data")

        self._token = LexusAUToken(
            access_token=access_token,
            id_token=id_token,
            refresh_token=token_payload.get("refresh_token", refresh_token),
            subject=_decode_jwt_claim(access_token, "sub"),
            expires_at=datetime.now(UTC)
            + timedelta(seconds=int(token_payload.get("expires_in", 3600))),
        )
        self._device_registered = False

    async def _async_password_check(self, access_token: str) -> None:
        """Replay the post-token OpenIDM password check seen in the app."""
        headers = {
            "Authorization": access_token,
            "X-Openidm-Password": "anonymous",
            "X-Openidm-Username": "anonymous",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Adrum": "isAjax:true",
            "Adrum_1": "isMobile:true",
            "Connection": "close",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        }

        response = await self._http.post(
            f"{OPENIDM_BASE_URL}{PASSWORD_CHECK_PATH}",
            headers=headers,
            content="",
        )
        if response.status_code != httpx.codes.OK:
            raise LexusAUAuthError(
                f"Password service check failed: {response.status_code} {response.text}"
            )

    async def _async_register_device(self) -> None:
        """Register the emulated mobile device with the AU backend."""
        if self._device_registered:
            return

        token = self._require_token()
        headers = self._api_headers(include_vin_header=False)
        headers["Api_key"] = self._api_key
        headers["Content-Type"] = "application/json"

        body = {
            "device_id": self._device_id,
            "device_type": DEVICE_TYPE,
            "label": APP_LABEL,
            "app_version": APP_VERSION,
            "brand": BRAND,
            "device_version": OS_VERSION,
            "device_model": DEVICE_MODEL,
            "GUID": token.subject,
        }

        response = await self._http.post(
            f"{API_BASE_URL}{DEVICE_STATUS_PATH}",
            headers=headers,
            json=body,
        )
        if response.status_code != httpx.codes.OK:
            raise LexusAURequestError(
                f"Device registration failed: {response.status_code} {response.text}"
            )

        self._device_registered = True

    async def _async_api_request(
        self,
        method: str,
        path: str,
        *,
        include_vin_header: bool = False,
        json_body: dict[str, Any] | None = None,
        retry_on_auth_failure: bool = True,
    ) -> dict[str, Any]:
        """Send an authenticated AU telematics request."""
        await self.async_login()

        headers = self._api_headers(include_vin_header=include_vin_header)
        response = await self._http.request(
            method,
            f"{API_BASE_URL}{path}",
            headers=headers,
            json=json_body,
        )

        if response.status_code == httpx.codes.UNAUTHORIZED and retry_on_auth_failure:
            LOGGER.debug("AU API returned 401, forcing a full re-login")
            await self.async_login(force=True)
            return await self._async_api_request(
                method,
                path,
                include_vin_header=include_vin_header,
                json_body=json_body,
                retry_on_auth_failure=False,
            )

        if response.status_code >= 400:
            raise LexusAURequestError(
                f"AU API request failed: {method} {path} -> "
                f"{response.status_code} {response.text}"
            )

        if not response.content:
            return {}

        payload = response.json()
        if isinstance(payload, dict):
            LOGGER.debug("AU API %s %s response: %s", method, path, redact_mapping(payload))
            return payload

        raise LexusAUProtocolError(
            f"Expected an object response from {path}, got {type(payload).__name__}"
        )

    async def _async_auth_step_1(self) -> str:
        """Initialize callback-based auth and obtain the first authId."""
        response = await self._http.post(
            f"{AUTH_BASE_URL}{AUTHENTICATE_PATH}",
            headers=self._auth_headers("application/json"),
            content="",
        )
        payload = _expect_json_response(response, "auth step 1")
        auth_id = payload.get("authId")
        if not isinstance(auth_id, str):
            raise LexusAUProtocolError("Auth step 1 did not return authId")
        return auth_id

    async def _async_auth_step_2(self, auth_id: str) -> str:
        """Submit the username callback payload."""
        payload = {
            "callbacks": [
                {
                    "output": [{"value": "User Name", "name": "prompt"}],
                    "input": [{"value": self._username, "name": "IDToken1"}],
                    "type": "NameCallback",
                    "_id": 0,
                },
                {
                    "output": [
                        {"value": "Prompt", "name": "prompt"},
                        {"value": ["Local", "Google", "Facebook", "Apple"], "name": "choices"},
                        {"value": 0, "name": "defaultChoice"},
                    ],
                    "input": [{"value": 0, "name": "IDToken2"}],
                    "type": "ChoiceCallback",
                    "_id": 1,
                },
            ],
            "authId": auth_id,
        }

        response = await self._http.post(
            f"{AUTH_BASE_URL}{AUTHENTICATE_PATH}",
            headers=self._auth_headers("application/json"),
            json=payload,
        )
        result = _expect_json_response(response, "auth step 2")
        next_auth_id = result.get("authId")
        if not isinstance(next_auth_id, str):
            raise LexusAUProtocolError("Auth step 2 did not return authId")
        return next_auth_id

    async def _async_auth_step_3(self, auth_id: str) -> str:
        """Submit the password callback payload."""
        payload = {
            "authId": auth_id,
            "callbacks": [
                {
                    "type": "PasswordCallback",
                    "output": [{"value": "Password", "name": "prompt"}],
                    "_id": 2,
                    "input": [{"name": "IDToken1", "value": self._password}],
                },
                {
                    "type": "ChoiceCallback",
                    "output": [
                        {"name": "prompt", "value": "Prompt"},
                        {"name": "choices", "value": ["continue", "resetpass"]},
                        {"name": "defaultChoice", "value": 0},
                    ],
                    "_id": 3,
                    "input": [{"name": "IDToken2", "value": 0}],
                },
            ],
        }

        response = await self._http.post(
            f"{AUTH_BASE_URL}{AUTHENTICATE_PATH}",
            headers=self._auth_headers("application/json"),
            json=payload,
        )
        result = _expect_json_response(response, "auth step 3")
        token_id = result.get("tokenId")
        if not isinstance(token_id, str):
            raise LexusAUProtocolError("Auth step 3 did not return tokenId")
        return token_id

    async def _async_auth_step_4(self, token_id: str, code_challenge: str) -> str:
        """Exchange the auth tokenId session for an authorization code."""
        query = urlencode(
            {
                "redirect_uri": REDIRECT_URI,
                "client_id": CLIENT_ID,
                "realm": "/tmca",
                "response_type": "code",
                "code_challenge_method": "S256",
                "code_challenge": code_challenge,
                "scope": "openid profile write",
            }
        )
        headers = self._auth_headers("application/json")
        headers["cookie"] = f"iPlanetDirectoryPro={token_id}"

        response = await self._http.get(
            f"{AUTH_BASE_URL}{AUTHORIZE_PATH}?{query}",
            headers=headers,
        )

        if response.status_code not in {httpx.codes.FOUND, httpx.codes.SEE_OTHER}:
            raise LexusAUAuthError(
                "Authorization step failed: "
                f"{response.status_code} {response.text}"
            )

        location = response.headers.get("location")
        if not location:
            raise LexusAUProtocolError("Authorization step returned no location header")

        parsed = urlparse(location)
        code = parse_qs(parsed.query).get("code", [None])[0]
        if not isinstance(code, str):
            raise LexusAUProtocolError("Authorization redirect did not include code")
        return code

    async def _async_auth_step_5(
        self, code: str, code_verifier: str
    ) -> dict[str, Any]:
        """Exchange the authorization code for tokens."""
        headers = self._auth_headers("application/x-www-form-urlencoded")
        headers["Authorization"] = TOKEN_BASIC_AUTH

        body = urlencode(
            {
                "code": code,
                "grant_type": "authorization_code",
                "code_verifier": code_verifier,
                "redirect_uri": REDIRECT_URI,
                "client_id": CLIENT_ID,
            }
        )

        response = await self._http.post(
            f"{AUTH_BASE_URL}{ACCESS_TOKEN_PATH}",
            headers=headers,
            content=body,
        )
        return _expect_json_response(response, "auth step 5")

    def _require_token(self) -> LexusAUToken:
        """Return the current token or raise."""
        if self._token is None:
            raise LexusAUAuthError("No Lexus AU access token is available")
        return self._token

    def _auth_headers(self, content_type: str) -> dict[str, str]:
        """Headers for auth and token-exchange requests."""
        return {
            "Accept": "*/*",
            "Accept-Api-Version": "resource=2.0, protocol=1.0",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9",
            "Adrum": "isAjax:true",
            "Adrum_1": "isMobile:true",
            "Content-Type": content_type,
            "User-Agent": USER_AGENT,
        }

    def _api_headers(self, *, include_vin_header: bool) -> dict[str, str]:
        """Headers for AU telematics requests."""
        token = self._require_token()
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Adrum": "isAjax:true",
            "Adrum_1": "isMobile:true",
            "Authorization": f"Bearer {token.access_token}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "X-Api-Key": self._x_api_key,
            "X-Appbrand": BRAND,
            "X-Appversion": APP_VERSION,
            "X-Brand": BRAND,
            "X-Channel": CHANNEL,
            "X-Device-Timezone": DEVICE_TIMEZONE,
            "X-Guid": token.subject,
            "X-Locale": LOCALE,
            "X-Osname": OS_NAME,
            "X-Osversion": OS_VERSION,
        }
        if include_vin_header:
            headers["Vin"] = self._vin
        return headers


def generate_device_id() -> str:
    """Generate a stable-looking device ID for config entry creation."""
    return secrets.token_hex(32)


def _generate_pkce_code_verifier(length: int = 128) -> str:
    return "".join(secrets.choice(_PKCE_CHARSET) for _ in range(length))


def _generate_pkce_code_challenge(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("utf-8")


def _decode_jwt_claim(token: str, claim: str) -> str:
    try:
        _, payload_segment, _ = token.split(".", 2)
        padding = "=" * (-len(payload_segment) % 4)
        payload = json.loads(
            base64.urlsafe_b64decode(payload_segment + padding).decode("utf-8")
        )
        value = payload[claim]
    except (KeyError, ValueError, json.JSONDecodeError) as err:
        raise LexusAUProtocolError(f"JWT token is missing claim: {claim}") from err

    if not isinstance(value, str):
        raise LexusAUProtocolError(f"JWT claim {claim} is not a string")
    return value


def _expect_json_response(response: httpx.Response, step_name: str) -> dict[str, Any]:
    if response.status_code >= 400:
        raise LexusAUAuthError(
            f"{step_name} failed: {response.status_code} {response.text}"
        )

    try:
        payload = response.json()
    except ValueError as err:
        raise LexusAUProtocolError(f"{step_name} did not return JSON") from err

    if not isinstance(payload, dict):
        raise LexusAUProtocolError(
            f"{step_name} returned {type(payload).__name__} instead of an object"
        )
    return payload
