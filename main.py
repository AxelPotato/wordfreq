from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from wordfreq import zipf_frequency
import re

# Initialize the FastAPI app
app = FastAPI(title="WordFreq Context API", description="Finds rare words and maps their text locations.")

# Define the incoming JSON payload structure
class TextAnalysisRequest(BaseModel):
    text: str
    lang: str = "en"
    zipf_threshold: float = 3.5  # Words with a score below this are considered "hard"

@app.post("/api/analyze")
def analyze_text(request: TextAnalysisRequest):
    try:
        text = request.text
        lang = request.lang
        threshold = request.zipf_threshold

        # 1. Map sentence boundaries (to provide context for the LLM)
        sentences = []
        # Matches sequences of characters ending in punctuation or a newline
        sentence_regex = re.compile(r'[^.!?\n]+[.!?\n]*')
        for match in sentence_regex.finditer(text):
            sentences.append({
                "text": match.group().strip(),
                "start": match.start(),
                "end": match.end()
            })

        # 2. Setup Word Extraction
        # This Regex matches English and Russian words, and safely includes internal hyphens/apostrophes (e.g., Michelin-star, don't)
        word_regex = re.compile(r"[a-zA-Zа-яА-ЯёЁ]+(?:[-'][a-zA-Zа-яА-ЯёЁ]+)*")
        
        results = []
        score_cache = {} # Cache scores so we don't recalculate the same word multiple times

        # 3. Scan text, score words, and map locations
        for match in word_regex.finditer(text):
            word_raw = match.group()
            word_lower = word_raw.lower()

            # Calculate Zipf score if we haven't seen this word yet
            if word_lower not in score_cache:
                score_cache[word_lower] = zipf_frequency(word_lower, lang)
            
            score = score_cache[word_lower]

            # If the word is rare enough, add it to our output list
            if score <= threshold:
                loc = match.start()
                context_sentence = text  # Fallback if sentence mapping fails
                
                # Find which sentence this specific word belongs to
                for s in sentences:
                    if s["start"] <= loc < s["end"]:
                        context_sentence = s["text"]
                        break
                
                # Append the exact JSON structure the n8n LLM node expects
                results.append({
                    "word_location": loc,
                    "word": word_raw,
                    "sentence": context_sentence,
                    "zipf_score": score # Included for your visibility/debugging
                })
        
        # FastAPI automatically serializes this list into JSON
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}
