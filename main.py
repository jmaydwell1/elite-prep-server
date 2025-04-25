from datetime import date, datetime, timezone
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field, field_validator
from pymongo.mongo_client import MongoClient # type: ignore
from pymongo.server_api import ServerApi # type: ignore
from typing import Optional, List
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
print("API Key loaded:", os.getenv("OPENAI_API_KEY") is not None)  # Debug print

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# MongoDB connection
uri = "mongodb+srv://eliteprep:test@cluster0.vlsnw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0&tlsAllowInvalidCertificates=true&ssl=true"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client.eliteprep  # database name

# OpenAI client initialization
client = OpenAI(
    api_key="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"
)

class OnboardingData(BaseModel):
    email: EmailStr
    name: str
    birthdate: datetime
    gender: str
    city: str
    state: str
    sport: List[str]
    athletic_status: str
    handicap: int
    expectation: str
    goal: str

    @field_validator('birthdate', mode='before')
    def parse_birthdate(cls, value):
        if isinstance(value, date) and not isinstance(value, datetime):
            return datetime.combine(value, datetime.min.time())
        return value

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UserCreate(BaseModel):
    password: str = Field(
        min_length=6,
        pattern=r'^[A-Za-z\d!@#$%^&*(),.?":{}|<>]{6,}$',
        example="Password123!"
    )
    email: EmailStr

class PerformanceTrends(BaseModel):
    email: EmailStr
    focus: int
    confidence: int
    anxiety: int
    enjoyment: int
    burnout: int
    effort: int
    motivation: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class User(BaseModel):
    email: EmailStr
    password: str
    onboarding_data: Optional[OnboardingData] = None
    performance_trends: List[PerformanceTrends] = []

@app.post("/register")
async def register_user(user: UserCreate):
    # Check if username already exists
    if db.users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create new user
    user_dict = user.model_dump()
    db.users.insert_one(user_dict)
    return {"message": "User registered successfully"}

@app.post("/login")
async def login_user(user: User):
    # Find user by username and password
    found_user = db.users.find_one({
        "email": user.email,
        "password": user.password
    })
    
    if not found_user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    return {"message": "Login successful"}

@app.post("/onboarding")
async def onboarding(user: OnboardingData):
    print("Debug - user:", user)
    try:
        # First check if user exists
        if not db.users.find_one({"email": user.email}):
            raise HTTPException(status_code=404, detail="User not found")
        
        # Convert to dict and exclude email
        update_data = {"onboarding_data": user.model_dump(exclude={'email'})}
        
        result = db.users.update_one(
            {"email": user.email},
            {"$set": update_data}
        )
        
        if result.modified_count == 1:
            return {"message": "User updated with onboarding data"}
        else:
            return {"message": "No changes made"}
            
    except Exception as e:
        print(f"Debug - Error: {str(e)}")  # Debug print
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/performance-trends")
async def performance_trends(user: PerformanceTrends):
    try:
        if not db.users.find_one({"email": user.email}):
            raise HTTPException(status_code=404, detail="User not found")
        
        result = db.users.update_one(
            {"email": user.email},
            {"$push": {"performance_trends": user.model_dump(exclude={'email'})}}
        )
        
        if result.modified_count == 1:
            return {"message": "User updated with performance trends"}
        else:
            return {"message": "No changes made"}
        
    except Exception as e:
        print(f"Debug - Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/performance-averages/{email}")
async def get_performance_averages(email: EmailStr):
    try:
        print(f"Fetching performance averages for email: {email}")  # Debug log
        
        # Find user and their performance trends
        user = db.users.find_one({"email": email})
        if not user:
            print(f"User not found in database: {email}")  # Debug log
            raise HTTPException(status_code=404, detail="User not found")
            
        if "performance_trends" not in user:
            print(f"No performance trends found for user: {email}")  # Debug log
            raise HTTPException(status_code=404, detail="No performance data available")
        
        trends = user["performance_trends"]
        if not trends:
            print(f"Empty performance trends array for user: {email}")  # Debug log
            raise HTTPException(status_code=404, detail="No performance trends found")
        
        print(f"Found {len(trends)} performance trends for user: {email}")  # Debug log
        
        # Calculate individual averages
        metrics = {
            "email": email,
            "average_focus": sum(t["focus"] for t in trends) / len(trends),
            "average_confidence": sum(t["confidence"] for t in trends) / len(trends),
            "average_anxiety": sum(t["anxiety"] for t in trends) / len(trends),
            "average_enjoyment": sum(t["enjoyment"] for t in trends) / len(trends),
            "average_burnout": sum(t["burnout"] for t in trends) / len(trends),
            "average_effort": sum(t["effort"] for t in trends) / len(trends),
            "average_motivation": sum(t["motivation"] for t in trends) / len(trends),
            "total_entries": len(trends),
            "last_updated": trends[-1]["timestamp"] if trends else None
        }
        
        # Calculate total average (excluding anxiety and burnout as they are negative metrics)
        positive_metrics = [
            metrics["average_focus"],
            metrics["average_confidence"],
            metrics["average_enjoyment"],
            metrics["average_effort"],
            metrics["average_motivation"]
        ]
        
        metrics["total_average"] = sum(positive_metrics) / len(positive_metrics)
        
        print(f"Successfully calculated metrics for user: {email}")  # Debug log
        return metrics
        
    except Exception as e:
        print(f"Debug - Error: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Welcome to ElitePrep API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)