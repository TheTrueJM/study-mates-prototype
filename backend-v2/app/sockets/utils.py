# In backend-v2/app/sockets/utils.py

import uuid
import random

COLORS = ["Red", "Blue", "Green", "Yellow", "Purple", "Orange", "Pink", "Cyan", "Magenta", "Lime",
          "Indigo", "Violet", "Coral", "Teal", "Gold", "Silver", "Bronze", "Maroon", "Navy", "Azure"]
ANIMALS = ["Elephant", "Tiger", "Lion", "Bear", "Wolf", "Fox", "Eagle", "Hawk", "Dolphin", "Whale",
           "Panda", "Koala", "Kangaroo", "Penguin", "Owl", "Raven", "Falcon", "Shark", "Otter", "Deer"]

def generate_student_uuid():
    """Generate a UUID for student"""
    return str(uuid.uuid4())

def generate_student_name():
    """Generate a name in 'Colour-Animal' format"""
    return f"{random.choice(COLORS)}-{random.choice(ANIMALS)}"