import os, requests

BACKEND = os.getenv("BACKEND_URL").rstrip("/")

def start_agent(student_id:int, lesson_id:int, level_slug:str):
    r = requests.post(f"{BACKEND}/agent/start", json={"student_id":student_id,"lesson_id":lesson_id,"level_slug":level_slug})
    r.raise_for_status()
    return r.json()

def get_quiz(student_id:int, lesson_id:int, level_slug:str):
    r = requests.post(f"{BACKEND}/agent/quiz", json={"student_id":student_id,"lesson_id":lesson_id,"level_slug":level_slug})
    r.raise_for_status()
    return r.json()["items"]

def grade_quiz(student_id:int, lesson_id:int, level_slug:str, answers:list[str], assignment_id:int|None=None):
    r = requests.post(f"{BACKEND}/agent/grade", json={"student_id":student_id,"lesson_id":lesson_id,"level_slug":level_slug,"answers":answers,"assignment_id":assignment_id})
    r.raise_for_status()
    d = r.json(); return d["score"], d["total"]

def next_step(student_id:int, lesson_id:int, level_slug:str, answers:list[str], assignment_id:int|None=None):
    r = requests.post(f"{BACKEND}/agent/coach_or_celebrate", json={"student_id":student_id,"lesson_id":lesson_id,"level_slug":level_slug,"answers":answers,"assignment_id":assignment_id})
    r.raise_for_status()
    return r.json()
