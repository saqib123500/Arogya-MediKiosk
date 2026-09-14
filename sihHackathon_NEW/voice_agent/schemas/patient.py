
from typing import Optional

from pydantic import BaseModel


class PatientState(BaseModel):
    FullName: Optional[str] = None
    Age: Optional[int] = None
    Gender: Optional[str] = None
    Contact_Number: Optional[str] = None
    Address: Optional[str] = None
    Chief_Complaint: Optional[str] = None
    Prakriti: Optional[str] = None
    Vikriti: Optional[str] = None
    Sara: Optional[str] = None
    Samhanana: Optional[str] = None
    Pramana: Optional[str] = None
    Satmya: Optional[str] = None
    Satva: Optional[str] = None
    Ahara_Shakti: Optional[str] = None
    Vyayama_Shakti: Optional[str] = None
    Vaya: Optional[str] = None
    
    