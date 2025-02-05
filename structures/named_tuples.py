from typing import NamedTuple, Optional

from ._mixins import TupleUtilsMixin

# Explicitly export specific names to be available in the module's namespace
# This helps in controlling which names are exposed when the module is imported
__all__ = ("EnvVariables",)


# Define a structured, immutable container for storing environment variables
@TupleUtilsMixin
class EnvVariables(NamedTuple):
    """
    A container for storing environment variables relevant to the application.

    This class provides a structured way to store and access environment variables such as
    webhook credentials and application tokens that are essential for the application.

    :ivar logging_webhook_token: The authentication token used for the webhook.
    :ivar logging_webhook_id: The unique identifier for the webhook.
    :ivar bot_token: The bot authentication token.
    :ivar application_id: The application’s unique identifier.
    """

    logging_webhook_token: Optional[str]
    logging_webhook_id: Optional[str]
    bot_token: Optional[str]
    application_id: Optional[str]
