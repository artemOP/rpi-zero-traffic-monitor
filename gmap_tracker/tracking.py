import asyncio
import json
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from types import TracebackType
from typing import Any, Mapping, Self, Sequence
from zoneinfo import ZoneInfo

import aiohttp
from _types.enums import ExtraComputation, RouteTravelMode, RoutingPreference
from _types.models import LatLng, Location, Request, RouteModifiers, Waypoint
from adafruit_ssd1305 import SSD1305, SSD1305_128x32, constants
from tasks import loop


class Tracker:
    _session: aiohttp.ClientSession
    _request_body: Request
    _display: SSD1305
    locations: dict[str, Any]
    headers: dict[str, str]
    task_running: asyncio.Event

    def __init__(self, locations_path: Path, headers_path: Path):
        self._locations_path = locations_path
        self._headers_path = headers_path

    async def __aenter__(self) -> Self:
        self._session = aiohttp.ClientSession()
        self.task_running = asyncio.Event()
        self._display = SSD1305_128x32().__enter__()
        self._display.font = self._display.font_folder_path / "small_6x8"

        with open(self._locations_path, "r") as f:
            self.locations = json.load(f)
        with open(self._headers_path, "r") as f:
            self.headers = json.load(f)

        self._build_request_body()
        self.task.start()
        self.task_running.set()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        self.task.cancel()
        await self._session.close()
        self._display.__exit__(None, None, None)
        if exc_type in (KeyboardInterrupt, asyncio.CancelledError):
            return True
        return False

    def _build_request_body(self) -> Request:

        def latlng(obj: dict) -> LatLng:
            return {"latitude": obj["latitude"], "longitude": obj["longitude"]}

        def location(obj: dict) -> Location:
            return {"latLng": latlng(obj)}

        origin: Waypoint = {"location": location(self.locations["origin"])}
        destination: Waypoint = {"location": location(self.locations["destination"])}

        intermediates: list[Waypoint] = []
        for wp in self.locations.get("intermediates", []):
            intermediate: Waypoint = {
                "via": wp.get("via", False),
                "location": location(wp["location"]),
            }
            intermediates.append(intermediate)

        route_modifiers: RouteModifiers = {
            "avoidTolls": True,
        }

        self._request_body: Request = {
            "origin": origin,
            "intermediates": intermediates,
            "destination": destination,
            "travelMode": RouteTravelMode.DRIVE,
            "routingPreference": RoutingPreference.TRAFFIC_AWARE,
            "computeAlternativeRoutes": False,
            "routeModifiers": route_modifiers,
            "languageCode": "en-GB",
            "units": "IMPERIAL",
            "extraComputations": [ExtraComputation.TRAFFIC_ON_POLYLINE],
        }
        return self._request_body

    @property
    def stringified_request_body(self) -> dict[str, Any]:
        def stringify(body: Any) -> Any:
            if isinstance(body, Enum):
                return body.value
            elif isinstance(body, Mapping):
                return {str(key): stringify(value) for key, value in body.items()}
            elif isinstance(body, Sequence) and not isinstance(body, (str, bytes, bytearray)):
                return [stringify(item) for item in body]
            else:
                return body

        result = stringify(self._request_body)
        assert isinstance(result, dict)
        return result

    @property
    def route(self) -> str:
        return "https://routes.googleapis.com/directions/v2:computeRoutes"

    @property
    def is_daytime(self) -> bool:
        tz = ZoneInfo("Europe/London")
        now = datetime.now(tz)
        return 7 <= now.hour < 16

    @property
    def is_weekday(self) -> bool:
        tz = ZoneInfo("Europe/London")
        now = datetime.now(tz)
        return now.weekday() < 5  # Monday to Friday are 0-4

    @property
    def display(self) -> SSD1305:
        return self._display

    def update_display(self, data: dict[str, Any]) -> None:
        self._display.fill(constants.Colour.BLACK)
        travel_seconds = int(data.get("routes", [{}])[0].get("duration", "").removesuffix("s"))
        eta = datetime.now(tz=ZoneInfo("Europe/London")) + timedelta(seconds=travel_seconds)

        travel_advisory = data.get("routes", [{}])[0].get("travelAdvisory", {}).get("speedReadingIntervals", [])
        speeds = {}
        for advisory in travel_advisory:
            speed = advisory.get("speed", "SPEED_UNSPECIFIED")
            if speed not in speeds:
                speeds[speed] = 0
            speeds[speed] += 1

        if speeds.get("NORMAL", 0) >= speeds.get("SLOW", 0) and speeds.get("NORMAL", 0) >= speeds.get("TRAFFIC_JAM", 0):
            traffic_condition = "Normal"
        elif speeds.get("SLOW", 0) >= speeds.get("TRAFFIC_JAM", 0):
            traffic_condition = "Medium"
        else:
            traffic_condition = "Heavy"

        self._display.text(f"ETA:         {eta.strftime('%H:%M')}", 0, 0)
        self._display.text(f"Travel time: {travel_seconds // 60} min", 0, 10)
        self._display.text(f"Traffic:     {traffic_condition}", 0, 20)

    @loop(minutes=2)
    async def task(self) -> None:
        if not (self.is_weekday and self.is_daytime):
            return

        try:
            result = await self._session.post(
                self.route,
                json=self.stringified_request_body,
                headers=self.headers,
            )
            data = await result.json()
            print(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Error during tracking task: {e}")
        else:
            self.update_display(data)

    @task.before_loop
    async def before_task(self) -> None:
        print("Tracking task running...")

    @task.after_loop
    async def after_task(self) -> None:
        self.task_running.clear()


async def main():
    async with Tracker(
        Path("./gmap_tracker/locations.json"),
        Path("./gmap_tracker/headers.json"),
    ) as tracker:
        while tracker.task_running.is_set():
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
