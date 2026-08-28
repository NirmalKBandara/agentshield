from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class ToolArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class GetCustomerArguments(ToolArguments):
    customer_id: str = Field(pattern=r"^[0-9]{4}$", examples=["1002"])


class SendEmailArguments(ToolArguments):
    to: str = Field(min_length=3, max_length=320)
    message: str = Field(min_length=1, max_length=2000)

    @field_validator("to")
    @classmethod
    def validate_demo_email(cls, value: str) -> str:
        local, separator, domain = value.rpartition("@")
        if not separator or not local or "." not in domain or any(char.isspace() for char in value):
            raise ValueError("to must be a valid email address")
        return value.lower()


class IssueRefundArguments(ToolArguments):
    order_id: str = Field(pattern=r"^ORD-[0-9]{4}$", examples=["ORD-1002"])
    amount: Decimal = Field(gt=0, max_digits=8, decimal_places=2)


class FetchUrlArguments(ToolArguments):
    url: HttpUrl
