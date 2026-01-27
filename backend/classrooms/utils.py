import string
import random

def generate_classroom_code():
    # Returns a code like 'AB-C12-D3'
    chars = string.ascii_uppercase + string.digits
    part1 = ''.join(random.choices(chars, k=2))
    part2 = ''.join(random.choices(chars, k=3))
    part3 = ''.join(random.choices(chars, k=2))
    return f"{part1}-{part2}-{part3}"
    