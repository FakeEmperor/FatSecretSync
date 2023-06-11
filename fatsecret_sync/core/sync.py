import logging
from collections import defaultdict
from typing import Iterable, Optional, TypeVar

from kily.common.utils.dt import get_now

from ..api.client import FatSecretUserAPI
from ..api.models.common import DateInt
from ..api.models.food_entry import CreateFoodEntryRequest, EditFoodEntryRequest, FoodEntries, FoodEntry
from .models.sync import SyncDelta
from .utils import make_diary_print

logger = logging.getLogger(__name__)

KT = TypeVar("KT")


def merge_food_entries(
    origin_entries: Iterable[FoodEntry], target_entries: Iterable[FoodEntry], keep_unique_target_food: bool = True
) -> SyncDelta:
    origin_entries = list(origin_entries)
    target_entries = list(target_entries)

    def _map_reduce_foods(
        _foods: Iterable[FoodEntry], field: str | Iterable[str] = "food_id", key_type: type[KT] = int
    ) -> dict[KT, list[FoodEntry]]:
        _unique_foods: dict[key_type, list[FoodEntry]] = defaultdict(list)
        for _food in _foods:
            _key = getattr(_food, field) if isinstance(field, str) else tuple((getattr(_food, k) for k in field))
            _unique_foods[_key].append(_food)
        return _unique_foods

    delta = SyncDelta(delete=[], edit=[], create=[])

    # Process deletes
    to_delete = {e.food_entry_id for e in target_entries}
    if keep_unique_target_food:  # Remove from delete delta all food that is unique to target diary
        logger.debug("Will keep every food entry that is not in origin diary")
        origin_by_food_id: dict[int, list[FoodEntry]] = _map_reduce_foods(origin_entries)
        target_by_food_id: dict[int, list[FoodEntry]] = _map_reduce_foods(target_entries)
        for food_id, target_food_id_entries in target_by_food_id.items():
            if food_id not in origin_by_food_id:
                for entry in target_food_id_entries:
                    to_delete.remove(entry.food_entry_id)
                    logger.debug(f"KEEP '{entry.food_entry_description}': not present in origin")
    delta.delete = list(to_delete)
    # Process creates
    origin_by_cat = _map_reduce_foods(origin_entries, field=("food_id", "serving_id"), key_type=tuple[int, int])
    target_by_cat = _map_reduce_foods(target_entries, field=("food_id", "serving_id"), key_type=tuple[int, int])

    for cat_key, origin_cat_entries in origin_by_cat.items():
        if cat_key not in target_by_cat:  # Add all: food and serving not present in target
            for entry in origin_cat_entries:
                logger.debug(f"ADD '{entry.food_entry_description}': not present in target")
                delta.create.append(
                    CreateFoodEntryRequest(
                        serving_id=entry.serving_id,
                        food_entry_name=entry.food_entry_name,
                        number_of_units=entry.number_of_units,
                        meal=entry.meal,
                        food_id=entry.food_id,
                        date=entry.date_int,
                    )
                )
        else:  # Check target, add/edit: food and serving are present in target.
            target_cat_entries = target_by_cat[cat_key]
            for idx, entry in enumerate(origin_cat_entries):
                if idx >= len(target_cat_entries):
                    logger.debug(f"ADD '{entry.food_entry_description}': not present in target")
                    delta.create.append(
                        CreateFoodEntryRequest(
                            serving_id=entry.serving_id,
                            food_entry_name=entry.food_entry_name,
                            number_of_units=entry.number_of_units,
                            meal=entry.meal,
                            food_id=entry.food_id,
                            date=entry.date_int,
                        )
                    )
                else:
                    target_entry = target_cat_entries[idx]
                    delta.delete.remove(target_entry.food_entry_id)
                    if (
                        target_entry.serving_id != entry.serving_id
                        or target_entry.number_of_units != entry.number_of_units
                        or target_entry.meal != entry.meal
                    ):
                        delta.edit.append(
                            EditFoodEntryRequest(
                                food_entry_id=target_entry.food_entry_id,
                                food_entry_name=target_entry.food_entry_name,
                                serving_id=target_entry.serving_id,
                                number_of_units=entry.number_of_units,
                                meal=entry.meal,
                            )
                        )
    return delta


async def sync_user(origin_api: FatSecretUserAPI, target_api: FatSecretUserAPI, date: Optional[DateInt] = None):
    if date is None:
        now = get_now()
        date = DateInt(year=now.year, month=now.month, day=now.day)
    logger.info(f"Synchronizing users on {date.isoformat()}")

    origin_entries = await origin_api.get_food_entries_v2(date=date)
    if origin_entries is None or not origin_entries.food_entry:
        logger.warning("No origin entries, nothing to sync")
        return
    logger.info(f"Found {len(origin_entries.food_entry)} origin food entries:\n{make_diary_print(origin_entries.food_entry)}")
    target_entries = await target_api.get_food_entries_v2(date=date)
    if target_entries is None:
        target_entries = FoodEntries(food_entry=[])
    logger.info(f"Found {len(target_entries.food_entry)} target food entries:\n{make_diary_print(target_entries.food_entry)}")
    delta = merge_food_entries(
        origin_entries=origin_entries.food_entry, target_entries=target_entries.food_entry, keep_unique_target_food=True
    )
    if not delta:
        logger.info("Nothing to sync, everything is the same")
        return

    if delta.delete:
        logger.info(f"DEL {len(delta.delete)} food entries from target")
        for entry_id in delta.delete:
            # noinspection PyBroadException
            try:
                await target_api.delete_entry(entry_id)
            except Exception:
                logger.warning(f"Failed to DEL food entry", exc_info=True)

    if delta.create:
        logger.info(f"ADD {len(delta.create)} food entries to target")
        for req in delta.create:
            # noinspection PyBroadException
            try:
                await target_api.create_entry(req)
            except Exception:
                logger.warning("Failed to ADD food entry", exc_info=True)

    if delta.edit:
        logger.info(f"EDT {len(delta.edit)} food entries to target")
        for req in delta.edit:
            # noinspection PyBroadException
            try:
                await target_api.edit_entry(req)
            except Exception:
                logger.warning("Failed to EDT food entry", exc_info=True)
