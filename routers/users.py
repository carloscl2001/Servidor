from fastapi import APIRouter, HTTPException, status, Response
from db.models.user import User, UserSubject
from db.schemas.user import user_schema, users_schema
from db.client import db_client
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt

#CONSTANTS
ALGORITHM = "HS256"
ACCESS_TOKEN_DURATION = 15
SECRET = "201d573bd7d1344d3a3bfce1550b69102fd11be3db6d379508b6cccc58ea230b"


crypt = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/users",
                   tags=["users"],
                   responses={status.HTTP_404_NOT_FOUND: {"message": "Not found"}})


#Obtener todos los usuarios
@router.get("/", response_model=list[User])
async def get_subject():
    try:
        users_list = list(db_client.users.find())  # Convierte el cursor en una lista
        return users_schema(users_list)  # Aplica el schema a la lista
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    

#Obtener un usuario por su username
@router.get("/{username}", response_model=User)
async def get_all_subjects(username: str):
    user = search_user("username", username)
    if user:
        return user
    raise HTTPException(status_code=404, detail="User not found")


# Obtener las asignaturas de un usuario
@router.get("/{username}/subjects", response_model=list[UserSubject])
async def get_user_subjects(username: str):
    # Verificamos si el usuario existe
    existing_user = search_user("username", username)

    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Recuperamos el usuario de la base de datos
    user_data = db_client.users.find_one({"username": username})

    # Retornamos la información de las asignaturas
    return [UserSubject(code=subject['code'], types=subject['types']) for subject in user_data.get("subjects", [])]


# Crear un usuario
@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_user(user: User):
    # Verificamos si el usuario ya existe por email o username
    if search_user("email", user.email):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Email already registered"
        )
    
    if search_user("username", user.username):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Username already exists"
        )
    
    if search_user("email", user.email) and search_user("username", user.username):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Username and email already registered"
        )

    # Creamos un diccionario con los datos del usuario
    user_dict = user.model_dump()

    # Eliminamos el campo id ya que no lo necesitamos para la inserción
    user_dict.pop("id", None)

    # Cifrar la contraseña antes de almacenar el usuario
    user_dict["password"] = crypt.hash(user.password)

    # Solo eliminamos el campo subjects si no está presente o está vacío
    if "subjects" in user_dict and not user_dict["subjects"]:
        del user_dict["subjects"]

    # Insertamos el nuevo usuario en la base de datos
    id = db_client.users.insert_one(user_dict).inserted_id

    # Recuperamos el usuario recién creado
    new_user = db_client.users.find_one({"_id": id})

    # Generar un token JWT para el usuario
    access_token = {
        "sub": user.username,  # Identificador del usuario
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_DURATION),  # Fecha de expiración
    }
    token = jwt.encode(access_token, SECRET, algorithm=ALGORITHM)

    # Devolvemos el nuevo usuario y el token
    return {
        "message": "User registered successfully",
        "user": User(**user_schema(new_user)),  # Información del usuario
        "token": token,  # Token JWT
    }

# Actualizar un usuario
@router.put("/{username}", response_model=User, status_code=status.HTTP_200_OK)
async def update_user(username: str, updated_user: User):
    # Verificamos si el usuario ya existe
    existing_user = search_user("username", username)

    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Convertimos el objeto de Pydantic a un diccionario
    updated_user_dict = updated_user.model_dump()

    # Eliminamos el campo 'id' si existe, ya que no se debe actualizar
    if "id" in updated_user_dict:
        del updated_user_dict["id"]

    # Si no se pasó un nuevo password, lo eliminamos del diccionario de actualización
    if "password" in updated_user_dict and updated_user_dict["password"] is None:
        del updated_user_dict["password"]

    # Actualizamos el usuario en la base de datos
    db_client.users.update_one({"username": username}, {"$set": updated_user_dict})

    # Recuperamos el usuario actualizado
    updated_user_data = db_client.users.find_one({"username": username})

    return User(**updated_user_data)

#Actualiza las asignaturas de un usario
@router.patch("/{username}/subjects", status_code=status.HTTP_200_OK)
async def update_user_subjects(username: str, subjects_data: dict):
    # Verificamos si el usuario existe
    existing_user = db_client.users.find_one({"username": username})
    
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Extraemos subjects del diccionario recibido
    subjects = subjects_data.get("subjects", [])

    # Convertimos a la estructura esperada
    subjects_dict = [UserSubject(**subject).model_dump() for subject in subjects]

    # Actualizamos solo el campo "subjects" sin afectar los demás datos del usuario
    db_client.users.update_one(
        {"username": username}, 
        {"$set": {"subjects": subjects_dict}}
    )

    return {"message": "Subjects updated successfully"}


#Eliminar todos los usuarios
@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_users():
    # Contamos cuántos usuarios hay en la base de datos
    user_count = db_client.users.count_documents({})
    
    if user_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No users to delete"  # Mensaje en inglés
        )
    
    # Si hay usuarios, los eliminamos
    db_client.users.delete_many({})
    
    # Retornamos una respuesta de éxito
    return Response(content="All users deleted successfully", status_code=status.HTTP_204_NO_CONTENT)


#Eliminar un usuario por username
@router.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(username: str):

    #Verificamos si el usuario existe
    existing_user = search_user("username", username)
    if  existing_user:
        #Eliminamos el usuario
        db_client.users.delete_one({"username": username})
        raise HTTPException(status_code=204, detail="User deleted")
    #Si el usuario no se encontró, lanzamos la ecepción
    raise HTTPException(status_code=404, detail="User not found")


#Función para buscar un usuario por un campo específico
def search_user(field: str, key):
    try:
        user = db_client.users.find_one({field: key})
        if user:
            return User(**user_schema(user))  # Devuelve el usuario si se encuentra
        return None  # Devuelve None si no se encuentra el usuario
    except Exception as e:
        print(f"Error buscando usuario: {e}")  # Registra el error
        return None  # Devuelve None en caso de error