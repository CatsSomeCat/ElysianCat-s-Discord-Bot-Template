from __future__ import annotations

import functools
import inspect
import logging
import re
import time
from copy import deepcopy
from typing import Any, Callable, ClassVar, Optional, TypeVar, cast

import discord

from enums import LogSeverity
from exceptions import CallbackNotCallableError
from .decorators import copy_method

# Explicitly export specific names to be available in the module's namespace
# This helps in controlling which names are exposed when the module is imported
__all__ = (
	"StrictEmbedBuilder",
	"ExecutionTimeEstimator",
)

# Define a type variable for functions and coroutines
F = TypeVar("F", bound = Callable[..., Any])


class ExecutionTimeEstimator:
	"""
    A combined decorator and context manager for timing execution of functions, coroutines, or code blocks.

    This class measures the time taken by the wrapped function or the code block within the context.
    When used as a decorator, it wraps the function and logs its execution time using the provided or a default logger.
    When used as a context manager, it logs the elapsed time for the block of code.
    """
	
	__slots__ = ("name", "logger", "message_format", "callback", "log_as", "_start")
	
	# Class variable to hold a default logger
	_logger: Optional[logging.Logger] = None  # Allow None initially
	
	def __new__(cls, *args: Any, **kwargs: Any) -> ExecutionTimeEstimator:
		# Create a default logger for the class if it doesn't exist yet.
		if cls._logger is None:
			cls._logger = logging.getLogger(cls.__name__)  # Initialize default logger
		return super().__new__(cls)
	
	def __init__(
			self,
			name: str,
			logger: Optional[logging.Logger] = None,
			*,
			message_format: str = "Execution of '{name}' took {elapsed:.6f} seconds.",
			callback: Optional[Callable[[float], None]] = None,
			log_as: LogSeverity = LogSeverity.INFO,
	) -> None:
		"""
        Initializes an instance of ExecutionTimeEstimator with a name, logger, and optional configuration parameters.

        :param name: The identifier for the timed operation.
        :param logger: The logger to use for outputting timing information.
        :param message_format: Custom format for the log message. Placeholders available: '{name}' and '{elapsed}'.
        :param callback: A callback function that will be called with the elapsed time.
        :param log_as: The logging level to use for output (from LogSeverity enum).
        """
		# Assign the name of the timed operation for identification in logs
		self.name = name
		
		# Use the provided logger if available; otherwise, fallback to the class-level default logger
		self.logger = logger if logger is not None else self.__class__._logger
		
		# Define the format for log messages, allowing customization of output structure
		self.message_format = message_format
		
		# Store an optional callback function to be executed after timing completes
		self.callback = callback
		
		# Set the logging severity level to control how execution time messages are logged
		self.log_as = log_as
		
		# Initialize a placeholder for the start time, which will be set when execution begins
		self._start: float = 0.0
	
	def __enter__(self) -> ExecutionTimeEstimator:
		"""
        Enters the synchronous runtime context and start timing.

        :return: The instance of ExecutionTimeEstimator for use within the context block.
        """
		# Record high-resolution start time using perf_counter()
		self._start = time.perf_counter()
		return self
	
	def __exit__(
			self,
			exc_type: Optional[type],
			exc_value: Optional[BaseException],
			traceback: Optional[Any],
	) -> None:
		"""
        Exits the synchronous runtime context, log the elapsed time, and call the optional callback.

        :param exc_type: The type of exception raised (if any).
        :param exc_value: The exception instance raised (if any).
        :param traceback: The traceback object (if any).
        """
		# Calculate elapsed time regardless of exceptions
		elapsed: float = time.perf_counter() - self._start
		
		# Format and log message at configured severity level
		message: str = self.message_format.format(name = self.name, elapsed = elapsed)
		self.logger.log(self.log_as.value, message)  # type: ignore
		
		# Check if a callback is provided and if it is callable
		if self.callback is not None and callable(self.callback):
			# If the callback exists and is callable, call it with the elapsed time
			self.callback(elapsed)
		elif self.callback is not None:
			# If a callback is provided, but it's not callable, raise a custom exception with details
			raise CallbackNotCallableError(
				f"The callback provided for timing '{self.name}' must be callable, but received: {self.callback!r}"
			)
	
	async def __aenter__(self) -> ExecutionTimeEstimator:
		"""
        Asynchronously enters the runtime context and start timing.

        :return: The instance of ExecutionTimeEstimator for use within the asynchronous context block.
        """
		# Same timing mechanism as synchronous version
		self._start = time.perf_counter()
		return self
	
	async def __aexit__(
			self,
			exc_type: Optional[type],
			exc_value: Optional[BaseException],
			traceback: Optional[Any],
	) -> None:
		"""
        Asynchronously exits the runtime context, log the elapsed time, and call the optional callback.

        :param exc_type: The type of exception raised (if any).
        :param exc_value: The exception instance raised (if any).
        :param traceback: The traceback object (if any).
        """
		# Identical timing logic to synchronous version
		elapsed: float = time.perf_counter() - self._start
		message: str = self.message_format.format(name = self.name, elapsed = elapsed)
		self.logger.log(self.log_as.value, message)  # type: ignore
		
		# Check if a callback is provided and if it is callable
		if self.callback is not None and callable(self.callback):
			# If the callback exists and is callable, call it with the elapsed time
			self.callback(elapsed)
		elif self.callback is not None:
			# If a callback is provided, but it's not callable, raise a custom exception with details
			raise CallbackNotCallableError(
				f"The callback provided for timing '{self.name}' must be callable, but received: {self.callback!r}"
			)
	
	def __call__(self, func: F) -> F:
		"""
        Allows the ExecutionTimeEstimator instance to be used as a decorator for both synchronous and asynchronous functions.

        :param func: The function to be decorated.
        :return: The wrapped function with execution time estimation functionality.
        """
		# Check if decorated function is a coroutine
		if inspect.iscoroutinefunction(func):
			
			@functools.wraps(func)
			async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
				# Use async context manager for coroutine functions
				async with self:
					return await func(*args, **kwargs)
			
			return cast(F, async_wrapper)
		else:
			
			@functools.wraps(func)
			def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
				# Use regular context manager for sync functions
				with self:
					return func(*args, **kwargs)
			
			return cast(F, sync_wrapper)


