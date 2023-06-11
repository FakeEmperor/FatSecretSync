from pydantic import BaseModel

from fatsecret_sync.api.models.food_entry import CreateFoodEntryRequest, EditFoodEntryRequest


class SyncDelta(BaseModel):
    delete: list[int]
    edit: list[EditFoodEntryRequest]
    create: list[CreateFoodEntryRequest]

    def __bool__(self) -> bool:
        return bool(self.delete) or bool(self.edit) or bool(self.create)
