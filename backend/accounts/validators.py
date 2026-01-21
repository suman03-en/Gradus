from django.core.exceptions import ValidationError
import re

def validate_roll_number(value):
    regex=r'\w{3}\d{3,5}\w{3,5}\d{3}'
    is_match = re.fullmatch(regex, value)
    if not is_match:
        raise ValidationError("Invalid Roll no.")