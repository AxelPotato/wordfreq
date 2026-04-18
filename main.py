from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from wordfreq import zipf_frequency

# Initialize the FastAPI app
app = FastAPI(title="WordFreq API", description="Microservice for Zipf word frequency")

# Define the expected JSON payload format
class WordRequest(BaseModel):
    word: str
    lang: str = "en" # Defaults to English if not provided

@app.post("/api/frequency")
def get_frequency(request: WordRequest):
    try:
        # Calculate the Zipf score
        # Returns a float between 0.0 (rare) and 8.0 (extremely common)
        score = zipf_frequency(request.word, request.lang)
        
        return {
            "status": "success",
            "word": request.word,
            "lang": request.lang,
            "zipf_score": score
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Optional health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}