## API PARA GESTIONAR LAS ASIGNATURAS ##
from fastapi import APIRouter, HTTPException, status, Response
from db.models.subject import Subject
from db.schemas.subject import subject_schema, subjects_schema
from db.client import db_client
from bson import ObjectId

# Definimos el router
router = APIRouter(prefix="/subjects",
                    tags=["subjects"],
                    responses={status.HTTP_404_NOT_FOUND: {"message": "Not found"}})


#Obtener todas las asignaturas
@router.get("/", response_model=list[Subject])
async def get_subject():
    try:
        subjects_list = list(db_client.subjects.find())  # Convierte el cursor en una lista
        return subjects_schema(subjects_list)  # Aplica el schema a la lista
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
#Obtener una asignatura por su code
@router.get("/{code}", response_model=Subject)
async def get_all_subjects(code: str):
    subject = search_subject("code", code)
    if subject:
        return subject
    raise HTTPException(status_code=404, detail="Subject not found")


#Crear una asignatura
@router.post("/", response_model=Subject, status_code=status.HTTP_201_CREATED)
async def create_subject(subject: Subject):
    # Verificamos si la asignatura ya existe por su code
    existing_subject = search_subject("code", subject.code)
    if existing_subject:  # Si la asignatura ya existe
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Subject already exists"
        )

    # Convertimos el objeto de Pydantic a un diccionario
    subject_dict = subject.model_dump()  # Convierte los objetos en un diccionario JSON serializable
    
    # Insertamos el nuevo subject en la base de datos
    result = db_client.subjects.insert_one(subject_dict)
    
    print(f"Asignatura insertada con id: {result.inserted_id}")

    # Recuperamos el subject recién creado
    new_subject = db_client.subjects.find_one({"_id": result.inserted_id})
    
    return Subject(**new_subject)


#Actualizar una asignatura
@router.put("/{code}", response_model=Subject, status_code=status.HTTP_200_OK)
async def update_subject(code: str, updated_subject: Subject):
    # Verificamos si la asignatura ya existe
    existing_subject = search_subject("code", code)

    if not existing_subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Convertimos el objeto de Pydantic a un diccionario
    updated_subject_dict = updated_subject.model_dump()

    # Actualizamos la asignatura en la base de datos
    db_client.subjects.update_one({"code": code}, {"$set": updated_subject_dict})

    # Recuperamos el subject actualizado
    updated_subject_data = db_client.subjects.find_one({"code": code})
    
    return Subject(**updated_subject_data)
                                                    

#Eliminar todas las asignaturas
@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_subjects():
    subject_count = db_client.subjects.count_documents({})

    if subject_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subjects to delete" 
        )
    
    # Si hay asignaturas, las eliminamos
    db_client.subjects.delete_many({})

    return Response(content="All subjects deleted successfully", status_code=status.HTTP_204_NO_CONTENT)


# Eliminar una asignatura por su code
@router.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject(code: str):
    # Verificamos si la asignatura ya existe
    existing_subject = search_subject("code", code)
    if existing_subject:
        # Eliminamos la asignatura
        return Response(content="The subject deleted successfully", status_code=status.HTTP_204_NO_CONTENT)
    # Si la asignatura no se encontró, lanzamos la excepción
    raise HTTPException(status_code=404, detail="Subject not found")


#Función para buscar una asignatura por un campo específico
def search_subject(field: str, key):
    subject = db_client.subjects.find_one({field: key})
    if subject:
        return Subject(**subject_schema(subject))
    return None