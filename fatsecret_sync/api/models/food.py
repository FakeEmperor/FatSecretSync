from enum import Enum

from pydantic import BaseModel, HttpUrl

from .common import FullNutritionalInfoMixin


class ServingMetricUnitType(Enum):
    GRAMS = "g"
    OUNCES = "oz"
    MILLILITERS = "ml"


class ServingInfoV3(FullNutritionalInfoMixin):
    serving_id: int
    serving_description: str
    serving_url: HttpUrl
    metric_serving_amount: float
    metric_serving_unit: ServingMetricUnitType
    number_of_units: float
    measurement_description: str


class FoodInfoV3(BaseModel):
    food_url: HttpUrl
    servings: list[ServingInfoV3]
    food_name: str
    food_type: str
