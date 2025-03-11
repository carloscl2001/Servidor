def user_subject_schema(subject) -> dict:
    return {
        "code": subject["code"],  # Código de la asignatura
        "types": subject["types"],  # Lista de tipos de clase
    }

def user_subjects_schema(subjects) -> list:
    return [user_subject_schema(subject) for subject in subjects]

def user_schema(user) -> dict:
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "username": user["username"],
        "password": user["password"],
        "name": user["name"],
        "surname": user["surname"],
        "degree": user["degree"],
        "subjects": user_subjects_schema(user.get("subjects", [])),  # Aplica el esquema de asignaturas con tipos de clase
    }

def users_schema(users) -> list:
    return [user_schema(user) for user in users]