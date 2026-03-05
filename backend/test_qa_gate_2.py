from database import engine, Base, SessionLocal
from models import ComponentVault, SourceType
from schemas import Constraint
from pydantic import ValidationError

def test_pydantic_normalization():
    print("--- Testing Pydantic V2 Normalization ---")
    
    # Test 1: Valid Conversion (Inches to mm)
    try:
        # Assuming your schema takes a value and a unit
        c1 = Constraint(name="length", data_type="number", operator="<=", target_value=2, unit="in", is_strict=True)
        # The validator should have automatically changed 2 inches to 50.8 mm
        assert c1.unit == "mm", f"Failed: Unit not normalized. Got {c1.unit}"
        assert c1.target_value == 50.8, f"Failed: Math conversion incorrect. Got {c1.target_value}"
        print("✅ Pydantic Test 1 Passed: Imperial to Metric conversion successful.")
    except Exception as e:
        print(f"❌ Pydantic Test 1 Failed: {e}")

    # Test 2: Invalid Data Type
    try:
        # Passing a string where a number is expected
        c2 = Constraint(name="voltage", data_type="number", operator="==", target_value="five", unit="V", is_strict=True)
        print("❌ Pydantic Test 2 Failed: Did not catch invalid data type.")
    except ValidationError:
        print("✅ Pydantic Test 2 Passed: Correctly blocked invalid data type with ValidationError.")

def test_sqlalchemy_vault():
    print("\n--- Testing SQLite Component Vault ---")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Test 3: Insert and Retrieve
        mock_part = ComponentVault(
            part_number="TEST-MTR-001",
            name="Mock 12V Motor",
            specs={"voltage": 12, "torque": 1.5},
            source_type=SourceType.API_CACHE
        )
        db.add(mock_part)
        db.commit()
        
        retrieved_part = db.query(ComponentVault).filter_by(part_number="TEST-MTR-001").first()
        assert retrieved_part is not None, "Failed to retrieve part."
        assert retrieved_part.source_type == SourceType.API_CACHE, "Failed to store Enum correctly."
        print("✅ SQLAlchemy Test 3 Passed: Component inserted and Enum retrieved correctly.")
        
    except Exception as e:
        print(f"❌ SQLAlchemy Test 3 Failed: {e}")
    finally:
        # Cleanup
        db.query(ComponentVault).filter_by(part_number="TEST-MTR-001").delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    test_pydantic_normalization()
    test_sqlalchemy_vault()