@copy_method('__init__', override = True)
class StrictEmbedBuilder(discord.Embed):
	"""
    A strict and extended builder for creating Discord embeds with comprehensive validation.

    This builder validates key embed properties such as title, description, URL, and color
    automatically when they are assigned. It also provides helper methods to clone an embed
    or merge properties from another embed.
    """
	
	# Centralized maximum length constants for easier maintenance
	MAX_TITLE_LENGTH: ClassVar[int] = 256
	MAX_DESCRIPTION_LENGTH: ClassVar[int] = 4096
	MAX_FIELD_NAME_LENGTH: ClassVar[int] = 256
	MAX_FIELD_VALUE_LENGTH: ClassVar[int] = 1024
	MAX_FOOTER_TEXT_LENGTH: ClassVar[int] = 2048
	MAX_AUTHOR_NAME_LENGTH: ClassVar[int] = 256
	
	# Regex for validating URLs (a basic pattern)
	URL_REGEX: ClassVar[re.Pattern[str]] = re.compile(
		r"^(https?://)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$"
	)
	
	# Predefine attribute names to optimize memory usage
	__slots__ = (
		"title",
		"url",
		"type",
		"_timestamp",
		"_colour",
		"_footer",
		"_image",
		"_thumbnail",
		"_video",
		"_provider",
		"_author",
		"_fields",
		"description",
	)
	
	@staticmethod
	def _validate_string(value: str, max_length: int, field_name: str) -> None:
		"""
        Validates that the given value is a string and does not exceed the maximum length.

        :param value: The string value to validate.
        :param max_length: The maximum allowed length for the string.
        :param field_name: The name of the field being validated (used in error messages).
        :raise TypeError: If the value is not a string.
        :raise ValueError: If the value exceeds the maximum allowed length.
        """
		# Check if the provided value is a string
		if not isinstance(value, str):
			raise TypeError(
				f"{field_name} must be a string. Received {type(value).__name__} instead."
			)
		# If the value is not of type 'str', raise a 'TypeError' with a message specifying
		# the expected type and the actual received type
		
		# Check if the string length exceeds the allowed maximum
		if len(value) > max_length:
			raise ValueError(
				f"{field_name} cannot exceed {max_length} characters (got {len(value)})."
			)
		# If the string length is greater than 'max_length', raise a 'ValueError' with
		# an error message indicating the maximum limit and the actual length of the string
	
	@classmethod
	def _validate_url(cls, url: Any, field_name: str) -> None:
		"""
        Validates that the given URL is a string and matches a basic URL pattern.

        :param url: The URL string to validate.
        :param field_name: The name of the field being validated (used in error messages).
        :raise TypeError: If the URL is not a string.
        :raise ValueError: If the URL does not match the expected format.
        """
		if not isinstance(url, str):
			raise TypeError(
				f"{field_name} must be a string. Received {type(url).__name__} instead."
			)
		if not cls.URL_REGEX.match(url):
			raise ValueError(
				f"{field_name} must be a valid URL. Provided value: {url!r}"
			)
	
	def __setattr__(self, key: str, value: Any) -> None:
		"""
        Intercepts attribute assignment to validate key embed properties before setting them.

        This method ensures that values assigned to title, description, URL, and color follow
        Discord's embed constraints and validation rules.

        :param key: The attribute name being assigned.
        :param value: The new value to be assigned to the attribute.
        :raise TypeError: If the assigned value does not match the expected data type.
        :raise ValueError: If the assigned value exceeds the allowed constraints.
        """
		# Validate the title if being set
		if key == "title" and value is not None:
			self._validate_string(value, self.MAX_TITLE_LENGTH, "Title")
		
		# Validate the description if being set
		elif key == "description" and value is not None:
			self._validate_string(value, self.MAX_DESCRIPTION_LENGTH, "Description")
		
		# Validate the embed URL if being set
		elif key == "url" and value is not None:
			self._validate_url(value, "Embed URL")
		
		# Validate color if being set (both 'color' and 'colour' should be allowed)
		elif key in ("colour", "color") and value is not None:
			if not isinstance(value, int):  # Ensure the color is an integer
				raise TypeError(
					f"Color must be an integer, got {type(value).__name__} instead."
				)
			if not (
					0x000000 <= value <= 0xFFFFFF
			):  # Ensure the value is within the RGB range
				raise ValueError("Color must be between 0x000000 and 0xFFFFFF.")
		
		# Call the parent class's '__setattr__' to actually set the attribute
		super().__setattr__(key, value)
	
	def __getattr__(self, key: str) -> Any:
		"""
        Safer attribute access that respects parent class attributes.
        Only raises AttributeError for truly undefined attributes.
        """
		try:
			# First try parent class attribute access
			return super().__getattr__(key)  # type: ignore
		except AttributeError:
			# Fallback to original behavior for clearer errors
			raise AttributeError(
				f"'{type(self).__name__}' has no attribute '{key}'. "
				"Note: This error only occurs for attributes not defined in "
				"discord.Embed or StrictEmbedBuilder."
			)
	
	def clone(self) -> StrictEmbedBuilder:
		"""
        Creates a deep copy of the embed.

        :return: A new StrictEmbedBuilder instance with the same properties.
        """
		return deepcopy(self)
	
	def merge(self, other: StrictEmbedBuilder) -> StrictEmbedBuilder:
		"""
        Merges properties from another embed into this one.

        Appends all fields from the other embed and copies title, description, URL, and color
        if they are not already set. Returns the modified instance for chaining.

        :param other: Another StrictEmbedBuilder instance to merge from.
        :return: The modified StrictEmbedBuilder instance for chaining.
        """
		# Copy the title if it's missing in the current embed but exists in the other
		if not self.title and other.title:
			self.title = other.title
		
		# Copy the description if it's missing in the current embed but exists in the other
		if not self.description and other.description:
			self.description = other.description
		
		# Copy the URL if it's missing in the current embed but exists in the other
		if not self.url and other.url:
			self.url = other.url
		
		# Copy the colour if it's missing in the current embed but exists in the other
		# Using 'getattr' to safely check if 'colour' is present and not None
		if not getattr(self, "colour", None) and getattr(other, "colour", None):
			self.colour = other.colour
		
		# Append all fields from the other embed to this embed if the other embed has any
		if hasattr(other, "_fields") and isinstance(other._fields, list):
			for field in other._fields:
				# Use 'add_field' method to maintain validation
				super().add_field(**field)
		
		# Return self to allow method chaining
		return self
