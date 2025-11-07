# backend/app/schemas.py
from pydantic import BaseModel
from typing import List

class RenameResult(BaseModel):
    original: str
    renamed: str

class BatchRenameResponse(BaseModel):
    results: List[RenameResult]
    zipped: bool = False