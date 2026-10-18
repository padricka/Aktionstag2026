## 2026-10-17 - [Remove Hardcoded Secret Key Fallback]
**Vulnerability:** Found a hardcoded string used as a fallback for Django's SECRET_KEY in production.
**Learning:** Hardcoded fallbacks in configuration allow attackers to guess session tokens or CSRF tokens if the environment variable is accidentally omitted. The correct approach in Django is to raise an ImproperlyConfigured exception so the service fails securely, or only use the insecure fallback during development (DEBUG=True).
**Prevention:** Never use hardcoded security keys as fallbacks. Always validate the presence of sensitive environment variables and raise an exception if they are missing in production environments.
