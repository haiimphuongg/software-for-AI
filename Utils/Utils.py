from typing import Type, TypeVar

from pydantic import BaseModel

U = TypeVar('U', bound=BaseModel)
T = TypeVar('T', bound=BaseModel)
def convert_model(source_model: T, target_model_class: Type[U]) -> U:
    valid_fields = target_model_class.__fields__
    model_update = {field: value for field, value in source_model.dict().items() if field in valid_fields}
    return_instance = target_model_class(**model_update)
    return return_instance
