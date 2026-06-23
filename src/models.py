from pydantic import BaseModel, Field, field_validator


class OrderModel(BaseModel):
    # Ensures ID always follows 'ORD-123' pattern
    id: str = Field(pattern=r"^ORD-\d+$")
    item_name: str = Field(min_length=2, max_length=100)
    price: float = Field(gt=0.0)           # Price must be Greater Than 0
    # Quantity must be Greater than or Equal to 1
    quantity: int = Field(ge=1)
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        allowed = {"PENDING", "SHIPPED", "DELIVERED", "CANCELLED", "NOT_FOUND"}
        if value not in allowed:
            raise ValueError(
                f"Invalid status: {value}. Must be one of {allowed}")
        return value
