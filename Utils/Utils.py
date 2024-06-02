from typing import Type, TypeVar

from pydantic import BaseModel

U = TypeVar('U', bound=BaseModel)
T = TypeVar('T', bound=BaseModel)
def model_to_model_update(source_model: T, target_model_class: Type[U]) -> U:
    valid_fields = target_model_class.__fields__
    model_update = {field: value for field, value in source_model.dict().items() if field in valid_fields}
    return target_model_class(**model_update)
