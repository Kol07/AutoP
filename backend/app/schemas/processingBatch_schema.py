from pydantic import BaseModel

class ProcessingBatchCreate(BaseModel):
    filename: str