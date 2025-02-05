from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Mapping,
    NamedTuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from structures.named_tuples import EnvVariables

# Explicitly export specific names to be available in the module's namespace
# This helps in controlling which names are exposed when the module is imported
__all__ = (
    "SanitizedWrapper",
    "EnvVariables",
)

# This block is useful for providing type hints during static analysis (e.g., with mypy or pyright)
# without impacting runtime performance, it ensures better code clarity, catches type-related
# errors early, and improves IDE support for autocompletion and refactoring
if TYPE_CHECKING:
    from typing import Callable, Dict, Optional, Type
else:
    # At runtime, treat 'TypedDict' as a regular dict
    TypedDict = dict

# Define a type variable that can be either an instance of 'NamedTuple' or a dictionary-like object
T = TypeVar("T", bound=Union[NamedTuple, Mapping[str, Any]])


class SanitizedWrapper(Generic[T]):
    """
    A generic wrapper class for sanitizing data structures.

    This class accepts an instance of a subclass of either `NamedTuple` (immutable) or `TypedDict` (mutable)
    and sanitizes placeholder string values (e.g., empty strings, "NULL", "NONE") by converting them into `None` values.
    Upon instantiation, it automatically processes and returns the sanitized data.
    """

    def __new__(cls, data: T, sanitizer: Optional[Callable[[str], Any]] = None) -> T:
        """
        Creates and returns sanitized data instead of an instance of the class.

        This method initializes a temporary instance, configures the sanitizer,
        applies the sanitization process, and directly returns the sanitized data.

        :param data: A NamedTuple or TypedDict instance to sanitize.
        :param sanitizer: An optional function to customize string sanitization.
        :return: The sanitized NamedTuple or TypedDict instance.
        """
        # Create a temporary instance to use instance methods for sanitization
        temporary_self = super().__new__(cls)

        # Set up the instance and apply sanitization
        return temporary_self.__create_instance(data, sanitizer)  # type: ignore

    def __create_instance(
        self, data: T, sanitizer: Optional[Callable[[str], Any]]
    ) -> T:
        """
        Sets up instance attributes and applies sanitization.
        """
        # Use the provided sanitizer
        self.sanitizer: Optional[Callable[[str], Any]] = sanitizer

        # Store the original data
        self.data: T = data

        # Apply the sanitization process to the data
        self.apply_sanitization()

        # Return the sanitized data directly
        return self.data

    def _sanitize_value(self, value: Any) -> Any:
        """
        Sanitizes an individual value.

        If the value is a string, it is first processed using the default sanitizer.
        If the default sanitizer returns a non-None value, the custom sanitizer is applied (if provided).
        If the default sanitizer returns None (indicating a placeholder), None is returned immediately.

        :param value: The value to be sanitized (could be any type).
        :return: The sanitized value or the original value if it's not a string.
        """
        # Only process string values
        if isinstance(value, str):
            # Apply the default sanitizer first
            default_result = self._default_sanitizer(value)

            # If the default sanitizer results in None, immediately return None
            if default_result is None:
                return None

            # Otherwise, if a custom sanitizer is defined, apply it to the result
            if self.sanitizer is not None:
                return self.sanitizer(default_result)

            # If no custom sanitizer is provided, return the result from the default sanitizer
            return default_result

        # For non-string types, return the value unchanged
        return value

    @staticmethod
    def _default_sanitizer(value: str) -> Optional[str]:
        """
        The default sanitization function.

        This function converts empty strings, "NULL", or "NONE" (in any casing) into None, otherwise it returns the original string.

        :param value: The string value to sanitize.
        :return: None if the value is a placeholder, otherwise the original value.
        """
        # Strip whitespace and convert to uppercase for comparison
        if value.strip().upper() in {"", "NULL", "NONE"}:
            return None
        return value

    def apply_sanitization(self) -> None:
        """
        Applies the sanitization logic to the stored data.

        For a TypedDict (dictionary), each value is sanitized and updated in-place; for a NamedTuple, a new instance is created with the sanitized values.
        """
        # Check if the data is a dictionary (TypedDict)
        if isinstance(self.data, dict):
            for key, value in self.data.items():
                self.data[key] = self._sanitize_value(value)

        # Check if the data is a NamedTuple (tuple with _fields attribute)
        elif isinstance(self.data, tuple) and hasattr(self.data, "_fields"):
            # Cast to the NamedTuple type for type checking
            nt_cls: Type[NamedTuple] = cast(Type[NamedTuple], type(self.data))
            sanitized_values = []

            # Iterate over each field in the NamedTuple
            for field in self.data._fields:
                value = getattr(self.data, field)
                sanitized_value = self._sanitize_value(value)
                sanitized_values.append(sanitized_value)  # type: ignore

            # Create a new NamedTuple instance with the sanitized values
            self.data = nt_cls(*sanitized_values)  # type: ignore
