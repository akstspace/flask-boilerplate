"""Authentication service"""

from functools import lru_cache

import jwt
import requests
from flask import current_app
from loguru import logger

from app.core.exceptions import AuthenticationError


class KeycloakAuthService:
    """Handle Keycloak JWT token verification"""

    def __init__(self):
        """
        Initialize a KeycloakAuthService instance.
        
        Sets up internal state, including an internal `_public_key` placeholder used for caching a resolved public key.
        """
        self._public_key = None

    @property
    def keycloak_url(self) -> str:
        """
        Retrieve the configured Keycloak server base URL.
        
        Returns:
            The Keycloak server URL from the application configuration key `KEYCLOAK_SERVER_URL`.
        """
        return current_app.config["KEYCLOAK_SERVER_URL"]

    @property
    def realm(self) -> str:
        """
        Keycloak realm name from the Flask application configuration.
        
        Returns:
            str: The realm configured under the `KEYCLOAK_REALM` application setting.
        """
        return current_app.config["KEYCLOAK_REALM"]

    @property
    def certs_url(self) -> str:
        """
        Construct the JWKS (JSON Web Key Set) endpoint URL for the configured Keycloak realm.
        
        Returns:
            str: The Keycloak certificates (JWKS) endpoint URL.
        """
        return f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/certs"

    @lru_cache(maxsize=128)
    def _get_jwks(self) -> dict:
        """
        Retrieve the JWKS (JSON Web Key Set) from the configured Keycloak server.
        
        The fetched JWKS is cached per-process to avoid repeated network requests.
        
        Returns:
            dict: Parsed JWKS JSON payload.
        
        Raises:
            AuthenticationError: If the JWKS cannot be fetched or the response cannot be processed.
        """
        try:
            response = requests.get(self.certs_url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch JWKS from Keycloak: {e!s}")
            msg = "Unable to verify token"
            raise AuthenticationError(msg)

    def _get_public_key_by_kid(self, kid: str) -> str:
        """
        Return the PEM-formatted public key that matches the given key ID (kid) from the JWKS.
        
        Parameters:
            kid (str): Key ID from a JWT header used to locate the corresponding JWK.
        
        Returns:
            str: Public key in PEM format (UTF-8 string).
        """
        jwks = self._get_jwks()

        if "keys" not in jwks:
            msg = "Invalid JWKS response: 'keys' field not found"
            raise ValueError(msg)

        # Find the key matching the kid
        for key_data in jwks["keys"]:
            if key_data.get("kid") == kid:
                # Convert JWK to PEM format using python-jose
                from jose import jwk

                public_key = jwk.construct(key_data)
                return public_key.to_pem().decode("utf-8")

        msg = f"Public key with kid '{kid}' not found in JWKS"
        raise ValueError(msg)

    def verify_token(self, token: str) -> dict | None:
        """
        Verify JWT token from Keycloak

        Args:
            token: JWT token string

        Returns:
            Dict: Decoded token payload if valid

        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                msg = "Token missing 'kid' in header"
                raise AuthenticationError(msg)

            public_key = self._get_public_key_by_kid(kid)

            return jwt.decode(
                token,
                public_key,
                algorithms=[current_app.config["JWT_ALGORITHM"]],
                audience=current_app.config.get("KEYCLOAK_CLIENT_ID"),
                options={
                    "verify_signature": current_app.config["JWT_VERIFY_SIGNATURE"],
                    "verify_exp": current_app.config["JWT_VERIFY_EXPIRATION"],
                    "verify_aud": (
                        bool(current_app.config.get("KEYCLOAK_CLIENT_ID"))
                    ),
                },
                leeway=current_app.config["JWT_LEEWAY"],
            )


        except jwt.ExpiredSignatureError:
            msg = "Token has expired"
            raise AuthenticationError(msg)
        except jwt.InvalidTokenError as e:
            msg = f"Invalid token: {e!s}"
            raise AuthenticationError(msg)
        except ValueError as e:
            logger.error(f"Key verification error: {e!s}")
            msg = "Token verification failed"
            raise AuthenticationError(msg)
        except Exception as e:
            logger.exception(f"Token verification error: {e!s}")
            msg = "Token verification failed"
            raise AuthenticationError(msg)

    def extract_user_info(self, decoded_token: dict) -> dict:
        """
        Extract a user's profile and role information from a decoded Keycloak JWT payload.
        
        Parameters:
            decoded_token (dict): Decoded JWT payload as returned by JWT decode.
        
        Returns:
            dict: A mapping with keys:
                - user_id: Subject identifier (`sub`).
                - username: Preferred username (`preferred_username`).
                - email: Email address (`email`).
                - email_verified: Boolean indicating if email is verified (`email_verified`, defaults to False).
                - name: Full name (`name`).
                - given_name: Given name (`given_name`).
                - family_name: Family name (`family_name`).
                - roles: Realm-level roles (from `realm_access.roles`, defaults to []).
                - client_roles: Client-level roles for the configured Keycloak client (from `resource_access[KEYCLOAK_CLIENT_ID].roles`, defaults to []).
        """
        return {
            "user_id": decoded_token.get("sub"),
            "username": decoded_token.get("preferred_username"),
            "email": decoded_token.get("email"),
            "email_verified": decoded_token.get("email_verified", False),
            "name": decoded_token.get("name"),
            "given_name": decoded_token.get("given_name"),
            "family_name": decoded_token.get("family_name"),
            "roles": decoded_token.get("realm_access", {}).get("roles", []),
            "client_roles": decoded_token.get("resource_access", {})
            .get(current_app.config.get("KEYCLOAK_CLIENT_ID", ""), {})
            .get("roles", []),
        }


class JWKSAuthService:
    """Handle JWT token verification via a generic JWKS endpoint (e.g. Hanko, Clerk, custom providers)"""

    def __init__(self):
        """
        Initialize a JWKSAuthService instance.

        The PyJWKClient is created lazily on first use so that Flask app config
        is available at verification time.
        """
        self._jwks_client = None

    def _get_jwks_client(self):
        """
        Return a cached PyJWKClient, creating it on first access from Flask config.

        Returns:
            PyJWKClient: A client configured with the JWKS_URL from app config.
        """
        if self._jwks_client is None:
            from jwt import PyJWKClient

            self._jwks_client = PyJWKClient(current_app.config["JWKS_URL"])
        return self._jwks_client

    @property
    def jwks_url(self) -> str:
        """
        Retrieve the configured JWKS endpoint URL.

        Returns:
            str: The JWKS URL from the application configuration key ``JWKS_URL``.
        """
        return current_app.config["JWKS_URL"]

    @property
    def issuer(self) -> str | None:
        """
        Retrieve the expected token issuer.

        Returns:
            str | None: The issuer from the ``JWKS_ISSUER`` config key, or None.
        """
        return current_app.config.get("JWKS_ISSUER")

    @property
    def audience(self) -> str | None:
        """
        Retrieve the expected token audience.

        Returns:
            str | None: The audience from the ``JWKS_AUDIENCE`` config key, or None.
        """
        return current_app.config.get("JWKS_AUDIENCE")

    @property
    def algorithms(self) -> list[str]:
        """
        Retrieve the list of accepted signing algorithms.

        Returns:
            list[str]: Algorithm names parsed from the ``JWKS_ALGORITHMS`` config key.
        """
        raw = current_app.config.get("JWKS_ALGORITHMS", "EdDSA,RS256")
        if isinstance(raw, list):
            return raw
        return [a.strip() for a in raw.split(",")]

    def verify_token(self, token: str) -> dict | None:
        """
        Verify a JWT token using the configured JWKS endpoint.

        Args:
            token: JWT token string

        Returns:
            dict: Decoded token payload if valid

        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            client = self._get_jwks_client()
            signing_key = client.get_signing_key_from_jwt(token)

            decode_options = {}
            decode_kwargs = {
                "algorithms": self.algorithms,
            }

            if self.issuer:
                decode_kwargs["issuer"] = self.issuer
            if self.audience:
                decode_kwargs["audience"] = self.audience
            else:
                decode_options["verify_aud"] = False

            if decode_options:
                decode_kwargs["options"] = decode_options

            return jwt.decode(
                token,
                signing_key.key,
                **decode_kwargs,
            )

        except jwt.ExpiredSignatureError:
            msg = "Token has expired"
            raise AuthenticationError(msg)
        except jwt.InvalidTokenError as e:
            msg = f"Invalid token: {e!s}"
            raise AuthenticationError(msg)
        except Exception as e:
            logger.exception(f"Token verification error: {e!s}")
            msg = "Token verification failed"
            raise AuthenticationError(msg)

    def extract_user_info(self, decoded_token: dict) -> dict:
        """
        Extract user profile information from a decoded JWT payload.

        Handles both standard OIDC claims (snake_case) and common provider
        variants (camelCase, e.g. Better Auth / NextAuth).

        Parameters:
            decoded_token (dict): Decoded JWT payload.

        Returns:
            dict: Normalised user info with keys: user_id, username, email,
                  email_verified, name, given_name, family_name, image,
                  roles, client_roles, created_at, updated_at.
        """
        return {
            "user_id": decoded_token.get("sub"),
            "username": decoded_token.get("preferred_username"),
            "email": decoded_token.get("email"),
            "email_verified": decoded_token.get(
                "email_verified",
                decoded_token.get("emailVerified", False),
            ),
            "name": decoded_token.get("name"),
            "given_name": decoded_token.get("given_name"),
            "family_name": decoded_token.get("family_name"),
            "image": decoded_token.get("image"),
            "roles": decoded_token.get("roles", []),
            "client_roles": [],
            "created_at": decoded_token.get(
                "created_at", decoded_token.get("createdAt")
            ),
            "updated_at": decoded_token.get(
                "updated_at", decoded_token.get("updatedAt")
            ),
        }


def _create_auth_service(app):
    """
    Create the auth service instance for the given app's AUTH_PROVIDER config.

    Parameters:
        app: Flask application instance.

    Returns:
        KeycloakAuthService | JWKSAuthService: A new auth service instance.

    Raises:
        ValueError: If AUTH_PROVIDER is not a recognised value.
    """
    provider = app.config.get("AUTH_PROVIDER", "keycloak").lower()
    if provider == "keycloak":
        # Require explicit Keycloak configuration to avoid silent None URLs.
        for key in ("KEYCLOAK_SERVER_URL", "KEYCLOAK_REALM"):
            if not app.config.get(key):
                raise ValueError(
                    f"{key} must be set when AUTH_PROVIDER is 'keycloak'"
                )
        return KeycloakAuthService()
    elif provider == "jwks":
        # Ensure JWKS_URL is present for JWKS-based verification.
        if not app.config.get("JWKS_URL"):
            raise ValueError("JWKS_URL must be set when AUTH_PROVIDER is 'jwks'")
        return JWKSAuthService()
    else:
        msg = f"Unknown AUTH_PROVIDER: '{provider}'. Must be 'keycloak' or 'jwks'."
        raise ValueError(msg)


def init_auth_service(app):
    """
    Initialize and cache the auth service on the Flask app.

    Call this once during ``create_app`` to eagerly create the service.

    Parameters:
        app: Flask application instance.
    """
    app.extensions["auth_service"] = _create_auth_service(app)


def get_auth_service():
    """
    Return the cached auth service for the current application.

    The instance is created once (via ``init_auth_service``) and reused for
    every request.

    Returns:
        KeycloakAuthService | JWKSAuthService: The configured auth service.
    """
    return current_app.extensions["auth_service"]