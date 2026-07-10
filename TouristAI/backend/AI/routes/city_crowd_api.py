from fastapi import APIRouter, HTTPException

from services.city_crowd_history_service import predict_city_crowd_from_history

router = APIRouter()


@router.get("/api/city-crowd")
def get_city_crowd(city: str):
    try:
        return predict_city_crowd_from_history(city)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not calculate city crowd prediction: {str(error)}",
        )