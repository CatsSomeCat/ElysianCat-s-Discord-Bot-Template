from __future__ import annotations

import json
import os
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Iterable, TypeVar, cast

from exceptions import EmptyListError, MissingEnvironmentVariableError
from types_ import NestedSequence

# Explicitly export specific names to be available in the module's namespace
# This helps in controlling which names are exposed when the module is imported
__all__ = (
    "flatten_iterable",
    "flatten_dict_no_hierarchy_iterative",
    "format_iterable_into_human_readable_string",
    "is_hashable",
    "is_palindrome",
    "load_bot_config",
    "load_logging_config",
    "load_env_variables",
    "make_hashable",
    "find_same_objects",
)

# Define an invariant type variable (no covariant/contravariant flags)
T = TypeVar("T", covariant=False, contravariant=False)

# This block is useful for providing type hints during static analysis (e.g., with mypy or pyright)
# without impacting runtime performance, it ensures better code clarity, catches type-related
# errors early, and improves IDE support for autocompletion and refactoring
if TYPE_CHECKING:
    from typing import (
        Dict,
        Generator,
        Hashable,
        List,
        Literal,
        Optional,
        Set,
        Tuple,
        Type,
        Union,
    )


def flatten_iterable(
    nested_sequence: NestedSequence,
    /,
    *,
    disallowed_types: Optional[Tuple[Type[Any], ...]] = None,
    allowed_recursion: Tuple[Type[Iterable[Any]], ...] = (list, tuple, set, dict),
    preserve_order: bool = True,
    max_depth: Optional[int] = None,
) -> List[Any]:
    """
    Flattens a nested sequence (e.g., list, tuple) into a single-level list by expanding inner structures recursively.

    This function processes nested sequences and returns a flat list containing all elements from the input.
    It explicitly disallows str and bytes as top-level containers but allows them as elements inside containers.
    It also allows specifying which types to recurse into.

    :param nested_sequence: A sequence (e.g., list, tuple) that may contain nested sequences or elements.
    :param disallowed_types: A tuple of types that are not allowed as top-level containers (default: (str, bytes)).
    :param allowed_recursion: Types to recurse into (default: (list, tuple, set, dict)).
    :param preserve_order: If True, preserves the natural order of elements (default: True).
    :param max_depth: Maximum depth to flatten. None means no limit (full recursive flattening).
    :return: A flat list containing all elements from the input, with nested sequences expanded as per max_depth.
    :raise TypeError: If the top-level container is an instance of any type in disallowed_types.
    """
    # Default disallowed types
    default_disallowed_types: Tuple[Type[Any], ...] = (str, bytes)

    # Combine default and user-provided disallowed types
    if disallowed_types is not None:
        all_disallowed_types: Tuple[Type[Any], ...] = tuple(
            list(default_disallowed_types) + list(disallowed_types)
        )
    else:
        all_disallowed_types = default_disallowed_types

    # Runtime check to exclude disallowed types as top-level containers
    if isinstance(nested_sequence, all_disallowed_types):
        raise TypeError(
            f"Top-level container cannot be of type: {all_disallowed_types}."
        )

    # Initialize an empty list to store the flattened elements
    flattened: List[Any] = []

    # Create a stack for iterative traversal, starting with the input sequence
    # The stack holds tuples of (item, current_depth)
    stack: List[Tuple[NestedSequence, int]] = [(nested_sequence, 0)]

    # Track processed items to detect circular references and avoid infinite recursion
    processed: Set[int] = set()

    # Continue processing until the stack is empty
    while stack:
        # Pop the top item from the stack for processing
        current_item, depth = stack.pop()

        # If we have reached or exceeded max_depth, perform a shallow flatten:
        # If the item is an allowed iterable, iterate over it once and append its elements;
        # otherwise, append the item as is
        if max_depth is not None and depth >= max_depth:
            if isinstance(current_item, allowed_recursion):
                try:
                    # Cast current_item to 'Iterable[Any]' to help type checking
                    current_sequence: List[Any] = list(
                        cast(Iterable[Any], current_item)
                    )
                except TypeError:
                    current_sequence = list(cast(Iterable[Any], current_item))
                # Append each child without further flattening
                for child in current_sequence:
                    flattened.append(child)  # Shallow append
            else:
                flattened.append(current_item)
            continue  # Move to next item in stack

        # Check if the current item is an allowed iterable and hasn't been processed before,
        # and also ensure that we haven't exceeded the max_depth (if specified)
        if (
            isinstance(current_item, allowed_recursion)
            and id(cast(object, current_item)) not in processed
        ):
            # Add the current item's ID to the 'processed' set to track it and avoid circular references
            processed.add(id(cast(object, current_item)))

            # Use 'list' to get a sequence of the current item's elements
            try:
                # Cast current_item to Iterable[Any] to help type checking
                current_sequence = list(cast(Iterable[Any], current_item))
            except TypeError:
                current_sequence = list(cast(Iterable[Any], current_item))

            # Decide how to extend the stack based on preserve_order
            if preserve_order:
                # Special handling for sets: attempt to sort them for a consistent order if possible
                if isinstance(current_item, set):
                    try:
                        # Cast current_sequence to List[Any] for sorting
                        sorted_items: List[Any] = sorted(current_sequence)
                    except TypeError:
                        # If elements are not sortable, fallback to arbitrary order
                        sorted_items = list(current_sequence)
                    # Reverse so that when popped, items come out in sorted order
                    for child in reversed(sorted_items):
                        stack.append((child, depth + 1))
                else:
                    # For other iterables (lists, tuples, etc.), reverse to preserve left-to-right order
                    for child in reversed(current_sequence):
                        stack.append((child, depth + 1))
            else:
                # Without order preservation, simply add the children in natural order
                for child in current_sequence:
                    stack.append((child, depth + 1))
        else:
            # If the current item is not an allowed iterable (or max_depth is reached), add it to the result
            flattened.append(current_item)

    # Return the flattened list
    return flattened


