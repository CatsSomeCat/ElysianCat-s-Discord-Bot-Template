from __future__ import annotations

import re
from typing import TYPE_CHECKING, Generic, TypeVar, cast

from exceptions import (
    ConstantModificationError,
    ConstantNotFoundError,
    ImmutableAttributeError,
    InvalidAttributeNameError,
    InvalidClassNameError,
    OverridingDunderMethodError,
)

# Define a type variable that represents an immutable type which is invariant
# This type variable is used for generic immutable collections and ensures that
# the type is neither covariant nor contravariant, meaning it is strictly invariant
_ImmutableType = TypeVar("_ImmutableType", covariant=False, contravariant=False)

# Define a type variable for the constant value type
# This type variable is constrained to only 'int', 'float', 'str', or 'bool' types,
# ensuring that constants can only be of these basic immutable types.
# It is also invariant, meaning it does not allow covariance or contravariance
T = TypeVar("T", int, float, str, bool, covariant=False, contravariant=False)

# This block is useful for providing type hints during static analysis (e.g., with mypy or pyright)
# without impacting runtime performance, it ensures better code clarity, catches type-related
# errors early, and improves IDE support for autocompletion and refactoring
if TYPE_CHECKING:
    from typing import Any, Dict, NoReturn, Tuple, Type


class ImmutableCollection(Generic[_ImmutableType]):
    """
    A class for creating immutable constant collections.

    This class stores constant values and prevents any modifications or deletions
    after initialization. Constants are accessed by calling the instance with the
    constant name as an argument.
    """

    # Define '__slots__' for memory optimization and efficiency
    __slots__ = ("_data",)  # Restricts instance to only have '_data' attribute

    def __init__(self, **kwargs: _ImmutableType) -> None:
        """Initializes an instance of ImmutableCollection class with provided key-value pairs."""
        object.__setattr__(self, "_data", kwargs.copy())  # Store constants internally

    def __call__(self, name: str) -> _ImmutableType:
        """Returns the value of the constant with the specified name."""
        try:
            return cast(_ImmutableType, self._data[name])
        except KeyError:
            raise ConstantNotFoundError(name)

    def __setattr__(self, name: str, value: _ImmutableType) -> NoReturn:
        """Prevents modification of constants after initialization."""
        raise ConstantModificationError(
            f"Cannot modify constant '{name}' after initialization."
        )

    def __delattr__(self, name: str) -> NoReturn:
        """Prevents deletion of constants after initialization."""
        raise ConstantModificationError(f"Cannot delete constant '{name}'.")

    def __repr__(self) -> str:
        """Returns a string representation of the ImmutableCollection instance."""
        return f"{type(self).__name__}({self._data})"

    # Ensure '__str__' returns the same result as '__repr__'
    def __str__(self) -> str:
        """Returns the same result as __repr__."""
        return self.__repr__()


class ConstantDescriptor(Generic[T]):
    """Descriptor for creating immutable constant values."""

    def __init__(self, value: T) -> None:
        self.value = value  # Store the constant value with type safety

    def __get__(self, instance: Any, owner: Type[Any]) -> T:
        """Retrieves the constant value."""
        return self.value

    def __set__(self, instance: Any, value: Any) -> None:
        """Prevents modification of constant values after initialization."""
        raise ImmutableAttributeError("Cannot modify constant values.")

    def __delete__(self, instance: Any) -> None:
        """Prevents deletion of constant values after initialization."""
        raise ImmutableAttributeError("Cannot delete constant values.")


