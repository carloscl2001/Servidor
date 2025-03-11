from pydantic import BaseModel, Field
from typing import Optional, List


# Modelo para la asignatura
class Subject(BaseModel):
    code: str


 # Modelo para el grado 
class Degree(BaseModel):
    code: str
    name: str
    subjects: List[Subject]
