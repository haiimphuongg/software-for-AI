import os
import random
from dotenv import load_dotenv
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from Controller.bookController import BookController
from Controller.userController import UserController
import requests
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import PlainTextResponse
load_dotenv()

mlRoute = APIRouter()

IMPRESSIONS = Counter('recommendations_impressions_total', 'Total number of recommendation impressions', ['model'])
CLICKS = Counter('recommendations_clicks_total', 'Total number of recommendation clicks', ['model'])
CTR = Gauge('recommendations_ctr', 'Click-through rate for recommendations', ['model'])

class UserID(BaseModel):
    user_id: str

class RecommendationRequest(BaseModel):
    user_id: str
    num_recommendations: int = 5

class Recommendation(BaseModel):
    item_id: str

class RecommendationResponse(BaseModel):
    recommendations: List[Recommendation]


async def create_id_mapping():
    all_books = await BookController.get_books(get_all=True)
    return {i+1: str(book.id) for i, book in enumerate(all_books)}

async def create_id_user_mapping():
    list_user = await UserController.get_all_user(get_all=True)
    return {str(user.id): i+1 for i, user in enumerate(list_user)}

async def get_model_name(request: Request) -> str:
    if random.random() < 0.5:  
        model_name = "collaborate_base_recommend"
    else:  
        model_name = "content_based_recommend"
    IMPRESSIONS.labels(model=model_name).inc()
    request.state.model_name = model_name
    return model_name



def get_recommendations_from_hf(model_name: str, user_id: int, num_recommendations: int):
    if model_name == "content_based_recommend":
        API_URL = "https://oj0jhtqo7z7orgme.us-east-1.aws.endpoints.huggingface.cloud"
    elif model_name == "collaborate_base_recommend":
        API_URL = "https://tlrzvg4ssn69uxzy.us-east-1.aws.endpoints.huggingface.cloud"
    else:
        raise ValueError(f"Invalid model name: {model_name}")

    hf_api_token = os.getenv("HF_API_TOKEN")
    if not hf_api_token:
        raise ValueError("Hugging Face API token not found in environment variables")

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {hf_api_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": {
            "user_id": user_id,
            "k": num_recommendations
        }
    }

    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to get recommendations from {model_name}, status code: {response.status_code}")

@mlRoute.post("/recommend", response_model=RecommendationResponse)
async def get_recommendations(request: Request, req: RecommendationRequest, model_name: str = Depends(get_model_name)):
    try:
        # Fetch the book ID mapping
        book_id_mapping = await create_id_mapping()
        
        # Fetch the user ID mapping
        user_id_mapping = await create_id_user_mapping()
        
        # Map the input user ID to the model's user ID
        model_user_id = user_id_mapping.get((req.user_id))
        
        if model_user_id is None:
            raise HTTPException(status_code=404, detail="User not found in the mapping")

        # Get recommendations from the model using the mapped user ID
        response = get_recommendations_from_hf(model_name, model_user_id, req.num_recommendations)
        recommended_books_indices = response[0]["recommended_books"]

        # Use the book ID mapping to convert indices to actual book IDs, applying modulo operation
        num_books = len(book_id_mapping)
        formatted_recommendations = [
            Recommendation(item_id=book_id_mapping[(int(book_index) % num_books) + 1])
            for book_index in recommended_books_indices[:req.num_recommendations]
        ]

        return RecommendationResponse(recommendations=formatted_recommendations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")
@mlRoute.post("/click")
async def track_click(model_name: str, user_id: int):
    CLICKS.labels(model=model_name).inc()
    impressions = IMPRESSIONS.labels(model=model_name)._value.get()
    clicks = CLICKS.labels(model=model_name)._value.get()
    if impressions > 0:
        CTR.labels(model=model_name).set(clicks / impressions)
    return {"message": "Click tracked"}

@mlRoute.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)

@mlRoute.post("/reset_metrics")
async def reset_metrics():
    for model in ["collaborate_base_recommend", "content_based_recommend"]:
        IMPRESSIONS.labels(model=model)._value.set(0)
        CLICKS.labels(model=model)._value.set(0)
        CTR.labels(model=model).set(0)
    
    return {"message": "Metrics reset successfully"}