class ConstantMeta(type):
    """
    Metaclass for defining classes with constant attributes.

    This metaclass is designed to enforce best practices for constant classes in Python.
    A constant class is a class whose purpose is solely to store constant values. This metaclass
    ensures that the class and its attributes follow specific conventions to maintain clarity and prevent
    unintended modifications.

    The class name must adhere to a specific convention: it should be in CamelCase and the
    word 'Constants' must be at the end. This ensures that constant classes are easily identifiable and their intent is clear.
    Any class that does not follow this naming convention will raise an error.

    Additionally, all attribute names within the class must be uppercase. This is a common practice for constants
    to distinguish them from other variables and indicate their immutability. If an attribute name does not meet
    this requirement, an error will be raised.

    Once a constant class is defined, its attributes are treated as immutable. This means that after the class
    is created, attempts to modify or change the values of its attributes will result in an error. This preserves
    the integrity of the constant values, ensuring they remain consistent throughout the program.

    The metaclass also prevents the overriding of dunder methods like '__init__', '__del__', or etc.
    These methods are typically used for initialization or destruction in regular classes, but in constant classes, they are
    unnecessary and could lead to confusion or misuse. Overriding these methods is therefore disallowed.

    So it ensures that constant classes are strictly used for their intended purpose storing constant
    values and protects against any accidental modification or misuse.
    """

    def __new__(
        mcs: Type[ConstantMeta],
        name: str,
        bases: Tuple[type, ...],
        attrs: Dict[str, Any],
    ) -> ConstantMeta:
        # Check if the class name ends with "Constants" (case-insensitive)
        if not name.lower().endswith("constants"):
            raise InvalidClassNameError(
                f"Invalid class name '{name}'. Class names should follow CamelCase and end with `Constants` suffix."
            )

        # Check if the class name follows the CamelCase convention
        if not re.match(r"^[A-Z][a-zA-Z0-9]*Constants$", name):
            raise InvalidClassNameError(
                f"Invalid class name '{name}'. Class names should follow CamelCase and end with `Constants` suffix."
            )

        # Collect changes separately to avoid modifying the dictionary during iteration
        new_attrs = {}

        # Validate attributes and prepare for immutability
        for attr_name, attr_value in attrs.items():
            # Ensure attribute names are uppercase and not dunder methods (e.g., __init__)
            if not attr_name.isupper() and not (
                attr_name.startswith("__") and attr_name.endswith("__")
            ):
                raise InvalidAttributeNameError(
                    f"Invalid attribute name '{attr_name}', attribute names must be uppercase."
                )

            # Optionally check for valid types (ensure only str, int, float, or bool types)
            # Skip special attributes like '__annotations__'
            if not isinstance(attr_value, (str, int, float, bool)) and not (
                attr_name.startswith("__") and attr_name.endswith("__")
            ):
                raise ValueError(
                    f"Invalid value type for '{attr_name}'. Only int, float, str, and bool are allowed."
                )

            # Ensure attributes are immutable after class creation using the 'ConstantDescriptor' class which acts similar to properties
            if not callable(attr_value) and not (
                attr_name.startswith("__") and attr_name.endswith("__")
            ):  # Avoid wrapping methods and special attributes in properties or constant descriptors
                # Narrow the type of 'attr_value' to 'T' (int, float, str, or bool)
                if isinstance(attr_value, int):
                    new_attrs[attr_name] = ConstantDescriptor[int](attr_value)
                elif isinstance(attr_value, float):
                    new_attrs[attr_name] = ConstantDescriptor[float](attr_value)
                elif isinstance(attr_value, str):
                    new_attrs[attr_name] = ConstantDescriptor[str](attr_value)
                elif isinstance(attr_value, bool):
                    new_attrs[attr_name] = ConstantDescriptor[bool](attr_value)
                else:
                    raise TypeError(
                        f"Invalid type for constant '{attr_name}'. Expected int, float, str, or bool, got {type(attr_value)}."
                    )

        # Ensure no dunder methods like '__init__' or '__del__' are overridden
        if "__init__" in attrs or "__del__" in attrs:
            raise OverridingDunderMethodError(
                "Overriding dunder methods such as `__init__` or `__del__` is not allowed in constant classes."
            )

        # Apply the new attributes collected during the loop
        attrs.update(new_attrs)  # type: ignore

        # Return the newly created class with the modified attributes
        return super().__new__(mcs, name, bases, attrs)

    def __setattr__(cls, name: str, value: Any) -> None:
        """Prevents any modifications to the constants after they are set in the class."""
        raise ImmutableAttributeError("Cannot set attributes on constant classes.")

    def __delattr__(cls, name: str) -> None:
        """
        Prevents deletion of attributes in constant classes.

        This ensures that once a constant is defined, it cannot be deleted,
        preserving the immutability of the class.
        """
        raise ImmutableAttributeError(
            f"Cannot delete attribute '{name}' from constant class."
        )


class NoInstantiationMeta(type):
    """A metaclass that prevents instantiation of any class."""

    def __call__(cls: type, *args: Any, **kwargs: Any) -> NoReturn:
        raise RuntimeError(f"Instances of {cls.__name__} cannot be instantiated.")


# Combined metaclass that inherits from both ConstantMeta and NoInstantiationMeta
class ConstantNoInstantiationMeta(ConstantMeta, NoInstantiationMeta):
    """A metaclass that enforces constant class behavior and prevents instantiation."""
