from __future__ import annotations

import functools
import inspect
from collections import OrderedDict, defaultdict
from typing import TYPE_CHECKING, ParamSpec, TypeVar, cast

from exceptions import ValidationSignatureError

from .functions import is_hashable, make_hashable

# Explicitly export specific names to be available in the module's namespace
# This helps in controlling which names are exposed when the module is imported
__all__ = ("add_private_attributes", "validate_input", "memoize", "copy_method")

# Define type variables for callable objects
P = ParamSpec("P")  # Represents the parameters of the callable
R = TypeVar("R")  # Represents the return type of the callable

# 'T' is a type variable representing the class type being decorated
# It is constrained to be a subclass of 'type', which means it can be any class
T = TypeVar("T", bound=type)

# This block is useful for providing type hints during static analysis (e.g., with mypy or pyright)
# without impacting runtime performance, it ensures better code clarity, catches type-related
# errors early, and improves IDE support for autocompletion and refactoring
if TYPE_CHECKING:
    from typing import Any, Callable, Dict, Hashable, Literal, Tuple


def copy_method(method_name: str, override: bool = False) -> Callable[[T], T]:
    """
    A decorator that copies a method from the first found superclass in the method resolution order (MRO).

    This decorator searches through the MRO of the decorated class for a method with the given name.
    If the method is found, its implementation and signature are copied to the decorated class.
    If the method is not found in any superclass, or if the decorated class already has a method with
    that name and override is set to False, an AttributeError is raised.

    :param method_name: The name of the method to copy.
    :param override: If True, overrides an existing method in the subclass; otherwise, raises an error.
    :raises AttributeError: If the method is not found in any superclass or if the method already exists
                            in the subclass (and override is False).
    :return: A class decorator that applies the method copying to the target class.
    """
    
    def decorator(cls: T) -> T:
        """
        The actual decorator function that is applied to a class.

        This function copies the specified method from the first superclass found in the method resolution order (MRO)
        and attaches it to the class being decorated.

        It also ensures that the method signature is copied for better IDE autocompletion and static analysis.

        :param cls: The class to which the method will be copied. This is the class being decorated.
        :return: The class with the copied method from the first found superclass in the MRO.
        :raises AttributeError: If the method is not found in any superclass or if the method already exists
                                in the class and overriding is not allowed (based on the `override` parameter).
        """
        # Search the class's MRO (excluding the class itself) for the specified method
        for base in cls.mro()[1:]:
            parent_method = getattr(base, method_name, None)
            if parent_method is not None:
                break
        else:
            raise AttributeError(f"No method '{method_name}' found in MRO of {cls.__name__}.")

        # Prevent accidental override of an existing method unless override is explicitly allowed
        if not override and hasattr(cls, method_name):
            raise AttributeError(f"'{cls.__name__}' already has a method '{method_name}'. Use override=True.")

        # Create a new method that calls the parent's method while preserving its metadata
        new_method = functools.wraps(parent_method)(
            lambda self, *args, **kwargs: parent_method(self, *args, **kwargs)
        )

        # Explicitly copy the method's docstring along with other metadata
        new_method.__doc__ = parent_method.__doc__

        setattr(cls, method_name, new_method)

        # Copy the signature for enhanced IDE autocompletion and static analysis
        getattr(cls, method_name).__signature__ = inspect.signature(parent_method)

        return cls

    return decorator


