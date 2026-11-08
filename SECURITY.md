# Security policy

TripWir3 is a research prototype. It has no supported production release or guaranteed security response time. Audit results describe the tested inputs and model artifact; they are not a safety certification.

## Report a vulnerability privately

Use the repository's [private vulnerability reporting page](https://github.com/mukherjeeabhirup/hackutd2026-initial/security/advisories/new) if GitHub enables it for your account. If it is unavailable, contact the repository owner through an existing private channel. If you have no private contact, open an issue asking only for a secure contact method; omit vulnerability details and sensitive data.

Include the affected version, component, expected and observed behavior, impact, and a minimal reproduction with dummy credentials. Do not publish API keys, tokens, private keys, private model data or raw provider logs in issues, pull requests or attachments.

If a credential may have been exposed, notify its owner and stop publication. The owner should revoke or rotate it with the provider and decide how to remediate the repository. Removing a file in a new commit does not remove it from Git history. Do not rewrite shared history without coordination.

## Local operation

Keep credentials in ignored local environment files, restrict their permissions, and use placeholders in examples. Keep local model services bound to loopback with authentication enabled. Review saved evidence before sharing it. Report software defects separately from limitations in model detection accuracy.
