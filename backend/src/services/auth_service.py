from datetime import timedelta
from typing import Optional

import bcrypt
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token

from models.models import User
from repositories.user_repository import UserRepository
from utils.error_handlers import UnauthorizedError, ValidationError


class AuthService:
    def __init__(self, user_repository: Optional[UserRepository] = None):
        self.user_repo = user_repository or UserRepository()

    def authenticate(self, username: str, password: str) -> dict:
        if not username or not password:
            raise ValidationError('Username and password are required')

        user = self.user_repo.get_by_username(username)
        if not user:
            raise UnauthorizedError('Invalid username or password')

        if not user.is_active:
            raise UnauthorizedError('Account is deactivated')

        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            raise UnauthorizedError('Invalid username or password')

        user.last_login = __import__('datetime').datetime.utcnow()
        self.user_repo.update(user)

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                'username': user.username,
                'role_id': user.role_id,
                'branch_id': user.branch_id,
            },
            expires_delta=timedelta(hours=8),
        )
        refresh_token = create_refresh_token(
            identity=str(user.id),
            expires_delta=timedelta(days=30),
        )

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict(),
        }

    def refresh_token(self, refresh_token_value: str) -> dict:
        try:
            decoded = decode_token(refresh_token_value)
            user_id = decoded.get('sub')
            if not user_id:
                raise UnauthorizedError('Invalid refresh token')
        except UnauthorizedError:
            raise
        except Exception:
            raise UnauthorizedError('Invalid or expired refresh token')

        user = self.user_repo.get_by_id(int(user_id))
        if not user or not user.is_active:
            raise UnauthorizedError('User not found or deactivated')

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                'username': user.username,
                'role_id': user.role_id,
                'branch_id': user.branch_id,
            },
            expires_delta=timedelta(hours=8),
        )
        new_refresh = create_refresh_token(
            identity=str(user.id),
            expires_delta=timedelta(days=30),
        )

        return {
            'access_token': access_token,
            'refresh_token': new_refresh,
        }

    def change_password(self, user_id: int, old_password: str, new_password: str) -> None:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValidationError('User not found')

        if not bcrypt.checkpw(old_password.encode('utf-8'), user.password_hash.encode('utf-8')):
            raise ValidationError('Current password is incorrect')

        if len(new_password) < 6:
            raise ValidationError('New password must be at least 6 characters')

        user.password_hash = bcrypt.hashpw(
            new_password.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')
        self.user_repo.update(user)
