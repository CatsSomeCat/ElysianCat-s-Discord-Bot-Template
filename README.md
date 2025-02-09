# 😺 ElysianCat's Discord Bot Template

---

[![Pre-commit](https://img.shields.io/badge/pre--commit-disabled-lightgrey?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/Python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![Discord.py](https://img.shields.io/badge/discord.py-2.3.2+-blue.svg)](https://discordpy.readthedocs.io/)
[![GitHub Stars](https://img.shields.io/github/stars/CatsSomeCat/ElysianCat-s-Discord-Bot-Template?style=social)](https://github.com/CatsSomeCat/ElysianCat-s-Discord-Bot-Template/stargazers)
[![GitHub Release](https://img.shields.io/github/v/release/CatsSomeCat/ElysianCat-s-Discord-Bot-Template?label=Latest%20Version)](https://github.com/CatsSomeCat/ElysianCat-s-Discord-Bot-Template/releases)

---

**ElysianCat's Discord Bot Template** is a lightweight, highly customizable template designed for building Discord bots.

While it doesn't come with pre-built features like moderation or entertainment commands, it provides a robust foundation with advanced logging, utilities, and a modular structure.

This makes it perfect for developers who want to create a bot tailored to their specific needs without starting from scratch.

---

## 🌟 Features

- **Advanced Logging**: Configurable multi-channel logging with JSON configuration.
- **Environment Management**: Secure token handling with `.env` files.
- **Dev/Prod Ready**: Built-in support for different environments.
- **Utilities**: A collection of useful utility functions and decorators to simplify development.
- **Extensible**: Designed to be easily extended with new features and integrations.

---

## 🛠️ Prerequisites

- Python 3.13 or newer.
- A Discord bot token (obtained from the [Discord Developer Portal](https://discord.com/developers/applications)).
- `discord.py` library installed (`pip install discord.py`).

---

## ⚡ Quick Installation

1. Clone the repository:
   ```bash
   git clone "https://github.com/CatsSomeCat/ElysianCat-s-Discord-Bot-Template.git"
   ```

2. Navigate to the project directory:
    ```bash
    cd ElysianCat-Discord-Bot-Template
    ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt # If using pip
   ```

   ```bash
   poetry install # If using poetry
   ```

4. Run the bot:
    ```bash
   python main.py
    ```

---

> **Note**: Depending on your system configuration, you may need to replace `python` with the appropriate Python command, such as `py`, `python3`, `python3.13`, or another version-specific command. To check which Python versions are installed, run:
> ```bash
> python --version
> python3 --version
> ```
> Ensure you use the correct command that corresponds to the required Python version (3.13 or higher) for this project.

---

## 🤖 Configure the Bot

1. **Environment Configuration:**
   - Rename `.example.env` to `.env`.
   - Add your Discord bot token, application ID, and other necessary details in the `.env` file.

2. **Logging Configuration:**
   - Rename `logging_config.example.json` to `logging_config.json`.
   - Customize the logging settings in the `logging_config.json` file to suit your needs.

3. **Bot Configuration:**
   - Rename `config.example.json` to `config.json`.
   - Modify the settings in the `config.json` file to configure the bot according to your preferences.

---

## 🔧 Configuration

Customize `logging_config.json` to tailor the logging behavior to your needs. Here's what you can configure:

1. **File Logging Paths**: Specify where log files are saved.
2. **Log Levels**: Set different log levels (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL).
3. **Formatting Styles**: Customize the format of log messages (e.g., timestamp, log level, message).
4. **Rotation Policies**: Configure log file rotation based on size, time or even both simultaneously.

### Custom Formatters

1. **`simple`**: Basic log format for file logging.
2. **`colorized`**: Colorized log format for console output.
3. **`discord_embed`**: Formats logs into Discord embed messages.
4. **`JSONLFormatter` (unused)**: Formats logs into JSON Lines (JSONL) format.

### Custom Handlers

1. **`console`**: Outputs logs to the console.
2. **`file`**: Writes logs to a file with rotation support.
3. **`discord`**: Sends logs to a Discord channel via a webhook.

### Custom Implementation

The bot includes custom handlers and formatters located in `logging_.handlers` and `logging._formatters`:

---

```python
__all__ = (
    "DualRotatingHandler",
    "JSONLFileHandler",
    "DiscordWebHookHandler",
)
```

---

```python
__all__ = (
    "ColorizedFormatter",
    "JSONLFormatter",
    "DiscordEmbedLoggingFormatter",
)
```

---

### Example `logging_config.json` File:
```json
{
  "version": 1,
  "disable_existing_loggers": false,
  "formatters": {
    "standard": {
      "format": "%(asctime)s - %(levelname)s - %(message)s"
    }
  },
  "handlers": {
    "file_handler": {
      "class": "logging.handlers.RotatingFileHandler",
      "filename": "logs/bot.log",
      "maxBytes": 10485760,
      "backupCount": 5,
      "formatter": "standard"
    },
    "console_handler": {
      "class": "logging.StreamHandler",
      "formatter": "standard"
    }
  },
  "loggers": {
    "": {
      "handlers": ["file_handler", "console_handler"],
      "level": "INFO",
      "propagate": true
    }
  }
}
```

---

## 📅 Versioning

We use [CalVer](http://semver.org) for versioning. CalVer is a versioning scheme based on project release dates, making it easy to track when a version was released and how old it is.
See the [tags on this repository](https://github.com/CatsSomeCat/ElysianCat's-Discord-Bot-Template/tags).

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a new branch (git checkout -b feature-branch).
3. Commit your changes (git commit -m "Add new feature").
4. Push to the branch (git push origin feature-branch).
5. Open a Pull Request.

---

## 📝 License
This project is licensed under the MIT License. See [LICENSE](LICENSE.txt) for details.

---

## 💬 Discord
Join our Discord community for support, updates, and discussions!

[![Discord](https://img.shields.io/discord/1280221378338881606?label=Join%20Our%20Discord&logo=discord&style=for-the-badge)](https://discord.gg/qjucAQEWNU)

- **Get help**: Ask questions and troubleshoot issues with the community.
- **Share ideas**: Suggest new features or improvements.
- **Stay updated**: Be the first to know about new releases and updates.

---

## ❤️ Donate

If you find this project helpful, consider supporting its development! Your donations help keep the project alive and improve its features.

### Donation Options:
- **Coming Soon**: We're working on setting up donation options. Stay tuned for updates!
- **Support Us**: In the meantime, you can support us by starring the repository, sharing it with others, or contributing code.

Every contribution, no matter how small, is greatly appreciated! Thank you for your support.
