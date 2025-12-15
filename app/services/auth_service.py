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
        Initialize the KeycloakAuthService instance.
        
        Sets an internal attribute used to cache the currently loaded public key; initially None.
        """
        self._public_key = None

    @property
    def keycloak_url(self) -> str:
        """
        Return the configured Keycloak server base URL.
        
        Returns:
            The Keycloak server base URL from the application's configuration.
        """
        return current_app.config["KEYCLOAK_SERVER_URL"]

    @property
    def realm(self) -> str:
        """
        Keycloak realm configured for the application.
        
        Returns:
            realm (str): The Keycloak realm name from application configuration.
        """
        return current_app.config["KEYCLOAK_REALM"]

    @property
    def certs_url(self) -> str:
        """
        Constructs the JWKS (certificates) endpoint URL for the configured Keycloak realm.
        
        Returns:
            str: The full URL of the realm's OpenID Connect JWKS (certs) endpoint.
        """
        return f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/certs"

    @lru_cache(maxsize=128)
    def _get_jwks(self) -> dict:
        """
        Retrieve the JSON Web Key Set (JWKS) from Keycloak and return it as a parsed dictionary. The fetched result is cached.
        
        Returns:
            dict: The JWKS payload parsed from JSON.
        
        Raises:
            AuthenticationError: If the JWKS cannot be fetched or parsed.
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
        Retrieve the PEM-formatted public key from the JWKS that matches the given JWT `kid`.
        
        Parameters:
            kid (str): Key ID from the JWT header to search for in the JWKS.
        
        Returns:
            str: Public key in PEM format.
        
        Raises:
            ValueError: If the JWKS payload does not contain a `keys` field or no key with the given `kid` is found.
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
        Verify a Keycloak-issued JWT and return its decoded payload.
        
        Returns:
            Decoded token payload as a dict.
        
        Raises:
            AuthenticationError: If the token is missing the `kid` header, has expired, is invalid, or fails verification for any other reason.
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
        Builds a normalized user info dictionary from a decoded Keycloak JWT payload.
        
        Parameters:
            decoded_token (dict): Decoded JWT payload containing Keycloak claims.
        
        Returns:
            dict: A mapping with the following keys:
                - user_id: Subject identifier from the `sub` claim.
                - username: Username from the `preferred_username` claim.
                - email: Email address from the `email` claim.
                - email_verified: Boolean indicating whether the email is verified.
                - name: Full name from the `name` claim.
                - given_name: Given (first) name from the `given_name` claim.
                - family_name: Family (last) name from the `family_name` claim.
                - roles: List of realm-level roles from `realm_access.roles`.
                - client_roles: List of client-level roles for the configured client from `resource_access[KEYCLOAK_CLIENT_ID].roles`.
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