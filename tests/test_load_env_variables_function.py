from unittest.mock import patch

import pytest

from exceptions import MissingEnvironmentVariableError
from utilities.functions import load_env_variables


# Fixture to mock the load_dotenv function
@pytest.fixture
def mock_load_dotenv():
    with patch("dotenv.load_dotenv") as mock:
        yield mock


# Fixture to mock the os.path.isfile function
@pytest.fixture
def mock_isfile():
    with patch("os.path.isfile") as mock:
        yield mock


# Fixture to mock the os.getenv function
@pytest.fixture
def mock_getenv():
    with patch("os.getenv") as mock:
        yield mock


@pytest.mark.parametrize(
    "env_file, variable_names, mock_env, expected_result, raises_error",
    [
        # Test case 1: Valid environment variables
        (
            "valid.env",
            ["VAR1", "VAR2"],
            {"VAR1": "value1", "VAR2": "value2"},
            {"var1": "value1", "var2": "value2"},
            None,
        ),
        # Test case 2: Missing environment variable
        (
            "valid.env",
            ["VAR1", "VAR2"],
            {"VAR1": "value1"},
            None,
            MissingEnvironmentVariableError,
        ),
        # Test case 3: FileNotFoundError if the file is not found
        ("non_existent.env", ["VAR1"], {"VAR1": "value1"}, None, FileNotFoundError),
    ],
)
def test_load_env_variables(
    env_file,
    variable_names,
    mock_env,
    expected_result,
    raises_error,
    mock_load_dotenv,
    mock_getenv,
    mock_isfile,
):
    """Tests the load_env_variables function with various scenarios."""
    # Mock the os.path.isfile to simulate file existence
    if env_file == "non_existent.env":
        mock_isfile.return_value = False  # Simulate file does not exist
    else:
        mock_isfile.return_value = True  # Simulate file exists

    # Mock the os.getenv function to simulate different environment variables
    def mock_getenv_side_effect(variable_name):
        return mock_env.get(variable_name)

    # Apply the mock for os.getenv
    mock_getenv.side_effect = mock_getenv_side_effect

    # Simulate the load_dotenv functionality (you can adjust if necessary)
    mock_load_dotenv.return_value = True

    if raises_error:
        # If an error is expected, assert that the error is raised
        with pytest.raises(raises_error):
            load_env_variables(env_file, variable_names)
    else:
        # Otherwise, assert that the result matches the expected output
        result = load_env_variables(env_file, variable_names)
        assert result == expected_result
