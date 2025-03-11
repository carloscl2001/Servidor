from pydantic import BaseModel, Field

class PasswordChangeRequest(BaseModel):
    new_password: str