from collections import defaultdict
from typing import Iterable

from fatsecret_sync.api.models.common import BasicNutritionalInfoMixin
from fatsecret_sync.api.models.food_entry import FoodEntry


def make_diary_print(food_entries: Iterable[FoodEntry], include_total_calories: bool = True):
    meals: dict[str, list[FoodEntry]] = defaultdict(list)
    food_entries = list(food_entries)
    for food_entry in food_entries:
        meals[food_entry.meal].append(food_entry)
    detailed_print = []
    for meal_name, foods in meals.items():
        foods = sorted(foods, key=lambda x: x.calories, reverse=True)
        category_print = [f"Meal: {meal_name} ({sum([f.calories for f in foods])}kCal)"] + [
            f"  - {f.food_entry_name}: {f.calories}kCal (P={f.protein}g, F={f.fat}g, C={f.carbohydrate}g)" for f in foods
        ]
        detailed_print.append("\n".join(category_print))
    detailed_print = "\n".join(detailed_print)
    if include_total_calories:
        tl = BasicNutritionalInfoMixin(
            calories=sum([f.calories for f in food_entries]),
            protein=sum([f.protein for f in food_entries]),
            carbohydrate=sum([f.carbohydrate for f in food_entries]),
            fat=sum([f.fat for f in food_entries]),
        )
        detailed_print = f"Total: {tl.calories}kCal (P={tl.protein}g, F={tl.fat}g, C={tl.carbohydrate}g)" + "\n" + detailed_print
    return detailed_print
