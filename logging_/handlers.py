import asyncio
import datetime as dt
import os
import re
import threading
import time
from logging import Handler, LogRecord
from logging.handlers import BaseRotatingHandler
from typing import Any, Dict, Literal, Optional, override

import aiohttp

from exceptions import InvalidLogFileExtensionError, InvalidWebhookStatusCodeError

__all__ = (
    "DualRotatingHandler",
    "JSONLFileHandler",
    "DiscordWebHookHandler",
)

# Regex pattern to identify timestamped backup files in the log directory
timestamp_pattern = re.compile(r"\.\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}-\d{4}$")


class DualRotatingHandler(BaseRotatingHandler):
    """
    A thread-safe log handler designed for advanced log management, supporting both size-based and time-based rotation,
    along with customizable backup file naming schemes.

    Logs can be rotated based on file size thresholds or time intervals, offering flexibility for diverse application needs.
    The handler ensures thread safety for multi-threaded environments by utilizing a reentrant lock mechanism.

    It provides customizable backup naming formats: numeric increments or timestamp-based naming.
    This feature improves organization and simplifies management of backup log files.

    The class is ideal for applications requiring detailed and adaptable log rotation strategies to handle large volumes of logs efficiently.
    """

    def __init__(
        self,
        file_name: str,
        mode: Literal["a", "w", "x", "r+", "w+"] = "a",
        max_bytes: int = 0,
        backup_count: int = 0,
        interval: int = 1,
        when: Literal[
            "S", "M", "H", "D", "MIDNIGHT", "W0", "W1", "W2", "W3", "W4", "W5", "W6"
        ] = "MIDNIGHT",
        at_time: Optional[dt.time] = None,
        encoding: Optional[str] = None,
        delay: bool = False,
        errors: Optional[str] = None,
        backup_extension_type: Literal["count", "time"] = "count",
    ) -> None:
        """
        Initializes a dual rotating log handler for size-based and/or time-based rotation.

        :param file_name: The full path to the log file where the logs will be written.
        :param mode: The file opening mode. 'a' for append (default), 'w' for overwrite.
        :param max_bytes: The maximum size (in bytes) of the log file before rotation occurs. Set 0 to disable size-based rotation.
        :param backup_count: The maximum number of backup files to keep. Files beyond this count will be deleted.
        :param interval: The interval value for time-based rotation, combined with the `when` parameter.
        :param when: A string representing the rotation policy for time intervals (e.g., 'MIDNIGHT', 'D', 'W0').
        :param at_time: A `datetime.time` object indicating a specific time for rotation (applies to 'MIDNIGHT' or 'W*' policies).
        :param encoding: Encoding of the log file. Defaults to system encoding if None.
        :param delay: If True, delays creating the log file until the first write operation. Default is False.
        :param errors: Specifies error handling for encoding issues (e.g., 'strict', 'ignore').
        :param backup_extension_type: Backup file naming policy:
                                      - 'count': Numeric backups (e.g., file.log.1, file.log.2, ...).
                                      - 'time': Timestamp backups (e.g., file.log.2025-01-24_17-03-32-4642).

        :raise ValueError: Raised for invalid parameter values.
        """
        # Reassign 'handleError' to adhere to snake_case naming convention
        setattr(self, "handle_error", BaseRotatingHandler.handleError)

        # Initialize the base class for logging file management
        super().__init__(file_name, mode, encoding, delay, errors)

        # Create a reentrant lock to ensure safe file operations in multithreaded environments
        self.reentrant_lock = threading.RLock()

        # Assign instance variables
        self.day_of_week = None
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.when = when.upper()
        self.interval = interval
        self.at_time = at_time
        self.backup_extension_type = backup_extension_type

        # Perform validation on all parameters
        self._validate_parameters()

        # Define the supported time intervals for rotation
        self.time_units = {
            "S": "seconds",
            "M": "minutes",
            "H": "hours",
            "D": "days",
            "MIDNIGHT": "midnight",
        }

        # Compute the initial rollover time for time-based rotation
        self.rollover_at = self.compute_rollover(dt.datetime.now(dt.timezone.utc))

    def _validate_parameters(self) -> None:
        """
        Validates the parameters provided during the initialization of the handler.
        Raises ValueError for invalid values and warns about potential issues.

        :raise ValueError: Raised for invalid file names, unsupported modes, negative intervals,
                           invalid time-based rotation intervals, or invalid backup configurations.
        """
        # Validate baseFilename (ensure it is a non-empty string)
        if not self.baseFilename or not isinstance(self.baseFilename, str):
            raise ValueError(
                "baseFilename must be a non-empty string specifying the log file path."
            )

        # Validate file mode
        if self.mode not in {"a", "w", "x", "r+", "w+"}:
            raise ValueError(
                f"Invalid file mode: {self.mode}. Supported modes are 'a', 'w', 'x', 'r+', and 'w+'."
            )

        # Validate max_bytes (must be a non-negative integer)
        if not isinstance(self.max_bytes, int) or self.max_bytes < 0:
            raise ValueError("max_bytes must be a non-negative integer.")

        # Validate backup_count (must be a non-negative integer)
        if not isinstance(self.backup_count, int) or self.backup_count < 0:
            raise ValueError("backup_count must be a non-negative integer.")

        # Warn if no backups will be created due to a count of zero
        if self.backup_count == 0:
            pass
        # logging.warning("backup_count is set to 0; no backups will be retained during log rotation.")

        # Validate interval (must be a positive integer)
        if not isinstance(self.interval, int) or self.interval <= 0:
            raise ValueError("interval must be a positive integer greater than zero.")

        # Validate 'when' parameter for time-based rotation
        if self.when.startswith("W"):  # Weekly rotation
            if len(self.when) == 2 and self.when[1].isdigit():
                day = int(self.when[1])  # Extract day of the week
                if 0 <= day <= 6:
                    self.day_of_week = day  # Valid day
                else:
                    raise ValueError(
                        f"Invalid day specified in 'when': {self.when}. Must be between 0 (Monday) and 6 (Sunday)."
                    )
            else:
                raise ValueError(
                    f"Invalid 'when' format: {self.when}. Expected format is 'W0' to 'W6' for weekly rotation."
                )
        else:
            self.day_of_week = None  # No weekly rotation

        # Check for unsupported or invalid 'when' values
        if self.when not in {
            "S",
            "M",
            "H",
            "D",
            "MIDNIGHT",
        } and not self.when.startswith("W"):
            raise ValueError(
                f"Invalid rollover interval specified: {self.when}. Supported values are 'S', 'M', 'H', 'D', 'MIDNIGHT', or 'W0' to 'W6'."
            )

        # Validate at_time (must be a datetime.time object or None)
        if self.at_time is not None and not isinstance(self.at_time, dt.time):
            raise ValueError("at_time must be a datetime.time object or None.")

        # Validate backup_extension_type
        if self.backup_extension_type not in {"count", "time"}:
            raise ValueError(
                f"Invalid backup_extension_type: {self.backup_extension_type}. Supported values are 'count' and 'time'."
            )

    def compute_rollover(self, current_time: dt.datetime) -> float:
        """
        Computes the next time at which rollover should occur based on the specified `when` and `interval`.

        :param current_time: The current timestamp as a `datetime` object.
        :return: The timestamp (in seconds since the epoch) of the next rollover time.

        :raise ValueError: If an unsupported `when` value is provided.
        """
        if self.when == "MIDNIGHT":
            # Schedule the next rollover to occur at midnight
            # Add one day to the current time and reset the hour, minute, second, and microsecond to zero
            rollover_time = (current_time + dt.timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            # If a specific rollover time (`self.at_time`) is configured, adjust the rollover time accordingly
            if self.at_time:
                rollover_time = rollover_time.replace(
                    hour=self.at_time.hour,
                    minute=self.at_time.minute,
                    second=self.at_time.second,
                )

            # Return the timestamp of the next rollover time in seconds since the epoch
            return rollover_time.timestamp()

        elif self.when in ("S", "M", "H", "D"):
            # For interval-based rollovers (e.g., seconds, minutes, hours, or days):
            # Use a `timedelta` to calculate the next rollover time based on the interval.
            delta = dt.timedelta(**{self.time_units[self.when]: self.interval})
            return (current_time + delta).timestamp()

        elif self.when.startswith("W") and self.day_of_week is not None:
            # For weekly rollovers, calculate the next rollover day based on `self.day_of_week` (0 = Monday, ..., 6 = Sunday)

            # Compute the number of days until the next rollover day
            # Add 7 to ensure the modulo operation handles negative differences correctly
            days_to_go = (self.day_of_week - current_time.weekday() + 7) % 7

            # If the current day is the rollover day (`days_to_go == 0`), schedule it for the next week
            if days_to_go == 0:
                days_to_go = 7

            # Add the computed days to the current time to get the next rollover date
            next_rollover = current_time + dt.timedelta(days=days_to_go)

            # Adjust the rollover time to a specific hour, minute, and second if `self.at_time` is configured
            if self.at_time:
                next_rollover = next_rollover.replace(
                    hour=self.at_time.hour,
                    minute=self.at_time.minute,
                    second=self.at_time.second,
                )
            else:
                # Default to midnight if no specific time is configured
                next_rollover = next_rollover.replace(
                    hour=0, minute=0, second=0, microsecond=0
                )

            # Return the timestamp of the next rollover time in seconds since the epoch
            return next_rollover.timestamp()

        else:
            # Raise an error for unrecognized `when` values, providing a detailed message
            raise ValueError(
                f"Unhandled rollover schedule '{self.when}'. Supported values are: "
                f"'S' (Seconds), 'M' (Minutes), 'H' (Hours), 'D' (Days), 'MIDNIGHT' (rotate at midnight), "
                f"and 'W0'-'W6' (weekly on a specific day, 0=Monday, 6=Sunday). "
                "Please verify that the 'when' parameter matches one of these supported values."
            )

    def should_rollover(self, record: LogRecord) -> Optional[bool]:
        """
        Determines whether rollover conditions are met based on file size and/or time intervals.

        :param record: The log record being processed.
        :return: True if rollover conditions are satisfied, False otherwise.
        """
        # Check if the stream is not initialized (None), and if so, initialize it by opening a new stream
        if self.stream is None:
            self.stream = self._open()  # type: ignore

        # Check if the file exceeds the size limit
        if self.max_bytes > 0:
            self.stream.seek(0, os.SEEK_END)
            if self.stream.tell() >= self.max_bytes:
                return True

        # Check if the current time exceeds the rollover threshold
        if dt.datetime.fromtimestamp(record.created).timestamp() >= self.rollover_at:
            return True

        # Indicate that no rollover is necessary by returning False
        return False

    def do_rollover(self) -> None:
        """
        Executes the rollover operation. Renames the current log file to a backup and creates a new log file for future writes.
        Old backups exceeding the configured retention limit (backup_count) are deleted.

        :raise Exception: If an error occurs during the rollover process.
        """
        # Close the current log file stream if it's open
        # This ensures there are no file access conflicts during renaming or deletion
        if self.stream:
            self.stream.close()

        # Reset the stream attribute to `None` so a new log file can be created later
        self.stream = None  # type: ignore

        # Determine the backup file naming strategy based on the extension type
        if self.backup_extension_type == "time":
            # Generate a unique timestamp string for time-based backup filenames
            # Example format: "2025-01-21_21-03-47-1193" (last two digits of microseconds omitted for brevity)
            timestamp = dt.datetime.now(dt.timezone.utc).strftime(
                "%Y-%m-%d_%H-%M-%S-%f"
            )[:-2]
            backup_file = (
                f"{self.baseFilename}.{timestamp}"  # Time-based backup filename
            )
        else:
            # Generate a numerical backup filename, e.g., "logfile.1"
            backup_file = f"{self.baseFilename}.1"

        # Use a reentrant lock to ensure thread safety in multithreaded environments
        with self.reentrant_lock:
            try:
                # Handle numbered backup rotation if the extension type is not "time"
                if self.backup_extension_type != "time":
                    # Start from the highest backup number and rename files in reverse order
                    for index in range(self.backup_count - 1, 0, -1):
                        old_file = f"{self.baseFilename}.{index}"  # Current backup file
                        new_file = f"{self.baseFilename}.{index + 1}"  # Target filename

                        if os.path.exists(old_file):  # Check if the backup file exists
                            if os.path.exists(
                                new_file
                            ):  # Remove the target file if it exists
                                os.remove(new_file)
                            # Rename the current backup file to the target filename
                            os.rename(old_file, new_file)

                    # Rename the current log file to the first backup file (e.g., "logfile.1")
                    if os.path.exists(self.baseFilename):
                        os.rename(self.baseFilename, backup_file)

                # Handle time-based backup rotation
                elif self.backup_extension_type == "time":
                    # Get the directory where the log file is stored
                    backup_dir = os.path.dirname(self.baseFilename)

                    # Collect all timestamped backup files along with their last modified times
                    timestamped_backups = []
                    for file in os.listdir(
                        backup_dir
                    ):  # Iterate through files in the directory
                        file_path = os.path.join(backup_dir, file)
                        if timestamp_pattern.search(
                            file
                        ):  # Match files against the timestamp pattern
                            timestamped_backups.append((file_path, os.path.getmtime(file_path)))  # type: ignore

                    # Append the current backup file to the list for proper management
                    timestamped_backups.append((backup_file, dt.datetime.now(dt.timezone.utc).timestamp()))  # type: ignore

                    # Sort the backups by their last modified time, with the oldest backups first
                    timestamped_backups.sort(key=lambda backup_info: backup_info[1])  # type: ignore

                    # Calculate how many files exceed the backup limit
                    excess_files = len(timestamped_backups) - self.backup_count  # type: ignore

                    # Remove only the excess (oldest) backup files if necessary
                    for index in range(excess_files):
                        # Path of the oldest backup file
                        old_backup = timestamped_backups[index][0]  # type: ignore
                        # Delete the file
                        os.remove(old_backup)  # type: ignore

                    # Rename the current log file to include the new timestamp in its name
                    if os.path.exists(self.baseFilename):
                        os.rename(self.baseFilename, backup_file)

                # Open a new empty log file for future writes
                self.stream = self._open()

                # Schedule the next rollover time if using time-based log rotation
                self.rollover_at = self.compute_rollover(dt.datetime.now())

            except Exception as error:
                # Raise an exception with additional context if any errors occur during the rollover process
                raise Exception(
                    f"An error occurred during the log file rollover process: {error}"
                ) from error

    @override
    def emit(self, record: LogRecord) -> None:
        """
        Processes and writes a log record. Triggers rollover if necessary.

        This method ensures that rollover is performed either due to exceeding file size or reaching
        the scheduled time threshold.

        :param record: The log record being logged.
        """
        # Ensure thread-safe access to log file operations using a reentrant lock
        with self.reentrant_lock:
            try:
                # Check if rollover conditions are met and perform rollover if necessary
                if self.should_rollover(record):
                    self.do_rollover()  # Perform rollover (e.g., rotate log file)

                # Format the log record into a string
                log_entry = self.format(record)

                # Write the formatted log entry to the stream and append the terminator
                self.stream.write(log_entry + self.terminator)

                # Flush the buffer to ensure immediate write to the file or output stream
                self.stream.flush()

            except Exception as error:
                # Raise an exception with additional context if any errors occur during the emit process
                raise Exception(f"An error occurred while emitting: {error}") from error

                # Log the exception with traceback info for debugging
                # logging.exception(error, exc_info = True); self.handle_error(self, record)


class JSONLFileHandler(DualRotatingHandler):
    """
    A custom logging handler that writes log messages to a file with a `.jsonl` extension.
    This handler supports both size-based and time-based log file rotation. The `.jsonl`
    extension ensures compatibility with systems expecting logs in JSON line format.

    Inherits from `DualRotatingHandler` to provide rotation functionality based on file size
    and time, allowing for automatic log file management with options for backup retention.
    """

    def __init__(
        self,
        file_name: str,
        mode: Literal["a", "w", "x", "r+", "w+"] = "a",
        max_bytes: int = 0,
        backup_count: int = 0,
        interval: int = 1,
        when: Literal[
            "S", "M", "H", "D", "MIDNIGHT", "W0", "W1", "W2", "W3", "W4", "W5", "W6"
        ] = "MIDNIGHT",
        at_time: Optional[dt.time] = None,
        encoding: Optional[str] = None,
        delay: bool = False,
        errors: Optional[str] = None,
        backup_extension_type: Literal["count", "time"] = "count",
    ) -> None:
        """
        Initializes an instance of JSONLFileHandler to manage log rotation and log writing to a `.jsonl` file.

        :param file_name: The full path to the log file where the logs will be written. Must end with `.jsonl`.
        :param mode: The file opening mode. Default is 'a' for append, 'w' for overwrite, etc.
        :param max_bytes: The maximum size (in bytes) of the log file before rotation occurs.
        :param backup_count: The maximum number of backup files to retain.
        :param interval: The interval value for time-based rotation.
        :param when: Specifies the rotation interval (e.g., 'MIDNIGHT', 'D' for daily).
        :param at_time: A `datetime.time` object indicating a specific time for rotation.
        :param encoding: Encoding of the log file. Defaults to None.
        :param delay: If True, delays log file creation until the first write operation.
        :param errors: Specifies error handling for encoding issues.
        :param backup_extension_type: Determines the naming pattern for backups ('count' or 'time').

        :raise ValueError: Raised if the filename does not end with `.jsonl` or any other parameter is invalid.
        """
        # Validate that the file name ends with a `.json` extension
        if not file_name.endswith(".jsonl"):
            raise InvalidLogFileExtensionError(file_name, ".jsonl")

        # Call the parent class constructor with all parameters
        super().__init__(
            file_name,
            mode,
            max_bytes,
            backup_count,
            interval,
            when,
            at_time,
            encoding,
            delay,
            errors,
            backup_extension_type,
        )


class DiscordWebHookHandler(Handler):
    """
    A custom logging handler that sends log messages to a Discord webhook asynchronously.
    This handler buffers log messages and sends them in batches to avoid spamming the Discord API,
    ensuring compliance with rate limits. It supports controlled buffering, periodic flushing,
    and configurable throttling to prevent exceeding Discord's API rate limits.

    Inherits from `logging.Handler` to provide asynchronous logging functionality.
    """

    def __init__(
        self,
        webhook_id: str,
        webhook_token: str,
        *,
        capacity: int = 100,
        flush_interval: float = 30.0,
        throttle_limit: float = 1.0,
        flush_on_close: bool = False,
        proxy: Optional[str] = None,
    ) -> None:
        """
        Initializes an instance of DiscordWebHookHandler to manage logging to a Discord webhook
        with controlled buffering, rate limiting, and optional proxy.

        :param webhook_id: The Discord Webhook ID, extracted from the webhook URL.
        :param webhook_token: The Discord Webhook Token, extracted from the webhook URL.
        :param capacity: Maximum number of log records to buffer before forcing a flush.
                        Defaults to 100 records.
        :param flush_interval: Time interval (in seconds) between automatic flush attempts.
                               Defaults to 30.0 seconds.
        :param throttle_limit: Minimum time (in seconds) between consecutive webhook requests
                               to prevent spamming the Discord API. Defaults to 1.0 second.
        :param flush_on_close: Whether to flush remaining logs in the buffer when the handler
                               is closed. Defaults to True.
        :param proxy: Optional HTTP or SOCKS5 proxy URL for the aiohttp session.
                      Useful for environments where direct internet access is restricted.
        """
        # Construct the webhook URL using the provided webhook ID and token
        self._webhook_url = (
            f"https://discord.com/api/webhooks/{webhook_id}/{webhook_token}"
        )

        # Initialize the parent class (logging.Handler)
        super().__init__()

        # Configure handler parameters
        self.capacity = capacity  # Maximum buffer size
        self.flush_interval = flush_interval  # Time between periodic flushes
        self.throttle_limit = throttle_limit  # Minimum time between API requests
        self.flush_on_close = flush_on_close  # Whether to flush on handler closure
        self.proxy = proxy  # Optional proxy for network requests

        # State management variables
        self.buffer = []  # Buffer to store log records
        self.last_sent_time = (
            time.time()
        )  # Stores the time of the last successful log transmission
        self.reentrant_lock = (
            threading.RLock()
        )  # Reentrant lock for thread-safe buffer operations

        # Initialize asynchronous infrastructure
        self.loop = (
            asyncio.new_event_loop()
        )  # Dedicated event loop for async operations

        self.loop_thread = threading.Thread(
            target=self.start_loop,
            args=(self.loop,),
            daemon=True,  # Ensure the thread terminates with the main program
        )
        self.loop_thread.start()  # Start the event loop in a separate thread

        # Start the periodic flush task in the event loop
        self.flush_task = self.loop.create_task(self._periodic_flush())

        # Validate the handler parameters and verify the webhook URL
        if not self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self._validate_parameters(), self.loop)

    @staticmethod
    def start_loop(loop: asyncio.AbstractEventLoop) -> None:
        """
        A static method to start the event loop in a separate thread.
        This method sets the provided event loop as the current event loop
        and runs it indefinitely.

        :param loop: The asyncio event loop to run.
        """
        asyncio.set_event_loop(loop)
        loop.run_forever()

    async def _validate_parameters(self) -> None:
        """
        Validates the parameters provided during the initialization of the handler.
        This method ensures that all configuration values are valid and performs
        a test request to verify that the webhook URL is functional.

        :raise ValueError: Raised for invalid webhook IDs, tokens, or other invalid parameters.
        """
        # Validate flush interval
        if (
            not isinstance(self.flush_interval, (int, float))
            or self.flush_interval <= 0
        ):
            raise ValueError("Flush interval must be a positive number.")

        # Validate throttle limit
        if (
            not isinstance(self.throttle_limit, (int, float))
            or self.throttle_limit <= 0
        ):
            raise ValueError("Throttle limit must be a positive number.")

        # Validate buffer capacity
        if not isinstance(self.capacity, int) or self.capacity <= 0:
            raise ValueError("Buffer capacity must be a positive integer.")

        # Validate proxy URL format
        if self.proxy is not None:
            valid_schemes = ("http://", "https://", "socks5://")
            if not any(self.proxy.startswith(scheme) for scheme in valid_schemes):
                raise ValueError(f"Proxy URL must start with one of: {valid_schemes}.")

        # Verify webhook functionality by sending a test payload
        test_payload = {"content": "Initializing webhook connection..."}

        try:
            await self._send_logs_to_webhook(test_payload)
        except InvalidWebhookStatusCodeError as error:
            raise ValueError(f"Webhook validation failed: {str(error)}")

    async def _send_logs_to_webhook(self, payload: Dict[str, Any]) -> None:
        """
        Asynchronous method to send log messages to the webhook URL.
        This method handles the actual HTTP request to Discord's API and ensures
        proper error handling for network issues and API errors.

        :param payload: The log data to be sent to the webhook, formatted as a dictionary.
        :raise ConnectionError: Raised for network-related failures.
        :raise InvalidWebhookStatusCodeError: Raised for non-2xx Discord API responses.
        """
        try:
            # Configure a TCPConnector to control connection settings
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=10, ssl=False)

            # Create a timeout configuration for the entire session
            session_timeout = aiohttp.ClientTimeout(total=60)

            # Create an aiohttp session to send the POST request
            async with aiohttp.ClientSession(
                timeout=session_timeout, connector=connector, trust_env=True
            ) as session:
                async with session.post(
                    url=self._webhook_url,
                    json=payload,  # type: ignore
                    proxy=self.proxy,
                    allow_redirects=False,  # Disable automatic redirection
                ) as response:
                    # Discord returns 204 (No Content) for successful requests
                    if response.status != 204:
                        raise InvalidWebhookStatusCodeError(
                            f"Discord API error: {response.status} - {await response.text()}"
                        )
        except aiohttp.ClientError as error:
            # Handle network-related errors
            raise ConnectionError(
                f"Network communication failed: {str(error)}"
            ) from error

    @staticmethod
    def _is_valid_embed(embed: Dict[str, Any]) -> bool:
        """
        Validates whether the provided dictionary is a valid Discord embed.

        :param embed: The embed dictionary to validate.
        :return: True if the embed is valid, False otherwise.
        """
        if not isinstance(embed, dict):
            return False

        # Check for at least one required field in the embed
        required_fields = [
            "title",
            "description",
            "url",
            "timestamp",
            "color",
            "footer",
            "image",
            "thumbnail",
            "video",
            "provider",
            "author",
            "fields",
        ]
        return any(field in embed for field in required_fields)

    async def _flush(self) -> None:
        """
        Asynchronously flushes the buffered log records to the Discord webhook.

        This method checks the buffer, formats the log messages, and sends them to the webhook in batches.
        It also handles rate limiting to ensure logs are not sent too frequently. The method is thread-safe
        and ensures that logs are not lost during the flush process.
        """
        # Reentrant lock allows nested calls and ensures thread-safe buffer access
        with self.reentrant_lock:
            # Do nothing if the buffer is empty
            if not self.buffer:
                return None  # type: ignore

            # Initialize a list to hold the formatted content, either embeds or plain text messages
            payload_content = []

            # Check if the formatter has a batch_format method for efficient batch processing
            if self.formatter is not None and hasattr(self.formatter, "format_batch"):
                # Use format_batch to handle batch formatting for efficiency
                batch_result = self.formatter.format_batch(self.buffer)  # type: ignore

                # Check if the batch result is a list and contains valid embeds
                if isinstance(batch_result, list) and len(batch_result) > 0:  # type: ignore
                    # Add the embeds directly to payload content, validating their structure
                    for embed in batch_result:  # type: ignore
                        # Validate each embed's structure and ensure each embed is a dictionary
                        if self._is_valid_embed(embed):  # type: ignore
                            payload_content.append(embed)  # type: ignore

            # Fallback to individual formatting for each record if batch formatting is not available
            else:
                for record in self.buffer:  # type: ignore
                    # If a custom formatter is provided, use it to format the log record
                    formatted_message = self.formatter.format(record) if self.formatter is not None else self.format(record)  # type: ignore

                    # Handle plain text content
                    if isinstance(formatted_message, str):
                        payload_content.append({"content": formatted_message})  # type: ignore

                    # Handle embed dictionaries
                    elif (
                        isinstance(formatted_message, dict)
                        and "embeds" in formatted_message
                    ):
                        # Extract the embed from the formatted message
                        embed = formatted_message["embeds"][0]
                        if self._is_valid_embed(embed):  # Validate embed structure
                            payload_content.append(embed)  # type: ignore

            # Prepare the payload for the Discord webhook only if there's something to send
            if payload_content:
                # Separate valid embeds and plain text content
                embeds = [item for item in payload_content if isinstance(item, dict) and self._is_valid_embed(item)]  # type: ignore
                content = "\n".join(item["content"] for item in payload_content if "content" in item)  # type: ignore

                # Initialize the payload dictionary
                payload = {}

                # Add embeds to the payload if they exist
                if embeds:
                    payload["embeds"] = (
                        embeds  # Ensure the embeds key contains a list of dictionaries
                    )

                # Add content to the payload if plain text exists
                if content:
                    payload["content"] = (
                        content  # Concatenate all plain text messages into one
                    )

                # Send the payload to the Discord webhook
                await self._send_logs_to_webhook(payload)  # type: ignore

                # Update the timestamp of the last successful log send to enforce throttling
                self.last_sent_time = time.time()

                # Clear the buffer after the logs are successfully sent
                self.buffer.clear()  # type: ignore

    async def _periodic_flush(self) -> None:
        """
        Periodically flushes the log buffer to the Discord webhook at the specified interval.
        This method runs continuously in the background event loop and ensures that logs
        are sent even if the buffer does not reach capacity.

        The flush interval is configurable via the `flush_interval` parameter.
        """
        while True:
            await asyncio.sleep(self.flush_interval)
            asyncio.run_coroutine_threadsafe(self._flush(), self.loop)

    def should_flush(self, record: LogRecord) -> bool:
        """
        Determines if the buffer should be flushed immediately.
        This method checks if the buffer has reached its capacity or if the log record
        is marked as urgent.

        :param record: The log record to evaluate.
        :return: True if the buffer should be flushed, False otherwise.
        """
        return (hasattr(record, "is_urgent") and record.is_urgent) or len(self.buffer) >= self.capacity  # type: ignore

    @override
    def emit(self, record: LogRecord) -> None:
        """
        Processes a log record: buffers the record and triggers a flush when appropriate.
        This method is called by the logging framework whenever a log record is emitted.

        :param record: A logging.LogRecord instance to handle.
        """
        # Reentrant lock for thread-safe buffer access
        with self.reentrant_lock:
            # Always buffer the record first
            self.buffer.append(record)  # type: ignore

            # Flush immediately if buffer reached its capacity, record is marked urgent or throttle period has expired
            if self.should_flush(record) or (
                time.time() - self.last_sent_time >= self.throttle_limit
            ):
                asyncio.run_coroutine_threadsafe(self._flush(), self.loop)

    @override
    def close(self) -> None:
        """
        Cleans up resources and cancels the periodic flush task.
        This method is called when the handler is closed to ensure that all resources
        are properly released and any remaining logs are flushed if configured to do so.
        """
        if self.flush_on_close:
            asyncio.run_coroutine_threadsafe(
                self._flush(), self.loop
            ).result()  # Flush remaining logs if configured

        if not self.flush_task.cancelled():
            self.flush_task.cancel()  # Cancel the periodic flush task
        super().close()  # Call the parent class's close method
