from domain.models.userModels import User


class UserService:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    def register_user(self, email, password):
        hashed_password = hash_password(password)
        user = User(user_id=None, name=None, email=email, hashed_password=hashed_password)
        self.user_repository.save(user)
        return user

    def authenticate_user(self, email, password):
        user = self.user_repository.find_by_email(email)
        if not user:
            raise ValueError("User not found")
        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid password")
        return user