def flatten_dict_no_hierarchy_iterative(
    nested_dict: Dict[str, Any],
    /,
    *,
    return_type: Literal["dict", "list_of_tuples", "tuple_of_lists"] = "dict",
) -> Union[Dict[str, Any], List[Tuple[str, Any]], Tuple[List[str], List[Any]]]:
    """
    Flattens a nested dictionary into a single-level data structure, discarding the hierarchy.
    Uses an iterative approach with a stack to avoid recursion.

    :param nested_dict: The nested dictionary to flatten.
    :param return_type: Specifies the type of data structure to return, with supported values being "dict" for a flattened dictionary (default),
                                            "list_of_tuples" for a list of (key, value) tuples, and "tuple_of_lists" for a tuple containing two lists.
    :return: A flattened data structure based on the specified return_type.
    """
    # Initialize an empty dictionary to store the flattened key-value pairs
    flattened_dict: Dict[str, Any] = {}

    # Use a stack to process dictionaries iteratively
    stack: List[Dict[str, Any]] = [nested_dict]

    # Continue processing until the stack is empty
    while stack:
        # Pop the top dictionary from the stack
        current_dict = stack.pop()

        # Iterate through each key-value pair in the current dictionary
        for key, value in current_dict.items():
            # Check if the value is a nested dictionary
            if isinstance(value, dict):
                # If it is a dictionary, push it onto the stack for further processing
                stack.append(value)  # type: ignore
            elif isinstance(value, (list, tuple)):
                # If the value is a list or tuple, flatten its elements with indexed keys
                for idx, item in enumerate(value):  # type: ignore
                    flattened_dict[f"{key}_{idx}"] = item
            else:
                # If it is not a dictionary, add the key-value pair to the flattened dictionary
                flattened_dict[key] = value

    # Determine the return type based on the 'return_type' parameter
    if return_type == "dict":
        # Return the flattened dictionary as is
        return flattened_dict

    elif return_type == "list_of_tuples":
        # Convert the dictionary items into a sorted list of tuples and return
        return sorted(flattened_dict.items())  # Sorting ensures consistent order

    elif return_type == "tuple_of_lists":
        # Extract keys and values separately and return them as a tuple of sorted lists
        if flattened_dict:
            # Unpack keys and values
            keys, values = zip(*sorted(flattened_dict.items()))

            # Explicitly convert dictionary items to two lists
            keys_list: List[str] = list(keys)
            values_list: List[Any] = list(values)
        else:
            keys_list, values_list = [], []
        return keys_list, values_list

    else:
        # Raise an error for unsupported return_type values
        raise ValueError(f"Unsupported return_type: {return_type}.")


