from app.repositories.user_repository import UserRepository

repo = UserRepository()

def get_user_by_email(email: str):
    return repo.get_by_email(email)

def get_user_by_id(uid: str):
    return repo.get_by_id(uid)

def store_user_with_password(email: str, password: str, name: str):
    return repo.create_with_password(email, password, name)

def verify_user_password(email: str, password: str):
    return repo.verify_password(email, password)

def update_user_data(user_data: dict, user_email: str):
    return repo.update_profile_by_email(user_data, user_email)

def store_or_update_user_data(user_data: dict):
    existing_user = repo.get_by_email(user_data["email"])
    if existing_user:
        repo.update_profile_by_email(user_data, user_data["email"])
    else:
        repo.store_google_user(user_data)