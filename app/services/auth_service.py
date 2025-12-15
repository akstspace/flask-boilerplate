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


# Global instance
auth_service = KeycloakAuthService()