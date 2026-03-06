from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Any, Dict
from enum import Enum

class SourceTypeEnum(str, Enum):
    API_CACHE = "API_CACHE"
    DEEP_SCRAPE = "DEEP_SCRAPE"
    USER_UPLOAD = "USER_UPLOAD"

class JobMetadata(BaseModel):
    job_id: str
    client_id: Optional[str] = None
    timestamp: str

class SearchParameters(BaseModel):
    query: str
    category: Optional[str] = None
    limit: int = 10

def normalize_unit(val: float, unit: str):
    unit_lower = unit.lower().strip()
    
    # Torque / Force
    if unit_lower in ['oz-in', 'ozin', 'ounce-inch']:
        return val * 0.00706155, 'Nm'
    elif unit_lower in ['lb-in', 'lbin', 'pound-inch']:
        return val * 0.1129848, 'Nm'
    elif unit_lower in ['lb-ft', 'lbft', 'pound-foot']:
        return val * 1.355818, 'Nm'
    elif unit_lower in ['n', 'newton', 'newtons', 'nm', 'n-m', 'newton-meter']:
        return val, 'Nm'
        
    # Dimensions
    elif unit_lower in ['in', 'inch', 'inches']:
        return val * 25.4, 'mm'
    elif unit_lower in ['cm', 'centimeter', 'centimeters']:
        return val * 10.0, 'mm'
    elif unit_lower in ['m', 'meter', 'meters']:
        return val * 1000.0, 'mm'
    elif unit_lower in ['mm', 'millimeter', 'millimeters']:
        return val, 'mm'
        
    # Electrical Potentials
    elif unit_lower in ['mv', 'millivolt', 'millivolts']:
        return val * 0.001, 'V'
    elif unit_lower in ['kv', 'kilovolt', 'kilovolts']:
        return val * 1000.0, 'V'
    elif unit_lower in ['v', 'volt', 'volts']:
        return val, 'V'
        
    # If unrecognized, return as is (flexible schema)
    return val, unit

class Constraint(BaseModel):
    name: str
    data_type: str
    operator: str
    target_value: float
    unit: str
    is_strict: bool

    @field_validator('unit')
    @classmethod
    def validate_unit(cls, v: str) -> str:
        if v not in ['Nm', 'mm', 'V']:
             raise ValueError(f"Unit must be SI standard (Nm, mm, V), got {v}")
        return v

    @model_validator(mode='before')
    @classmethod
    def convert_to_si(cls, data: Any) -> Any:
        if isinstance(data, dict):
            unit = data.get('unit')
            val = data.get('target_value')
            if unit is not None and val is not None:
                try:
                    new_val, new_unit = normalize_unit(float(val), str(unit))
                    data['target_value'] = new_val
                    data['unit'] = new_unit
                except ValueError as e:
                    if "could not convert string to float" not in str(e):
                        raise e
        return data

class ComponentSchema(BaseModel):
    part_number: str
    name: Optional[str] = None
    source_type: SourceTypeEnum
    specs: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('specs', mode='before')
    @classmethod
    def convert_specs_to_si(cls, v: Any) -> Any:
        if isinstance(v, dict):
            for key, attr in v.items():
                if isinstance(attr, dict) and 'value' in attr and 'unit' in attr:
                    try:
                        # Only normalize if it's a number
                        numeric_val = float(attr['value'])
                        new_val, new_unit = normalize_unit(numeric_val, str(attr['unit']))
                        attr['value'] = new_val
                        attr['unit'] = new_unit
                    except (ValueError, TypeError):
                        pass # Ignore if it's a string or dimensionless value
        return v

class ExecutionState(BaseModel):
    job_metadata: JobMetadata
    search_parameters: SearchParameters
    constraints: List[Constraint]
    candidates_evaluated: List[ComponentSchema] = Field(default_factory=list)
    final_selection: Optional[ComponentSchema] = None
    status: str = "PENDING"
