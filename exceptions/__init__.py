from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List


class ConstantMetaError(Exception):
    """Base class for all constant-related exceptions."""


class InvalidClassNameError(ConstantMetaError):
    """Raised when the class name does not end with 'Constants' or is invalid."""


class InvalidAttributeNameError(ConstantMetaError):
    """Raised when an attribute name is not in uppercase."""


class ImmutableAttributeError(ConstantMetaError):
    """Raised when an attempt is made to modify a constant class attribute."""


class OverridingDunderMethodError(ConstantMetaError):
    """Raised when a dunder method like '__init__' or '__del__' is overridden."""


class ConstantModificationError(Exception):
    """Exception raised when attempting to modify or delete an immutable constant."""


class ConstantNotFoundError(Exception):
    """Exception raised when a requested constant is not found."""

    def __init__(self, name: str) -> None:
        super().__init__(f"Constant '{name}' does not exist.")


class MissingEnvironmentVariableError(Exception):
    """Custom exception for missing environment variables."""

    pass


class InvalidColorError(Exception):
    """
    Exception raised when an invalid or missing color is referenced.
    """

    def __init__(self, color_name: str, available_colors: List[str]) -> None:
        """Initializes the exception with the invalid color name and available colors."""
        self.color_name = color_name
        self.available_colors = available_colors
        message = (
            f"The color '{color_name}' specified in the color_map is invalid or missing.\n"
            f"Available colors are: {', '.join(available_colors)}.\n"
            "Please ensure that all colors in the color_map are defined in the colors dictionary."
        )
        super().__init__(message)


class InvalidAttributeError(Exception):
    """
    Exception raised when an invalid or missing attribute is referenced.
    """

    def __init__(self, attribute: str, record_attributes: List[str]) -> None:
        """Initializes the exception with the invalid attribute name and available attributes."""
        self.attribute = attribute
        self.record_attributes = record_attributes
        message = (
            f"The attribute '{attribute}' specified in the color_map is not valid or not found in the logging record.\n"
            f"Available attributes in the log record are: {', '.join(record_attributes)}.\n"
            "Please ensure that all attributes in the color_map are present in the log record."
        )
        super().__init__(message)


class InvalidLogFileExtensionError(ValueError):
    """
    Exception raised when the log file does not have a valid extension.

    This custom exception provides more meaningful context and can be used
    to specifically catch issues related to invalid log file extensions.
    """

    def __init__(self, file_name: str, extension: str) -> None:
        """
        Initializes the exception with the file name and invalid file extension.

        :param file_name: The file name which contains the extension that caused the exception.
        :param extension: The expected extension for the file.
        """
        self.file_name = file_name
        self.message = (
            f"The log file '{file_name}' must have a `{extension}` extension."
        )
        super().__init__(self.message)


class InvalidWebhookStatusCodeError(Exception):
    """Custom exception raised when the Discord webhook returns an invalid status code."""


class EmptyListError(Exception):
    """Raised when an empty iterable is passed to the formatter."""

    pass


class ValidationSignatureError(Exception):
    """Exception raised when validation function's signature does not match the target function."""

    pass


class CallbackNotCallableError(Exception):
    """Custom exception raised when the provided callback is not callable."""

    pass
