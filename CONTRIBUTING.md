# Contributing to Organizer Chat Bot

Thank you for your interest in improving this project! Bug reports, feature suggestions, documentation improvements, and code contributions are welcome. Please read the following guidelines before opening an issue or submitting changes.

## Bug Reports

Before reporting a bug, please make sure that the problem has not already been reported.

1. **Describe the Problem:** Clearly explain what happened and what you expected to happen.

2. **Steps to Reproduce:** Provide a step-by-step description of the actions that caused the problem. If the issue occurred during a scan or bot session, include the selected chat, time window, prompt, and relevant settings when applicable.

3. **Error Messages and Logs:** Include the complete relevant error message or log output. **Remove API keys, Telegram credentials, session information, personal messages, usernames, IDs, and other sensitive information before submitting.**

4. **Environment:** When relevant, include:

   * Operating system
   * Python version
   * Project version or commit
   * Installation method (local or Docker)
   * AI provider being used (OpenRouter or Google AI Studio)
   * Relevant configuration options

5. **Reproducibility:** If possible, provide a minimal example or the smallest set of steps that consistently reproduces the issue.

> **Privacy:** Do not upload your Telethon `.session` file, `.env` file, API keys, or private Telegram messages to an issue.

## Feature Requests

If you have an idea for improving the project, open an issue and describe:

1. **The proposed feature:** Explain clearly what you want to add or change.
2. **The reason:** Explain what problem it solves or why it would be useful.
3. **Expected behavior:** Describe how the feature should work from the user's perspective.
4. **Possible implementation:** If you have an implementation idea, you are welcome to include it.

Features involving access to Telegram data should be designed with privacy and the project's read-only architecture in mind.

## Improving the Repo

Contributions to the codebase are welcome through pull requests.

1. **Fork the Repository:** Fork the project and make your changes in your own fork.

2. **Keep Changes Focused:** Each pull request should focus on one bug, feature, or improvement whenever possible.

3. **Respect the Read-Only Design:** Changes must not introduce functionality that modifies, deletes, reacts to, or otherwise alters messages or other Telegram content unless the project's intended behavior is explicitly changed.

4. **Protect Credentials and Private Data:** Never commit API keys, Telegram sessions, `.env` files, personal Telegram data, or other secrets.

5. **Test Your Changes:** Test the affected functionality before submitting the pull request. If your change affects Telegram interaction, AI analysis, configuration, or Docker execution, test the relevant path when possible.

6. **Keep Configuration Consistent:** Configuration should remain centralized through the project's settings system rather than introducing unrelated direct environment-variable access.

7. **Describe Your Changes:** Explain what was changed, why it was changed, and how it was tested.

8. **Code Quality:** Keep the implementation consistent with the existing project structure, naming conventions, type hints, and asynchronous design.

## Security and Privacy

This project works with a user's Telegram account and potentially private messages. Contributions must take this into account.

* Do not add unauthorized data collection.
* Do not send Telegram data to third-party services other than the explicitly configured AI provider or intended destination.
* Do not expose credentials, session data, or private messages through logs.
* Do not introduce code that secretly modifies or deletes Telegram content.
* Do not intentionally weaken the authorization restrictions of the bot.
* Do not commit secrets or sensitive user data.

Security or privacy issues should not be publicly disclosed with credentials or private data included in the report.

## Pull Requests

When submitting a pull request:

* Use a clear title describing the change.
* Explain the problem and the solution.
* Mention any important design decisions.
* Include testing information.
* Keep unrelated changes out of the pull request.

Pull requests may require changes before they can be merged.

## General Guidelines

Please keep discussions and contributions respectful and focused on improving the project.

By contributing, you agree that your contribution should be suitable for distribution with the project's existing license and should not contain malicious behavior, unauthorized data collection, credential theft, or other harmful functionality.
