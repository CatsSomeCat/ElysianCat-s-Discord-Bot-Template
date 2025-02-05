import json
from unittest.mock import mock_open, patch

import pytest

from utilities.functions import load_bot_config


@pytest.mark.parametrize(
    "config_data, expected_result",
    [
        # Test case 1: Valid bot configuration
        (
            {"token": "abc123", "prefix": "!", "owner_id": 1234567890},
            {"token": "abc123", "prefix": "!", "owner_id": 1234567890},
        ),
        # Test case 2: Empty bot configuration
        ({}, {}),
    ],
)
def test_load_bot_config_valid(config_data, expected_result):
    """
    Tests that the bot configuration is correctly loaded from a JSON file.
    """
    # Mock open to simulate reading a config file
    with patch("builtins.open", mock_open(read_data=json.dumps(config_data))):
        # Mock os.path.abspath to return a consistent path
        with patch("os.path.abspath") as mock_abspath:
            mock_abspath.return_value = "/mock/project/root"

            # Mock os.path.dirname to avoid system dependency
            with patch("os.path.dirname") as mock_dirname:
                mock_dirname.return_value = "/mock/project/utilities"

                # Call the function and check if output matches expected
                result = load_bot_config("bot_config.json")
                assert result == expected_result


def test_load_bot_config_file_not_found():
    """
    Tests that FileNotFoundError is raised when the configuration file does not exist.
    """
    with patch("os.path.abspath", return_value="/mock/project/root"), patch(
        "os.path.dirname", return_value="/mock/project/utilities"
    ), patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            load_bot_config("non_existent.json")


def test_load_bot_config_invalid_json():
    """
    Tests that a JSONDecodeError is raised when the config file contains invalid JSON.
    """
    with patch("os.path.abspath", return_value="/mock/project/root"), patch(
        "os.path.dirname", return_value="/mock/project/utilities"
    ), patch("builtins.open", mock_open(read_data="{invalid_json:}")):
        with pytest.raises(json.JSONDecodeError):
            load_bot_config("invalid.json")