def format_iterable_into_human_readable_string(
    items: Iterable[Any], /, *, separator: str = ", ", final: Union[str, None] = "and"
) -> str:
    """
    Formats an iterable of items into a human-readable string.

    :param items: An iterable of items (e.g., list, tuple). Strings are not allowed.
    :param separator: Separator between items (e.g., ', ', '; '). Defaults to ', '.
    :param final: Word to use before the last item (e.g., 'and', 'or'). Defaults to 'and'.
    :return: A formatted string representation of the iterable.
    :raise EmptyListError: If the iterable is empty.
    :raise TypeError: If a string is passed as 'items'.
    """
    # Check if the provided 'items' parameter is a string.
    if isinstance(items, str):
        raise TypeError(
            "The 'items' parameter must not be a string. Use a list or other iterable instead"
        )

    # Convert the iterable into a list to perform length-based operations.
    items = list(items)

    # Raise an error if the list is empty.
    if not items:
        raise EmptyListError("The 'items' iterable must contain at least one element")

    # Convert all items in the list to their string representation.
    items = list(map(str, items))

    # If there is only one item, return it directly.
    if len(items) == 1:
        return items[0]

    # If there are exactly two items, format them using the 'final' word between them.
    if len(items) == 2:
        return f"{items[0]} {final} {items[1]}"

    # For more than two items, split into all but the last and the final item.
    *initial_items, last_item = items

    # If a final word is provided, join the initial items with the separator and add the final word.
    if final:
        return f"{separator.join(initial_items)} {final} {last_item}"
    else:
        return f"{separator.join(initial_items)}{separator}{last_item}"


def find_same_objects(
    *, strict: bool = False, count: int = 3, **kwargs: T
) -> List[Tuple[T, List[str]]]:
    """
    Identifies objects that appear multiple times in keyword arguments, either by identity (`is`) or equality (`==`),
    and returns a list of tuples containing the object and the names of arguments referring to it.

    :param strict: If True, checks for object identity (`is`). If False, checks for equality (`==`).
    :param count: The minimum number of occurrences for an object to be included in the result.
    :param kwargs: Arbitrary keyword arguments with values to compare.
    :return: A list of tuples where each tuple contains:
                     - A hashable object found at least `count` times.
                     - A list of argument names referring to that object.
    """
    # Dictionary to store objects and their corresponding argument names
    objects: Dict[Any, List[str]] = defaultdict(list)

    if strict is True:
        # When strict mode is enabled, compare using object identity ('is')
        for key, value in kwargs.items():
            objects[id(value)].append(key)  # Store by unique object ID

        # Retrieve the original objects and filter based on count
        results = [
            (kwargs[names[0]], names)
            for names in objects.values()
            if len(names) >= count
        ]

    else:
        # When strict mode is disabled, compare using object equality ('==')
        for key, value in kwargs.items():
            # Convert lists to tuples (to make them hashable)
            hashable_value = tuple(value) if isinstance(value, list) else value  # type: ignore

            # Check if the value already exists in the dictionary
            found = False

            for obj in objects:
                if obj == hashable_value:  # Compare using equality ('==')
                    objects[obj].append(key)
                    found = True
                    break
            if not found:
                # Store the object if no match was found
                objects[hashable_value].append(key)

        # Filter objects that meet the 'count' threshold
        results = [
            (obj, names) for obj, names in objects.items() if len(names) >= count
        ]

    # Return a list of objects that appear at least 'count' times, along with their argument names
    return results


def is_palindrome(_string: str, /) -> bool:
    """
    Checks if a given string is a palindrome by ignoring case and non-alphanumeric characters.

    :param _string: The string to check.
    :return: True if the string is a palindrome, False otherwise.
    """
    # Normalize the string by converting to lowercase and filtering out non-alphanumeric characters
    normalized_string = "".join(char.lower() for char in _string if char.isalnum())

    # Use a two-pointer approach to compare characters from both ends, allowing early termination
    left, right = 0, len(normalized_string) - 1

    while left < right:
        # If characters at the pointers don't match, the string is not a palindrome
        if normalized_string[left] != normalized_string[right]:
            return False

        left += 1
        right -= 1

    # If the entire string has been checked without mismatches, it is a palindrome
    return True


