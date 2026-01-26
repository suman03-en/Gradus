from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import re

phone_regex = RegexValidator(
    regex=r"^\d{10}$",
    message="Phone number must be exactly 10 digits."
)

def validate_roll_number(value):
    regex=r'[A-Z]{3}\d{3,5}[A-Z]{3,5}\d{3}'
    is_match = re.fullmatch(regex, value)
    if not is_match:
        raise ValidationError("Invalid Roll no. Must be Capital Letters and digits")