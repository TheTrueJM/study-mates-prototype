import random, string, uuid

COLORS = ["Red", "Blue", "Green", "Yellow", "Purple", "Orange", "Pink", "Cyan", "Magenta", "Lime",
          "Indigo", "Violet", "Coral", "Teal", "Gold", "Silver", "Bronze", "Maroon", "Navy", "Azure"]
ANIMALS = ["Elephant", "Tiger", "Lion", "Bear", "Wolf", "Fox", "Eagle", "Hawk", "Dolphin", "Whale",
           "Panda", "Koala", "Kangaroo", "Penguin", "Owl", "Raven", "Falcon", "Shark", "Otter", "Deer"]

def generate_tutorial_code(length = 6):
    return ''.join(random.choices(string.ascii_uppercase, k=length))

def generate_student_uuid():
    return str(uuid.uuid4())

def generate_student_name():
    return f"{random.choice(COLORS)}-{random.choice(ANIMALS)}"