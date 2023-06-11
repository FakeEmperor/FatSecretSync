from typing import Optional

from pydantic import BaseModel

from .common import DateInt, HeightType, WeightType


class ProfileStatus(BaseModel):
    weight_measure: WeightType
    height_measure: HeightType
    last_weight_kg: Optional[float] = None
    last_weight_date_int: Optional[DateInt] = None
    last_weight_comment: Optional[str] = None
    goal_weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
