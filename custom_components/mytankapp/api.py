"""Async client for the MyTankApp private web API."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import datetime
import json
from typing import Any

from aiohttp import ClientError, ClientResponse, ClientSession, ClientTimeout

from .const import BASE_URL
from .models import MyTankAppAccount, MyTankAppReading, MyTankAppTank


class MyTankAppError(Exception):
    """Base MyTankApp client error."""


class MyTankAppAuthError(MyTankAppError):
    """Raised when authentication fails."""


class MyTankAppConnectionError(MyTankAppError):
    """Raised when MyTankApp cannot be reached."""


class MyTankAppResponseError(MyTankAppError):
    """Raised for an unexpected API response."""


class MyTankAppClient:
    """Read-only MyTankApp API client."""

    def __init__(
        self,
        session: ClientSession,
        username: str,
        password: str,
        *,
        base_url: str = BASE_URL,
    ) -> None:
        self._session = session
        self._username = username.strip()
        self._password = password
        self._base_url = base_url.rstrip("/")
        self._authorization: str | None = None
        self._login_lock = asyncio.Lock()

    async def async_login(self) -> None:
        """Authenticate and retain the returned opaque authorization value."""
        async with self._login_lock:
            offset = datetime.now().astimezone().utcoffset()
            offset_hours = 0 if offset is None else offset.total_seconds() / 3600
            payload = {
                "UserName": self._username,
                "Password": self._password,
                "TimeZoneOffset": offset_hours,
            }
            response = await self._request(
                "POST", "/api/user/login", json_body=payload, authenticated=False
            )
            token = await self._decode_token(response)
            if not token:
                raise MyTankAppAuthError("Login returned no authorization value")
            self._authorization = token

    async def async_get_account(self) -> MyTankAppAccount:
        """Fetch the user/dealer metadata required for normalization."""
        user, dealer = await asyncio.gather(
            self._request_json("GET", "/api/user/getuser"),
            self._request_json("GET", "/api/dealer"),
        )
        if not isinstance(user, Mapping) or not isinstance(dealer, Mapping):
            raise MyTankAppResponseError("Invalid account metadata response")
        units = str(user.get("DefaultUnits") or dealer.get("DefaultUnits") or "Gallons")
        return MyTankAppAccount(
            username=self._username,
            display_name=_optional_text(user.get("Name") or user.get("FirstName")),
            default_units=units.strip(),
            data_source=_optional_text(dealer.get("DataSource")),
        )

    async def async_get_tanks(self) -> dict[str, MyTankAppTank]:
        """Fetch all tanks available to the authenticated account."""
        payload = await self._request_json("GET", "/api/userdevice/devicelist")
        if not isinstance(payload, list):
            raise MyTankAppResponseError("Tank list was not an array")
        tanks: dict[str, MyTankAppTank] = {}
        for raw in payload:
            if not isinstance(raw, dict):
                continue
            tank = MyTankAppTank.from_api(raw)
            if tank is not None:
                tanks[tank.device_id] = tank
        return tanks

    async def async_get_recent_readings(
        self, device_id: str, *, days: int = 60
    ) -> list[MyTankAppReading]:
        """Fetch recent timestamped readings for one tank."""
        payload = await self._request_json(
            "GET",
            "/api/transaction/uniquelist",
            params={"DeviceID": device_id, "Days": days},
        )
        if not isinstance(payload, list):
            raise MyTankAppResponseError("Transaction list was not an array")
        readings = [
            reading
            for raw in payload
            if isinstance(raw, dict)
            and (reading := MyTankAppReading.from_api(raw)) is not None
        ]
        return sorted(readings, key=lambda reading: reading.reported_at, reverse=True)

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        retry_auth: bool = True,
    ) -> Any:
        if self._authorization is None:
            await self.async_login()
        response = await self._request(
            method, path, params=params, authenticated=True
        )
        if response.status in (401, 403) and retry_auth:
            self._authorization = None
            response.release()
            await self.async_login()
            return await self._request_json(
                method, path, params=params, retry_auth=False
            )
        if response.status in (401, 403):
            response.release()
            raise MyTankAppAuthError("Authorization was rejected")
        return await self._decode_json(response)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        authenticated: bool,
    ) -> ClientResponse:
        headers: dict[str, str] = {"Accept": "application/json"}
        if authenticated and self._authorization:
            headers["Authorization"] = self._authorization
        try:
            response = await self._session.request(
                method,
                f"{self._base_url}{path}",
                headers=headers,
                json=json_body,
                params=params,
                timeout=ClientTimeout(total=30),
            )
        except (ClientError, TimeoutError) as err:
            raise MyTankAppConnectionError("Unable to reach MyTankApp") from err

        if response.status in (400, 401, 403) and not authenticated:
            response.release()
            raise MyTankAppAuthError("Invalid username or password")
        if response.status >= 400 and response.status not in (401, 403):
            status = response.status
            response.release()
            if status in (502, 503, 504):
                raise MyTankAppConnectionError(f"MyTankApp returned HTTP {status}")
            raise MyTankAppResponseError(f"MyTankApp returned HTTP {status}")
        return response

    async def _decode_json(self, response: ClientResponse) -> Any:
        try:
            return await response.json(content_type=None)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as err:
            raise MyTankAppResponseError("MyTankApp returned invalid JSON") from err
        finally:
            response.release()

    async def _decode_token(self, response: ClientResponse) -> str:
        try:
            value = await response.json(content_type=None)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            value = await response.text()
        finally:
            response.release()

        if isinstance(value, str):
            return value.strip().strip('"')
        if isinstance(value, Mapping):
            for key in ("Authorization", "authorization", "token", "Token"):
                token = value.get(key)
                if isinstance(token, str):
                    return token.strip()
        raise MyTankAppResponseError("Unsupported login response")


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    result = str(value).strip()
    return result or None
