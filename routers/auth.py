from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from db.models.auth import PasswordChangeRequest
from db.models.user import User
from db.schemas.user import user_schema, users_schema
from db.client import db_client
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta


#CONSTANTS
ALGORITHM = "HS256"
ACCESS_TOKEN_DURATION = 15
SECRET = "201d573bd7d1344d3a3bfce1550b69102fd11be3db6d379508b6cccc58ea230b"

router = APIRouter(prefix="/auth", 
                   tags=["auth"],
                    responses={status.HTTP_404_NOT_FOUND: {"message": "Not found"}})

oauth2 = OAuth2PasswordBearer(tokenUrl="login")

crypt = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
    

#Función para autenticar al usuario
async def auth_user(token: str = Depends(oauth2)):

    exception = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"})
    
    try:
        username =  jwt.decode(token, SECRET, algorithms=[ALGORITHM]).get("sub")
        if username is None:
            raise exception
        
    except JWTError:
        raise exception
    
    return search_user("username", username)


#Función para verificar si el usuario está habilitado
async def get_current_user(user: User = Depends(auth_user)):
    #Verificamos si esta hablitado o no, pk no rsta implmentado los permisos
    # if user.disabled:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="User is disabled",)
    return user
   

#Operación para obtener el usuario autenticado
@router.get("/users/me")
async def read_users_me(user: User = Depends(get_current_user)):
    return user


#Operación para iniciar sesión
@router.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends()):
   
    #comprobar que exista el usuario
    user_auth = search_user("username", form.username)
    if not user_auth:    
        raise HTTPException(status_code=400, detail="User not found")
    
    #comprobar que la contraseña sea correcta
    if not crypt.verify(form.password, user_auth.password):
        raise HTTPException(status_code=400, detail="Invalid password")

    #generar token
    access_token = {"sub": user_auth.username,
                    "exp": datetime.now() + timedelta(minutes=ACCESS_TOKEN_DURATION)}

    
    return {"access_token": jwt.encode(access_token, SECRET, algorithm=ALGORITHM), "token_type": "bearer"}



# Operación para cambiar la contraseña
@router.put("/{username}/changePassword")
async def change_password(username: str, body: PasswordChangeRequest, user: User = Depends(get_current_user)):

    if user.username != username:
        raise HTTPException(status_code=403, detail="You can only change your own password")

    existing_user = search_user("username", username)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    #comprobar que la nueva contraseña sea distinta a la ya existente
    if crypt.verify(body.new_password, user.password):
        raise HTTPException(status_code=400, detail="The new password cannot be the same as the current password")


    hashed_password = crypt.hash(body.new_password)
    db_client.users.update_one({"username": username}, {"$set": {"password": hashed_password}})
    
    return {"message": "Password updated successfully"}