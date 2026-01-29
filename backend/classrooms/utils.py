import re
import string
import random

def generate_classroom_code():
    # Returns a code like 'AB-C12-D3'
    chars = string.ascii_uppercase + string.digits
    part1 = ''.join(random.choices(chars, k=2))
    part2 = ''.join(random.choices(chars, k=3))
    part3 = ''.join(random.choices(chars, k=2))
    return f"{part1}-{part2}-{part3}"


def expand_roll_range(range_str):
    ROLL_RANGE_RE = re.compile(
        r"([A-Z]{3}\d{3,5}[A-Z]{3,5})(\d{3})-([A-Z]{3}\d{3,5}[A-Z]{3,5})"
    )
    match = ROLL_RANGE_RE.match(range_str.strip())

    