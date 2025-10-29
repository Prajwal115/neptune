from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from pydantic import BaseModel
import os
import json
from pathlib import Path
import hashlib # Used to demonstrate simple, non-secure hashing for uniqueness

# Initialize the FastAPI application
app = FastAPI()

# --- Configuration & File Paths ---
BASE_DIR = Path(__file__).resolve().parent
# Path to the JSON file storing user credentials
USERS_FILE = BASE_DIR / "users.json" 

# 1. Mount the 'res' directory for static files
app.mount("/res", StaticFiles(directory=BASE_DIR / "res"), name="res")


# --- Pydantic Model for API Request ---
# This model works for both Registration and Login
class UserRegistration(BaseModel):
    """Schema for the registration request body."""
    username: str
    password: str

# --- Utility Functions for File Handling ---

def hash_password_mock(password: str) -> str:
    """
    WARNING: This is a NON-SECURE MOCK of password hashing. 
    In a real application, you MUST use a library like 'bcrypt' or 'argon2' 
    for proper, secure password hashing.
    """
    return hashlib.sha256(password.encode()).hexdigest()

def load_users() -> dict:
    """Loads all registered users from the JSON file."""
    if not USERS_FILE.exists():
        return {}
    
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_users(users: dict):
    """Saves the current dictionary of users to the JSON file."""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

# --- Endpoint Definitions ---

@app.get("/")
async def serve_index():
    """Serves the index.html file."""
    html_file_path = BASE_DIR / "index.html"
    if not html_file_path.exists():
        return JSONResponse({"error": "index.html not found"}, status_code=404)
    return FileResponse(html_file_path, media_type="text/html")

@app.get("/login")
async def serve_login():
    """Serves the login.html file."""
    html_file_path = BASE_DIR / "login.html"
    if not html_file_path.exists():
        return JSONResponse({"error": "login.html not found"}, status_code=404)
    return FileResponse(html_file_path, media_type="text/html")

@app.get("/register")
async def serve_register():
    """Serves the register.html file."""
    html_file_path = BASE_DIR / "register.html"
    if not html_file_path.exists():
        return JSONResponse({"error": "register.html not found"}, status_code=404)
    return FileResponse(html_file_path, media_type="text/html")

@app.get("/logout")
async def logout_user():
    """Serves the register.html file."""
    html_file_path = BASE_DIR / "logout.html"
    if not html_file_path.exists():
        return JSONResponse({"error": "logout.html not found"}, status_code=404)
    return FileResponse(html_file_path, media_type="text/html")

@app.get("/home")
async def serve_home():
    """Serves the home.html file."""
    html_file_path = BASE_DIR / "home.html"
    if not html_file_path.exists():
        return JSONResponse({"error": "home.html not found"}, status_code=404)
    return FileResponse(html_file_path, media_type="text/html")


@app.post("/api/register")
async def register_user(user_data: UserRegistration):
    """
    Handles user registration:
    1. Checks if username exists.
    2. Stores credentials in users.json.
    3. Creates a user-specific directory.
    """
    username = user_data.username
    password = user_data.password # This is the raw password
    
    # 1. Load existing users
    users = load_users()
    
    # 2. Check for existing username
    if username in users:
        raise HTTPException(status_code=400, detail="Username already exists. Please choose a different one.")
        
    # 3. Securely store password (MOCK implementation)
    # NOTE: We are storing the raw password for functional testing, 
    # but the hash_password_mock function exists to highlight where real hashing should occur.
    users[username] = {
        "password_hash": hash_password_mock(password), # Store hash
        "raw_password_unsafe": password,               # Storing raw password for dev testing ONLY
        "directory": str(BASE_DIR / username)
    }
    
    # 4. Save user data
    save_users(users)
    
    # 5. Create user-specific directory
    user_dir = BASE_DIR / username
    try:
        # Create directory, including intermediate directories if necessary
        user_dir.mkdir(parents=True, exist_ok=True)
        # Create a placeholder file to prove the directory exists
        (user_dir / "placeholder.txt").write_text(f"Files for user {username}")
    except OSError as e:
        # Handle file system error (rare, but good practice)
        print(f"Error creating directory for user {username}: {e}")
        # Optionally, remove the user from JSON if dir creation fails (rollback)
        # del users[username]
        # save_users(users)
        raise HTTPException(status_code=500, detail="Internal server error during directory setup.")
        
    return {"message": "User registered successfully and personal directory created.", "username": username}


@app.post("/api/login")
async def login_user(user_data: UserRegistration):
    """
    Handles user login by verifying credentials against the stored user data.
    """
    username = user_data.username
    password = user_data.password 
    
    users = load_users()
    
    # Check for existing username
    if username not in users:
        # Return generic error to prevent username enumeration
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    
    user = users[username]
    
    # Verify password (using insecure mock raw password comparison for dev purposes)
    if password != user.get("raw_password_unsafe"):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
        
    # Successful login
    return {"message": "Login successful!", "username": username}


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from datetime import datetime

SUPABASE_URL = "https://egngwqymsimurzldnubz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVnbmd3cXltc2ltdXJ6bGRudWJ6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE2ODUwMDksImV4cCI6MjA3NzI2MTAwOX0.8cCsFcYjBODPVUWh7gcuRDdsTi4dxRSdfs43MUhlRgU"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class ProjectCreate(BaseModel):
    user_id: str

    name: str
    description: str

@app.post("/create-project")
def create_project(data: ProjectCreate):
    try:
        payload = {
            "user_id": data.user_id,
            "name": data.name,
            "description": data.description,
            "created_at": datetime.utcnow().isoformat()
        }
        response = supabase.table("projects").insert(payload).execute()
        if response.data:
            return {"success": True, "message": "Project created successfully"}
    except:
        raise HTTPException(status_code=500, detail="Supabase insert failed")
    


supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class UserRequest(BaseModel):
    user_id: str

@app.post("/fetch-projects")
def fetch_projects(data: UserRequest):
    print("Recieved user_id:", data.user_id)
    try:
        response = supabase.table("projects").select("*").eq("user_id", data.user_id).execute()
        if response.data:
            return {"success": True, "projects": response.data}
        else:
            return {"success": True, "projects": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase error: {str(e)}")