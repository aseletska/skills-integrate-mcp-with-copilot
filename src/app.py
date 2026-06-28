"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
import os
from pathlib import Path
from secrets import token_urlsafe
from typing import Optional

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}

# In-memory users and auth sessions for demo purposes.
users = {
    "admin_teacher": {
        "password": "teach123",
        "role": "admin",
        "email": "admin@mergington.edu"
    },
    "emma@mergington.edu": {
        "password": "student123",
        "role": "student",
        "email": "emma@mergington.edu"
    },
    "michael@mergington.edu": {
        "password": "student123",
        "role": "student",
        "email": "michael@mergington.edu"
    }
}

sessions = {}


class LoginRequest(BaseModel):
    username: str
    password: str


class ActivityCreateRequest(BaseModel):
    name: str
    description: str
    schedule: str
    max_participants: int = Field(gt=0)
    participants: list[str] = Field(default_factory=list)


class ActivityUpdateRequest(BaseModel):
    description: Optional[str] = None
    schedule: Optional[str] = None
    max_participants: Optional[int] = Field(default=None, gt=0)


def get_current_user(x_auth_token: Optional[str]) -> dict:
    if not x_auth_token:
        raise HTTPException(status_code=401, detail="Authentication required")

    user = sessions.get(x_auth_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired auth token")
    return user


def ensure_admin(user: dict) -> None:
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")


@app.post("/auth/login")
def login(payload: LoginRequest):
    user_record = users.get(payload.username)
    if not user_record or user_record["password"] != payload.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = token_urlsafe(24)
    user = {
        "username": payload.username,
        "email": user_record["email"],
        "role": user_record["role"]
    }
    sessions[token] = user

    return {
        "token": token,
        "user": user
    }


@app.get("/auth/me")
def who_am_i(x_auth_token: Optional[str] = Header(default=None)):
    return get_current_user(x_auth_token)


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities")
def create_activity(payload: ActivityCreateRequest, x_auth_token: Optional[str] = Header(default=None)):
    user = get_current_user(x_auth_token)
    ensure_admin(user)

    if payload.name in activities:
        raise HTTPException(status_code=400, detail="Activity already exists")

    activities[payload.name] = {
        "description": payload.description,
        "schedule": payload.schedule,
        "max_participants": payload.max_participants,
        "participants": payload.participants,
    }

    return {"message": f"Created activity {payload.name}"}


@app.patch("/activities/{activity_name}")
def update_activity(activity_name: str, payload: ActivityUpdateRequest, x_auth_token: Optional[str] = Header(default=None)):
    user = get_current_user(x_auth_token)
    ensure_admin(user)

    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = activities[activity_name]

    if payload.description is not None:
        activity["description"] = payload.description
    if payload.schedule is not None:
        activity["schedule"] = payload.schedule
    if payload.max_participants is not None:
        if payload.max_participants < len(activity["participants"]):
            raise HTTPException(
                status_code=400,
                detail="max_participants cannot be smaller than current participant count"
            )
        activity["max_participants"] = payload.max_participants

    return {"message": f"Updated activity {activity_name}"}


@app.delete("/activities/{activity_name}")
def delete_activity(activity_name: str, x_auth_token: Optional[str] = Header(default=None)):
    user = get_current_user(x_auth_token)
    ensure_admin(user)

    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    del activities[activity_name]
    return {"message": f"Deleted activity {activity_name}"}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, x_auth_token: Optional[str] = Header(default=None)):
    """Sign up a student for an activity"""
    user = get_current_user(x_auth_token)

    if user["role"] == "student" and user["email"] != email:
        raise HTTPException(status_code=403, detail="Students can only sign up themselves")

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    if len(activity["participants"]) >= activity["max_participants"]:
        raise HTTPException(status_code=400, detail="Activity is full")

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, x_auth_token: Optional[str] = Header(default=None)):
    """Unregister a student from an activity"""
    user = get_current_user(x_auth_token)

    if user["role"] == "student" and user["email"] != email:
        raise HTTPException(status_code=403, detail="Students can only unregister themselves")

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
