from __future__ import annotations

from collections.abc import Mapping as MappingABC
from typing import TYPE_CHECKING, Any, Generic, Mapping, NamedTuple, TypeVar, Union

# Explicitly export specific names to be available in the module's namespace
# This helps in controlling which names are exposed when the module is imported
__all__ = ("TupleUtilsMixin", "DictUtilsMixin")

# This block is useful for providing type hints during static analysis (e.g., with mypy or pyright)
# without impacting runtime performance, it ensures better code clarity, catches type-related
# errors early, and improves IDE support for autocompletion and refactoring
if TYPE_CHECKING:
    from typing import Callable, Dict, Optional, Type

# Define a type variable that can be either an instance of 'NamedTuple' or a dictionary-like object
T = TypeVar("T", bound=Union[NamedTuple, Mapping[str, Any]])


def tuple_to_dict(instance: NamedTuple) -> Dict[str, Any]:
    """
    Converts a NamedTuple instance to a dictionary.

    :param instance: The NamedTuple instance.
    :return: A dictionary representation of the NamedTuple.
    :raise TypeError: If the instance is not a tuple.
    """
    if not isinstance(instance, tuple):
        raise TypeError(f"Cannot convert {type(instance).__name__} to a dict.")
    return {field: getattr(instance, field) for field in instance._fields}


def tuple_is_valid(instance: NamedTuple) -> bool:
    """
    Checks if all values in the NamedTuple are not None.

    :param instance: The NamedTuple instance.
    :return: True if all values are not None, False otherwise.
    """
    return all(getattr(instance, field) is not None for field in instance._fields)


def dict_to_tuple(instance: Mapping[str, Any]) -> NamedTuple:
    """
    Converts a dictionary instance to a NamedTuple.

    :param instance: The dictionary instance.
    :return: A NamedTuple containing the dictionary's values.
    :raise TypeError: If the instance is not a dictionary.
    """
    if not isinstance(instance, MappingABC):
        raise TypeError(f"Cannot convert {type(instance).__name__} to a tuple.")

    # Create type annotations dictionary
    annotations: Dict[str, Type[Any]] = {k: type(v) for k, v in instance.items()}

    # Dynamically create a NamedTuple class with type annotations
    cls = type(
        "GeneratedNamedTuple",
        (NamedTuple,),
        {"__annotations__": annotations, "__module__": __name__},
    )

    # Instantiate the NamedTuple with proper type casting
    return cls(**{k: v for k, v in instance.items()})  # type: ignore


def dict_is_valid(instance: Dict[str, Any]) -> bool:
    """
    Checks if all values in the dictionary are not None.

    :param instance: The dictionary instance.
    :return: True if all values are not None, False otherwise.
    :raise TypeError: If the instance is not a dictionary.
    """
    if not isinstance(instance, dict):
        raise TypeError(f"Expected a dict, got {type(instance).__name__}.")
    return all(value is not None for value in instance.values())


class TupleUtilsMixin(Generic[T]):
    """
    A class-based decorator that injects utility methods for converting a NamedTuple
    to a dictionary and checking its validity. Additional callables can be optionally injected.
    """

    def __new__(
        cls,
        decorated_cls: Type[T],
        additional_methods: Optional[Dict[str, Callable[[T], Any]]] = None,
    ) -> Type[T]:
        setattr(decorated_cls, "to_dict", tuple_to_dict)
        setattr(decorated_cls, "is_valid", tuple_is_valid)

        # Inject additional methods if provided
        if additional_methods:
            for name, method in additional_methods.items():
                setattr(decorated_cls, name, method)

        return decorated_cls


class DictUtilsMixin(Generic[T]):
    """
    A class-based decorator that injects utility methods for converting a dictionary
    (or TypedDict) to a tuple and checking its validity. Additional callables can be optionally injected.
    """

    def __new__(
        cls,
        decorated_cls: Type[T],
        additional_methods: Optional[Dict[str, Callable[[T], Any]]] = None,
    ) -> Type[T]:
        setattr(decorated_cls, "to_tuple", dict_to_tuple)
        setattr(decorated_cls, "is_valid", dict_is_valid)

        # Inject additional methods if provided
        if additional_methods:
            for name, method in additional_methods.items():
                setattr(decorated_cls, name, method)

        return decorated_cls
