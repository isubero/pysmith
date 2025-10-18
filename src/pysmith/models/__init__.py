from abc import ABC
from typing import Any, TypeVar

from pydantic import BaseModel, Field, create_model

T = TypeVar("T", bound="Model")


class Model(ABC):
    """Base class for all models."""

    _pydantic_model_cache: dict[type, type[BaseModel]] = {}
    pydantic_instance: BaseModel

    def __init__(self, **kwargs: Any) -> None:
        # Get or create the Pydantic model class (cached at class level)
        PydanticModelCls = self._get_or_create_pydantic_model()
        self.pydantic_instance = PydanticModelCls(**kwargs)

        for key, value in self.pydantic_instance.model_dump().items():
            setattr(self, key, value)

    @classmethod
    def _get_pydantic_fields(cls) -> dict[str, Any]:
        """Extract pydantic fields from class annotations."""
        return {
            key: (expected_type, Field(...))
            for key, expected_type in cls.__annotations__.items()
            if key
            not in {
                "pydantic_instance",
                "_pydantic_model_cache",
            }  # Skip internal fields
        }

    @classmethod
    def _get_or_create_pydantic_model(cls) -> type[BaseModel]:
        """Get the cached Pydantic model or create it if not cached."""
        if cls not in Model._pydantic_model_cache:
            model_name = cls.__name__
            fields = cls._get_pydantic_fields()
            pydantic_model = create_model(model_name, **fields)
            Model._pydantic_model_cache[cls] = pydantic_model
        return Model._pydantic_model_cache[cls]

    @classmethod
    def get_pydantic_model_cls(cls) -> type[BaseModel]:
        """Get the Pydantic model class for this Model class."""
        return cls._get_or_create_pydantic_model()

    @classmethod
    def validate_json(cls: type[T], json_data: str) -> T:
        """Validate and create an instance from JSON data."""
        pyd_model = cls._get_or_create_pydantic_model()
        pyd_instance = pyd_model.model_validate_json(json_data)
        return cls(**pyd_instance.model_dump())
