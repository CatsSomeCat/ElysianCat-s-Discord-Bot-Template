from logging import Filter, LogRecord
from typing import Iterable, Set, Union, override

from enums import LogSeverity


class IgnoreSpecificLevelFilter(Filter):
    """
    A custom logging filter that excludes log records matching specified severity levels.

    This filter can be used to suppress log messages of specific severity levels (e.g., DEBUG, INFO)
    while allowing others to pass through. It supports both single levels and collections of levels
    for flexible filtering.
    """

    def __init__(
        self, level_or_levels: Union[LogSeverity, Iterable[LogSeverity]] = (), /
    ) -> None:
        """
        Initializes an instance of the filter with level(s) to exclude.

        :param level_or_levels: Single level or collection of levels to filter out.
                               If not provided, no levels are filtered by default.
        """
        super().__init__()  # Initialize the base Filter class
        self._levels: Set[int] = set()  # Internal set to store filtered level values

        # Convert input levels to their numeric values for efficient comparison
        if isinstance(level_or_levels, LogSeverity):
            # Handle single level input
            self._levels.add(level_or_levels.value)
        elif isinstance(level_or_levels, Iterable):
            # Handle collection of levels
            self._levels = {level.value for level in level_or_levels}

    @property
    def levels(self) -> Set[int]:
        """
        Gets the numeric values of filtered levels as a read-only set.

        :return: A copy of the internal set containing the numeric values of filtered levels.
        """
        return self._levels.copy()  # Return a copy to prevent external modification

    @override
    def filter(self, record: LogRecord) -> bool:
        """
        Determines if the specified log record should be logged.

        This method is called by the logging framework for each log record. It checks whether
        the record's severity level matches any of the filtered levels.

        :param record: LogRecord instance containing logging metadata, including the severity level.
        :return: False if the record's level matches any of the filtered levels, True otherwise.
        """
        # Check if the record's level is in the filtered levels set
        return record.levelno not in self._levels
