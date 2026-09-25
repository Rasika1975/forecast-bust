import logging

from fastapi import APIRouter, HTTPException, Query

try:
    from ..services.forecast_service import (
        ForecastDataUnavailableError,
        get_daily_forecast,
        get_location_forecast,
        get_raw_forecast,
    )
except ImportError:
    from services.forecast_service import (
        ForecastDataUnavailableError,
        get_daily_forecast,
        get_location_forecast,
        get_raw_forecast,
    )

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/forecast", tags=["forecast"])


def _service_error(error: Exception) -> HTTPException:
    if isinstance(error, ForecastDataUnavailableError):
        status_code = 404
    else:
        status_code = 500
        logger.exception("Forecast service request failed")

    return HTTPException(status_code=status_code, detail=str(error))


@router.get("/raw")
def raw_forecast():
    try:
        return get_raw_forecast()
    except Exception as error:
        raise _service_error(error) from error


@router.get("/grid")
def daily_grid_forecast(
    lead_day: int = Query(1, ge=1, le=10),
):
    try:
        return get_daily_forecast(lead_day)
    except Exception as error:
        raise _service_error(error) from error


@router.get("/map")
def forecast_map(
    lead_day: int = Query(1, ge=1, le=10),
):
    try:
        return get_daily_forecast(lead_day)
    except Exception as error:
        raise _service_error(error) from error


@router.get("/location")
def location_forecast(
    latitude: float,
    longitude: float,
    lead_day: int = Query(1, ge=1, le=10),
):
    try:
        return get_location_forecast(latitude, longitude, lead_day)
    except Exception as error:
        raise _service_error(error) from error