def add_private_attributes(**attrs: Any) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    A decorator factory that adds private (underscore-prefixed) attributes to a callable object.

    This decorator allows you to attach private attributes (prefixed with an underscore `_`)
    to a function or callable object. The attributes are set dynamically and can be accessed
    as part of the callable's internal state.

    :param attrs: Keyword arguments representing the attributes and their values to set on the callable.
                              The attribute names must not start with an underscore (`_`).
    :return: A decorator that adds the specified attributes to the callable.
    :raise ValueError: If an attribute name starts with an underscore (`_`).
    :raise TypeError: If the decorated object is not callable.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        """
        The actual decorator that wraps the target function and adds private attributes.

        :param func: The callable object (function, method, etc.) to be decorated.
        :return: The wrapped function with added private attributes.
        :raise TypeError: If the decorated object is not callable.
        :raise ValueError: If an attribute name starts with an underscore (`_`).
        """
        # Validate that the decorated object is callable
        if not callable(func):
            raise TypeError("The decorator can only be applied to callable objects.")

        # Iterate through each attribute provided as a keyword argument
        for attr_name, attr_value in attrs.items():
            # Ensure the attribute name does not start with an underscore
            if attr_name.startswith("_"):
                raise ValueError(
                    f"Attribute name '{attr_name}' must not start with an underscore ('_')."
                )

            # Dynamically set the attribute with a prefixed underscore
            setattr(func, f"_{attr_name}", attr_value)

        # Use 'functools.wraps' to preserve the original function's metadata (e.g., name, docstring)
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            """
            The inner wrapper function that adds private attributes to the callable.

            This function is executed whenever the decorated callable is invoked.
            It ensures that the private attributes are set before the callable is called.

            :param args: Positional arguments passed to the callable.
            :param kwargs: Keyword arguments passed to the callable.
            :return: The result of the original callable.
            """

            # Call the original function with the provided arguments
            return func(*args, **kwargs)

            # Return the wrapper function to replace the original callable

        return wrapper

        # Return the decorator to be applied to the target function

    return decorator


