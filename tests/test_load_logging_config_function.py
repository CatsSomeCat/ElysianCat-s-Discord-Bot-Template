import json
from unittest.mock import mock_open, patch

import pytest

from utilities.functions import load_logging_config


# Test for loading a valid JSON configuration file
def test_load_logging_config_valid():
    """
    Verifies that the function successfully loads a valid logging configuration
    from a JSON file. It mocks the file reading process and checks that the
    returned configuration matches the mock data.
    """
    config_data = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "verbose",
            }
        },
        "loggers": {
            "mylogger": {"level": "DEBUG", "handlers": ["console"], "propagate": False}
        },
    }

    # Mock open to simulate reading the JSON config
    with patch("builtins.open", mock_open(read_data=json.dumps(config_data))):
        result = load_logging_config("logging_config.json")

    # Assert that the returned config matches the mock data
    assert result == config_data


# Test for handling a file that does not exist (FileNotFoundError)
def test_load_logging_config_file_not_found():
    """
    Verifies that the function raises a FileNotFoundError when the specified
    logging configuration file does not exist.
    """
    with patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            load_logging_config("non_existent_config.json")


# Test for handling invalid JSON (JSONDecodeError)
def test_load_logging_config_invalid_json():
    """
    Verifies that the function raises a JSONDecodeError when the provided
    logging configuration file contains invalid JSON.
    """
    # Mock open to simulate reading an invalid JSON config
    with patch("builtins.open", mock_open(read_data="invalid_json")):
        with pytest.raises(json.JSONDecodeError):
            load_logging_config("logging_config.json")


# Test for an empty config file (returns an empty dictionary)
def test_load_logging_config_empty_file():
    """
    Verifies that the function correctly handles an empty logging configuration
    file by returning an empty dictionary.
    """
    empty_data = {}
    # Mock open to simulate an empty JSON config
    with patch("builtins.open", mock_open(read_data=json.dumps(empty_data))):
        result = load_logging_config("empty_config.json")

    # Assert that the returned config is empty
    assert result == empty_data


def test_load_logging_config_path_construction():
    """
    Verifies that the function constructs the correct file path for the
    logging configuration file by mocking the os.path.abspath function.
    The function should correctly resolve the path to the config file.
    """
    config_data = {
        "version": 1,
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "verbose",
            }
        },
    }

    # Mock open to simulate the logging configuration file
    with patch("builtins.open", mock_open(read_data=json.dumps(config_data))):
        # Mock 'os.path.abspath' to return a fixed path
        with patch("os.path.abspath") as mock_abspath:
            mock_abspath.return_value = "/mock/project/root"  # Mocked project root

            # Mock 'os.path.dirname' to simulate the 'tests' folder location
            with patch("os.path.dirname") as mock_dirname:
                mock_dirname.return_value = (
                    "/mock/project/tests"  # Mocked directory for tests
                )

                # Call the function
                result = load_logging_config("logging_config.json")

                # Assert the correct file path was constructed
                mock_abspath.assert_called_with(
                    "/mock/project/tests\\.."
                )  # Mocked correct path
                assert result == config_data  # Ensure the result matches the mock data
