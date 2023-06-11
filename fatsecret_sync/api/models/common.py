import datetime
from enum import Enum
from typing import ForwardRef, Optional

from pydantic import BaseModel


class WeightType(Enum):
    KILOGRAM = "kg"
    POUND = "lb"

    @classmethod
    def _missing_(cls, value: str):
        value = value.lower()
        for member in cls:
            if member.value == value:
                return member
        return None


class HeightType(Enum):
    CENTIMETER = "cm"
    INCH = "inch"

    @classmethod
    def _missing_(cls, value: str):
        value = value.lower()
        for member in cls:
            if member.value == value:
                return member
        return None


class DateInt(datetime.date):
    EPOCH_START = datetime.date(year=1970, month=1, day=1)

    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema: dict):
        # __get_pydantic_json_schema__ should mutate the dict it receives
        # in place, the returned value will be ignored
        field_schema.update(
            type=["integer", "string"],
            pattern=r"\d+",
            examples=["14500"],
        )

    @classmethod
    def validate(cls, value: str | int | datetime.date | ForwardRef("DateInt")):
        match value:
            case datetime.date():
                return cls(year=value.year, month=value.month, day=value.day)
            case cls():
                return value
            case str():
                value = int(value)
            case int():
                pass
            case _:
                raise TypeError("Value must be an integer for dateint type")
        return cls.EPOCH_START + datetime.timedelta(days=value)

    def __int__(self) -> int:
        return self.to_int()

    def to_int(self) -> int:
        return (self - self.EPOCH_START).days


# TODO: add measuring system that supports conversion and multiplication factors
class BasicNutritionalInfoMixin(BaseModel):
    # Metric units can be seen here
    # https://platform.fatsecret.com/api/Default.aspx?screen=rapiref&method=food.get.v3
    calories: int  # kCal
    carbohydrate: float  # g
    protein: float  # g
    fat: float  # g


class FullNutritionalInfoMixin(BasicNutritionalInfoMixin):
    # Metric units can be seen here
    # https://platform.fatsecret.com/api/Default.aspx?screen=rapiref&method=food.get.v3
    saturated_fat: Optional[float] = None  # g
    polyunsaturated_fat: Optional[float] = None  # g
    monounsaturated_fat: Optional[float] = None  # g
    trans_fat: Optional[float] = None  # g
    cholesterol: Optional[float] = None  # mg

    sodium: Optional[float] = None  # mg
    potassium: Optional[float] = None  # mg

    fiber: Optional[float] = None  # g

    sugar: Optional[float] = None  # g
    added_sugars: Optional[float] = None  # g

    vitamin_a: Optional[float] = None  # mcg
    vitamin_d: Optional[float] = None  # mcg
    vitamin_c: Optional[float] = None  # mg
    calcium: Optional[float] = None  # mg
    iron: Optional[float] = None  # mg