def validate_input(
    validation_func: Callable[P, bool],
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Validates the input arguments of a function by applying a user-defined validation function.

    :param validation_func: A function that validates the inputs and returns a boolean.
                                                    If it returns False, a ValueError is raised.
    :return: A decorator that wraps the target function to validate its inputs before execution.
    """

    # The decorator factory returns a decorator that will wrap the target function
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        """
        The decorator function that wraps the target function with validation logic.

        This function compares the signature of the validation function (`validation_func`) with that of
        the target function (`func`). If the signatures do not match, a ValidationSignatureError is raised.

        :param func: The target function to be decorated.
        :return: A wrapped function that validates its inputs before execution.
        :raise ValidationSignatureError: If the signature of the validation function does not match the target function.
        """
        # Compare the signatures of the validation function and the target function
        validation_signature = inspect.signature(validation_func)
        target_signature = inspect.signature(func)

        # Ensure the validation function takes the same parameters as the target function
        if validation_signature != target_signature:
            raise ValidationSignatureError(
                f"The signature of the validation function {validation_func.__name__} "
                f"does not match the target function {func.__name__}."
            )

        # Use functools.wraps to preserve the metadata (e.g., name, docstring) of the original function
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            """
            The wrapper function that performs the validation and calls the original function.

            This function validates the inputs using the provided `validation_func`. If the validation fails
            (returns False), a ValueError is raised. If the validation succeeds, the original function is called.

            :param args: Positional arguments passed to the function.
            :param kwargs: Keyword arguments passed to the function.
            :return: The result of the original function if validation succeeds.
            :raise ValueError: If the validation function returns False.
            """
            # Call the validation function with the same arguments as the decorated function
            # If the validation fails (returns False), raise a ValueError
            if not validation_func(*args, **kwargs):
                raise ValueError(f"Input validation for {func.__name__} failed.")

            # If validation succeeds, call the original function with the provided arguments
            return func(*args, **kwargs)

        # Return the wrapper function, which now includes the validation logic
        return wrapper

    # Return the decorator, which can be applied to any function with matching parameter types
    return decorator


def memoize(
    *,
    max_cache_size: int = 10,
    eviction_policy: Literal["LRU", "LFU"] = "LRU",
    fast: bool = False,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    A decorator that caches the result of expensive function calls to improve performance.

    The decorator stores previously computed results based on the function's arguments
    in a cache.

    If the function is called again with the same arguments, the cached result will be returned, avoiding the need to recompute the result.

    When the cache exceeds the max_cache_size, the least recently used (LRU) or least frequently used (LFU) entry
    will be removed based on the eviction_policy parameter.

    :param max_cache_size: The maximum number of results to store in the cache.
                                                    Default is 10, meaning only the most recent 10 results are cached.
    :param eviction_policy: The eviction strategy to use. Can be either "LRU" (Least Recently Used)
                                                    or "LFU" (Least Frequently Used). Default is "LRU".
    :param fast: If True, use functools.lru_cache for fast LRU eviction handling.
    :return: A wrapped function that caches its results based on arguments and evicts entries.
    """
    # Negative max_cache_size is treated as 0
    if max_cache_size < 0:
        max_cache_size = 0

    if eviction_policy not in ("LRU", "LFU"):
        raise ValueError(
            f"eviction_policy must be either 'LRU' or 'LFU', '{eviction_policy}' doesn't exist."
        )

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        """
        The decorator function that adds caching and eviction behavior to the target function.

        It wraps the target function `func` to add cache management. It checks if the function
        has been called with the same arguments before and retrieves the cached result if available.
        If the result is not cached, it computes the result, caches it, and evicts the least recently
        used (LRU) or least frequently used (LFU) cache entry if the cache size exceeds `max_cache_size`.

        :param func: The target function to be decorated.
        :return: A wrapped function that caches its results and evicts entries according to the eviction policy.
        """
        # Initialize cache and metadata based on eviction policy
        if eviction_policy == "LRU":
            # Explicitly annotate the type of 'cache'
            lru_cache: OrderedDict[Tuple[Hashable, ...], R] = OrderedDict()
            setattr(func, "__cache__", lru_cache)

        elif eviction_policy == "LFU":
            # Explicitly annotate the types of 'cache' and 'access_count'
            lfu_cache: Dict[Tuple[Hashable, ...], R] = dict()
            access_count: defaultdict[Tuple[Hashable, ...], int] = defaultdict(int)
            setattr(func, "__cache__", lfu_cache)
            setattr(func, "__access_count__", access_count)

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            """
            The wrapper function that performs the caching and eviction logic.

            It checks if the result for the given arguments is already in the cache.
            If found, the cached result is returned. If not, it computes the result,
            caches it, and evicts the least recently used or least frequently used entry
            if the cache exceeds the `max_cache_size`.

            :param args: Positional arguments passed to the function.
            :param kwargs: Keyword arguments passed to the function.
            :return: The result of the function, either from the cache or newly computed.
            """
            # Check if all function parameters are hashable
            all_params_hashable = all(
                is_hashable(param) for param in func.__annotations__.values()
            )

            # Check if all arguments (both positional and keyword arguments) are hashable
            all_args_hashable = all(
                is_hashable(arg) for arg in zip(kwargs.values(), args, strict=False)
            )

            # If eviction policy is "LRU" and 'fast' is True and either all parameters or arguments are hashable
            if (
                eviction_policy == "LRU"
                and any((all_args_hashable, all_params_hashable))
                and fast
            ):
                # Use 'functools.lru_cache' for hashable arguments
                return functools.lru_cache(maxsize=max_cache_size, typed=True)(func)  # type: ignore

            # Create a cache key based on function arguments
            key = (
                tuple(
                    make_hashable(arg) if not is_hashable(arg) else arg for arg in args
                ),
                frozenset(
                    (k, make_hashable(v) if not is_hashable(v) else v)
                    for k, v in kwargs.items()
                ),
            )

            # Retrieve cache and access_count from the function
            cache = getattr(func, "__cache__")
            access_count = getattr(func, "__access_count__", None)

            # Check if the result is already cached
            if key in cache:
                if eviction_policy == "LRU":
                    # Move to end to mark as recently used
                    cache.move_to_end(key)
                elif eviction_policy == "LFU" and access_count is not None:
                    # Increase access count for LFU policy
                    access_count[key] += 1
                return cast(R, cache[key])  # Return the cached result

            # Compute and cache result if not found
            result = func(*args, **kwargs)
            cache[key] = result  # Store result in cache

            # Update access count for LFU on initial insertion
            if eviction_policy == "LFU" and access_count is not None:
                access_count[key] += 1

            # Eviction logic if cache exceeds max size
            if len(cache) > max_cache_size:
                if eviction_policy == "LRU":
                    # Ensure we only attempt eviction if the cache is non-empty
                    if cache:
                        # Remove the least recently used item
                        popped_key, _ = cache.popitem(last=False)
                elif eviction_policy == "LFU" and access_count is not None:
                    # Find the key with the minimum access count in the cache
                    lfu_key = min(cache, key=lambda k: access_count.get(k, 0))

                    del cache[lfu_key]  # Remove the least frequently used item
                    del access_count[lfu_key]  # Remove associated access count

            return result  # Return the newly computed result

        return wrapper  # Return the decorated function

    return decorator  # Return the decorator itself
