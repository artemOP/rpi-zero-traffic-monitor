from typing import TypeAlias, TypedDict

from .enums import (
    ExtraComputation,
    FallbackReason,
    FallbackRoutingMode,
    RoadFeatureState,
    RouteLabels,
    RouteTravelMode,
    RoutingPreference,
    Speed,
    TollPass,
    TransitRoutingPreference,
    TransitTravelMode,
    VehicleEmissionType,
)


class Duration(TypedDict, total=False):
    units: str
    value: int


class FallbackInfo(TypedDict, total=False):
    routingMode: FallbackRoutingMode
    reason: FallbackReason


class LatLng(TypedDict, total=False):
    latitude: float
    longitude: float


class LocalizedText(TypedDict, total=False):
    text: str
    languageCode: str


class Location(TypedDict, total=False):
    latLng: LatLng
    heading: int


class Money(TypedDict, total=False):
    currencyCode: str
    units: str
    nanos: int


class Polyline(TypedDict, total=False):
    encodedPolyline: str
    geoJsonLinestring: str


class RouteLeg(TypedDict, total=False):
    distanceMeters: int
    duration: Duration


class Viewport(TypedDict, total=False):
    low: LatLng
    high: LatLng


class VehicleInfo(TypedDict, total=False):
    emissionType: VehicleEmissionType


class RouteModifiers(TypedDict, total=False):
    avoidTolls: bool
    avoidHighways: bool
    avoidFerries: bool
    avoidIndoor: bool
    vehicleInfo: VehicleInfo
    tollPasses: list[TollPass]


class SpeedReadingInterval(TypedDict, total=False):
    startPolylinePointIndex: int
    endPolylinePointIndex: int
    speed: Speed


class TollInfo(TypedDict, total=False):
    estimatedPrice: list[Money]


class RouteTravelAdvisory(TypedDict, total=False):
    tollInfo: TollInfo
    speedReadingIntervals: list[SpeedReadingInterval]
    fuelConsumptionMicroliters: int
    routeRestrictionsPartiallyIgnored: bool
    transitFare: Money


class PolylinePointIndex(TypedDict, total=False):
    startIndex: int
    endIndex: int


class FlyoverInfo(TypedDict, total=False):
    flyoverPresence: RoadFeatureState
    polylinePointIndex: PolylinePointIndex


class NarrowRoadsInfo(TypedDict, total=False):
    narrowRoadPresence: RoadFeatureState
    polylinePointIndex: PolylinePointIndex


class PolylineDetails(TypedDict, total=False):
    flyoverInfo: list[FlyoverInfo]
    narrowRoadsInfo: list[NarrowRoadsInfo]


class Route(TypedDict, total=False):
    routeLabels: list[RouteLabels]
    legs: list[RouteLeg]
    distanceMeters: int
    duration: Duration
    staticDuration: Duration
    polyline: Polyline
    description: str
    warnings: list[str]
    viewport: Viewport
    travelAdvisory: RouteTravelAdvisory
    optimizedIntermediateWaypointIndex: list[int]
    localizedValues: LocalizedText
    routeToken: str
    polylineDetails: PolylineDetails


class Status(TypedDict, total=False):
    code: int
    message: str
    details: list[dict]


class GeocodedWaypoint(TypedDict, total=False):
    geocoderStatus: Status
    type: list[str]
    partialMatch: bool
    placeId: str
    intermediateWaypointRequestIndex: int


class GeocodingResults(TypedDict, total=False):
    origin: GeocodedWaypoint
    destination: GeocodedWaypoint
    intermediates: list[GeocodedWaypoint]


class Response(TypedDict, total=False):
    routes: list[Route]
    fallbackInfo: FallbackInfo
    geocodingResults: GeocodingResults


class TransitPreferences(TypedDict, total=False):
    allowedTravelModes: list[TransitTravelMode]
    routingPreference: TransitRoutingPreference


place_id: TypeAlias = str
address: TypeAlias = str


class Waypoint(TypedDict, total=False):
    via: bool
    vehicleStopover: bool
    sideOfRoad: bool
    location: Location | place_id | address


class Request(TypedDict, total=False):
    origin: Waypoint
    destination: Waypoint
    intermediates: list[Waypoint]
    travelMode: RouteTravelMode
    routingPreference: RoutingPreference
    computeAlternativeRoutes: bool
    routeModifiers: RouteModifiers
    languageCode: str
    units: str
    extraComputations: list[ExtraComputation]