def load_env_variables(env_file: str, variable_names: Iterable[str]) -> Dict[str, str]:
    """
    Loads the specified environment variables from the provided environment file.

    :param env_file: The path to the .env file.
    :param variable_names: An iterable of variable names in the .env file to load values from.
    :return: A dictionary where keys are variable names and values are the variables' values retrieved from the provided environment file.
    :raise FileNotFoundError: If the provided environment file is not found.
    :raise MissingEnvironmentVariableError: If any of the environment variables are not found in the provided environment file.
    """
    # Import the load_dotenv function from the python-dotenv package
    from dotenv import load_dotenv

    # Check if the file exists
    if not os.path.isfile(env_file):
        raise FileNotFoundError(f"{env_file} not found.")

    # Load environment variables from the provided environment file
    load_dotenv(env_file)

    # Dictionary to hold the result
    env_variables: Dict[str, str] = {}

    # Loop through the iterable of variable names and retrieve their values
    for variable_name in variable_names:
        # Retrieve the value of the environment variable using its name
        env_variable = os.getenv(variable_name)

        # Check if the environment variable was found
        if env_variable is None:
            # Raise a custom error if the environment variable is missing
            raise MissingEnvironmentVariableError(
                f"{variable_name} not found in the {env_file} file."
            )

        # Store the variable name and its value in the dictionary
        env_variables[variable_name.lower()] = env_variable

    # Create and return the namedtuple with the gathered values
    return env_variables


def load_logging_config(config_file: str, /) -> Dict[str, Any]:
    """
    Loads logging configuration from a JSON file located in the root directory of the project.

    :param config_file: The name of the JSON file containing the logging configuration.
    :return: The logging configuration as a dictionary.
    """
    # Get the root directory of the project (one directory above the 'utilities' folder)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Construct the full path to the config file in the project root
    config_path = os.path.join(project_root, config_file)

    # Open and read the JSON configuration file
    with open(config_path, "r+") as file:
        config = json.load(file)

    # Return the configuration as a dictionary
    return config


def load_bot_config(config_file: str, /) -> Dict[str, Any]:
    """
    Loads bot configuration from a JSON file located in the root directory of the project.

    :param config_file: The name of the JSON file containing the bot configuration.
    :return: The bot configuration as a dictionary.
    """
    # Get the root directory of the project (one directory above the 'utilities' folder)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Construct the full path to the config file in the project root
    config_path = os.path.join(project_root, config_file)

    # Open and read the JSON configuration file
    with open(config_path, "r", encoding="utf-8") as file:
        config = json.load(file)

    # Return the configuration as a dictionary
    return config


def make_hashable(value: Any) -> Hashable:
    """
    Recursively converts mutable types (like lists, dicts) to immutable types (like tuples, frozensets)
    so that they can be used as dictionary keys.

    :param value: The value to be converted to a hashable type.
    :return: A hashable version of the input value (tuple, frozenset, or the value itself).
    :raises TypeError: If the value or its nested components are not convertible to a hashable type.
    """
    # Early return for common hashable types
    if isinstance(value, (str, int, float, bool, bytes, type(None))):
        return value

    # Handle lists and tuples
    elif isinstance(value, (list, tuple)):
        return tuple(make_hashable(item) for item in value)  # type: ignore

    # Handle dictionaries
    elif isinstance(value, dict):
        # Explicitly annotate the generator expression
        dict_items: Generator[Tuple[Hashable, Hashable], None, None] = (
            (make_hashable(key), make_hashable(val)) for key, val in value.items()  # type: ignore
        )
        return frozenset(dict_items)

    # Handle sets and frozensets
    elif isinstance(value, (set, frozenset)):
        # Explicitly annotate the generator expression
        set_items: Generator[Hashable, None, None] = (make_hashable(item) for item in value)  # type: ignore
        return frozenset(set_items)

    # Check if the value is already hashable
    try:
        hash(value)
        return value
    except TypeError:
        raise TypeError(f"Unsupported type for hashing: {type(value)}")


def is_hashable(obj: Any) -> bool:
    """Check if an object is hashable."""
    try:
        hash(obj)
    except TypeError:
        return False
    return True
