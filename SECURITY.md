# Security Policy

## Reporting a Security Vulnerability

The Organizer Chat Bot interacts with a user's Telegram account and may process private messages. Security and privacy issues should therefore be reported responsibly.

If you believe you have found a security vulnerability, **do not open a public GitHub Issue with sensitive details**.

Instead, report the vulnerability privately to the project maintainer through the available private contact method.

When reporting a vulnerability, please provide:

1. **Description:** A clear explanation of the security issue.
2. **Impact:** Explain what an attacker could access, modify, or cause.
3. **Reproduction Steps:** Provide the minimum steps required to reproduce the issue.
4. **Affected Component:** Identify the relevant file, feature, or configuration.
5. **Suggested Fix:** If you have an idea for fixing the vulnerability, include it.

Please do not include real API keys, Telegram session files, private messages, passwords, or other sensitive information in the report.

## What Should Be Reported Privately?

Examples of security issues include:

* Exposure or leakage of Telegram API credentials.
* Exposure or leakage of BotFather tokens or AI provider API keys.
* Theft or unauthorized use of Telethon session data.
* Unauthorized access to the bot interface or another user's data.
* Bypassing the configured `ALLOWED_USER_ID` authorization.
* Unauthorized modification, deletion, or interaction with Telegram content.
* Sending private Telegram data to an unauthorized third-party service.
* Sensitive information being exposed through logs or error messages.
* Vulnerabilities that allow an attacker to execute arbitrary code.
* Vulnerabilities that allow unauthorized access to the configured AI providers or other services.
* Any issue that could compromise the privacy or security of the Telegram account using the bot.

## What Does Not Usually Require a Security Report?

Regular bugs that do not create a security or privacy risk should normally be reported through a regular GitHub Issue.

Examples include:

* Incorrect UI behavior.
* Incorrect message filtering.
* AI analysis producing unexpected results.
* Normal configuration errors.
* Installation or Docker problems.
* Performance problems without a security impact.

If you are unsure whether an issue is a security vulnerability, **treat it as a security issue and report it privately**.

## Sensitive Data

Because this project can access Telegram messages, contributors and users must take particular care when sharing diagnostic information.

**Never publicly post:**

* `.env` files.
* Telegram API ID/Hash.
* Bot tokens.
* AI provider API keys.
* Telethon `.session` files.
* Private Telegram messages.
* Private chat identifiers when they could expose sensitive information.
* Authentication codes or passwords.
* Logs containing sensitive information.

Before attaching logs to an issue or pull request, review and remove sensitive information.

## Security Expectations for Contributions

Contributions must not:

* Collect Telegram data without a legitimate purpose.
* Send user data to unauthorized servers.
* Expose credentials or session information.
* Disable or bypass authorization controls.
* Introduce hidden telemetry or tracking.
* Intentionally weaken the read-only behavior of the userbot.
* Store private Telegram data unnecessarily.
* Execute remote or untrusted code without an explicit and justified purpose.

Any contribution that introduces malicious behavior, unauthorized data collection, credential theft, or intentional security weaknesses will not be accepted.

## Disclosure

Please allow the maintainer reasonable time to investigate and address a privately reported vulnerability before publicly disclosing technical details.

Once a vulnerability has been investigated and, when appropriate, fixed, the maintainer may publish a security advisory or other disclosure containing the necessary information without exposing private user data or credentials.

## Scope

This security policy applies to the Organizer Chat Bot repository and its source code, configuration, deployment files, and officially maintained components.

Third-party services such as Telegram, OpenRouter, Google AI Studio, Docker, and Telethon have their own security policies and are outside the direct control of this project.
