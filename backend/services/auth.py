"""
Authentication Service - Windows AD/LDAP login + JWT session tokens
"""
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

import ldap
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from config import settings
from models import User

logger = logging.getLogger(__name__)


class AuthService:
    """Service for AD/LDAP authentication and JWT session management"""

    @staticmethod
    def _ad_domain() -> str:
        """Derive the AD domain (e.g. shapir.local) from AD_BASE_DN (dc=shapir,dc=local)"""
        parts = [
            part.split("=", 1)[1]
            for part in settings.AD_BASE_DN.split(",")
            if part.strip().lower().startswith("dc=")
        ]
        return ".".join(parts)

    @staticmethod
    def validate_ad_credentials(username: str, password: str) -> Optional[Dict]:
        """
        Validate credentials against Windows AD via LDAP bind

        Args:
            username: AD username (sAMAccountName or user@domain)
            password: AD password

        Returns:
            Dict with ad_username, ad_domain, email, name if valid, else None
        """
        if not username or not password:
            return None

        domain = AuthService._ad_domain()
        user_principal = username if "@" in username else f"{username}@{domain}"
        sam_account_name = user_principal.split("@")[0]

        conn = None
        try:
            conn = ldap.initialize(settings.AD_SERVER)
            conn.set_option(ldap.OPT_REFERRALS, 0)
            conn.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
            conn.simple_bind_s(user_principal, password)

            # Look up the user's own attributes using the now-authenticated bind
            name = sam_account_name
            email = user_principal
            try:
                results = conn.search_s(
                    settings.AD_BASE_DN,
                    ldap.SCOPE_SUBTREE,
                    f"(userPrincipalName={user_principal})",
                    ["mail", "displayName", "sAMAccountName"],
                )
                if results:
                    _, attrs = results[0]
                    if attrs.get("mail"):
                        email = attrs["mail"][0].decode("utf-8")
                    if attrs.get("displayName"):
                        name = attrs["displayName"][0].decode("utf-8")
            except ldap.LDAPError as e:
                logger.warning(f"AD attribute lookup failed for {user_principal}: {e}")

            return {
                "ad_username": sam_account_name,
                "ad_domain": domain,
                "email": email,
                "name": name,
            }

        except ldap.INVALID_CREDENTIALS:
            logger.warning(f"Invalid AD credentials for user: {username}")
            return None
        except ldap.LDAPError as e:
            logger.error(f"LDAP error during authentication for {username}: {e}")
            return None
        finally:
            if conn is not None:
                try:
                    conn.unbind_s()
                except ldap.LDAPError:
                    pass

    @staticmethod
    def get_or_create_user(db: Session, ad_user_info: Dict) -> User:
        """
        Find the user by email, creating them on first login

        Args:
            db: Database session
            ad_user_info: Dict returned by validate_ad_credentials

        Returns:
            User object
        """
        user = db.query(User).filter(User.email == ad_user_info["email"]).first()

        if not user:
            user = User(
                email=ad_user_info["email"],
                name=ad_user_info["name"],
                ad_username=ad_user_info["ad_username"],
                ad_domain=ad_user_info["ad_domain"],
            )
            db.add(user)
            logger.info(f"Created new user from AD login: {user.email}")

        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def create_access_token(user_id: str) -> str:
        """Create a signed JWT for the given user id"""
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {"sub": user_id, "exp": expire}
        return jwt.encode(payload, settings.SESSION_SECRET_KEY, algorithm=settings.SESSION_ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> Optional[str]:
        """Decode a JWT and return the user id it was issued for, or None if invalid/expired"""
        try:
            payload = jwt.decode(token, settings.SESSION_SECRET_KEY, algorithms=[settings.SESSION_ALGORITHM])
            return payload.get("sub")
        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            return None


# Create service instance
auth_service = AuthService()
