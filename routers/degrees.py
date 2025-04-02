## API PARA GESTIONAR LOS GRADOS##
from fastapi import APIRouter, HTTPException, status, Response
from db.models.degree import Degree
from db.schemas.degree import degree_schema, degrees_schema
from db.client import db_client
from bson import ObjectId
from typing import List

# Definimos el router
router = APIRouter(prefix="/degrees",
                    tags=["degrees"],
                    responses={status.HTTP_404_NOT_FOUND: {"message": "Not found"}})



#Obtener todas los grados
@router.get("/", response_model=list[Degree])
async def get_degree():
    try:
        degrees_list = list(db_client.degrees.find())  # Convierte el cursor en una lista
        return degrees_schema(degrees_list)  # Aplica el schema a la lista
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    

#Obtener un degree su code
@router.get("/{name}", response_model=Degree)
async def get_degree_by_name(name: str):
    degree = search_degree("name", name)  # Buscamos por name en vez de code
    if degree:
        return degree
    raise HTTPException(status_code=404, detail="Degree not found")

#Obtner los nambres de todos los degree
@router.get("/names/", response_model=List[str])
async def get_degree_names():
    try:
        # Proyectamos solo el campo 'name' y excluimos el _id si no lo quieres
        degrees_cursor = db_client.degrees.find({}, {"name": 1, "_id": 0})
        
        # Extraemos solo los nombres de los documentos
        names_list = [degree["name"] for degree in degrees_cursor]
        
        return names_list
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")


#Crear un grado
@router.post("/", response_model=Degree, status_code=status.HTTP_201_CREATED)
async def create_degree(degree: Degree):
    # Verificamos si la asignatura ya existe por su code
    existing_degree = search_degree("code", degree.code)
    if existing_degree:  # Si la asignatura ya existe
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Degree already exists"
        )

    # Convertimos el objeto de Pydantic a un diccionario
    degree_dict = degree.model_dump()  # Convierte los objetos en un diccionario JSON serializable
    
    # Insertamos el nuevo degree en la base de datos
    result = db_client.degrees.insert_one(degree_dict)
    
    print(f"Grado insertado con id: {result.inserted_id}")

    # Recuperamos el degree recién creado
    new_degree = db_client.degrees.find_one({"_id": result.inserted_id})
    
    return Degree(**new_degree)


#Actualizar una asignatura
@router.put("/{code}", response_model=Degree, status_code=status.HTTP_200_OK)
async def update_subject(code: str, updated_degree: Degree):
    # Verificamos si la asignatura ya existe
    existing_degree = search_degree("code", code)

    if not existing_degree:
        raise HTTPException(status_code=404, detail="Degree not found")

    # Convertimos el objeto de Pydantic a un diccionario
    updated_degree_dict = updated_degree.model_dump()

    # Actualizamos la asignatura en la base de datos
    db_client.degrees.update_one({"code": code}, {"$set": updated_degree_dict})

    # Recuperamos el subject actualizado
    updated_degree_data = db_client.degrees.find_one({"code": code})
    
    return Degree(**updated_degree_dict)
                                                    


#Eliminar todas los degrees
@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_degrees():
    degree_count = db_client.degrees.count_documents({})

    if degree_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No degree to delete" 
        )
    
    # Si hay asignaturas, las eliminamos
    db_client.degrees.delete_many({})

    return Response(content="All degrees deleted successfully", status_code=status.HTTP_204_NO_CONTENT)


# Eliminar un degree por su code
@router.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_degree(code: str):
    # Verificamos si la asignatura ya existe
    existing_degreee = search_degree("code", code)
    if existing_degreee:
        # Eliminamos la asignatura
        return Response(content="The degree deleted successfully", status_code=status.HTTP_204_NO_CONTENT)
    # Si la asignatura no se encontró, lanzamos la excepción
    raise HTTPException(status_code=404, detail="Degree not found")

#Función para buscar un degree por un campo específico
def search_degree(field: str, key):
    degree = db_client.degrees.find_one({field: key})  # Buscamos por el campo dado
    if degree:
        return Degree(**degree_schema(degree))  # Retornamos el resultado usando el schema
    return None