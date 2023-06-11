from pydantic import BaseModel, Field

from .common import DateInt, FullNutritionalInfoMixin


class BaseFoodEntryRequest(BaseModel):
    food_entry_name: str = Field(description="The name of the food entry.")
    serving_id: int = Field(description="The ID of the serving.")
    number_of_units: float = Field(description="The number of servings eaten.")
    meal: str = Field(description="The type of meal eaten. Valid meal types are 'breakfast', 'lunch', 'dinner' and 'other'.")


class EditFoodEntryRequest(BaseFoodEntryRequest):
    food_entry_id: int = Field(description="The ID of the food entry to edit. ")


class CreateFoodEntryRequest(BaseFoodEntryRequest):
    food_id: int = Field(description="The ID of the food eaten.")
    date: DateInt = Field(default=None, description="Food entry date (default value is the current day)")


class FoodEntry(FullNutritionalInfoMixin):
    food_entry_id: int
    food_entry_description: str
    date_int: DateInt
    meal: str
    food_id: int
    serving_id: int
    number_of_units: float
    food_entry_name: str


class FoodEntries(BaseModel):
    food_entry: list[FoodEntry]
