"""
Dev script that creates a config.schema.json file for IDEs auto-completion support on config files.

Run every time the AppConfig is changed.
"""
import logging
import pathlib
from os import PathLike
from typing import Type

from kily.common.utils.log import configure_logging
from pydantic import BaseModel

from fatsecret_sync.core.models import AppConfig

logger = logging.getLogger(__name__)

DEFAULT_SCHEMA_DESTINATION = pathlib.Path("../../schemas/config.schema.json")


def create_config_schema(schema_class: Type[BaseModel] = AppConfig, destination: PathLike = DEFAULT_SCHEMA_DESTINATION):
    destination = pathlib.Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Writing config schema to {destination}...")
    destination.write_text(schema_class.schema_json(indent=2))


if __name__ == "__main__":
    configure_logging()
    create_config_schema()
