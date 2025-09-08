from .db import check_password, create_student, create_teacher

def authenticate(email, password):
    return check_password(email, password)

def register_student(name, email, password, level, country):
    return create_student(name, email, password, level, country)

def register_teacher(title, name, email, password):
    return create_teacher(title, name, email, password)