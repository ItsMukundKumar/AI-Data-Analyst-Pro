from google import genai
from app.config import settings

print("API key loaded:", bool(settings.GEMINI_API_KEY))
print("Model:", settings.GEMINI_MODEL)

client = genai.Client(
    api_key=settings.GEMINI_API_KEY
)

response = client.models.generate_content(
    model=settings.GEMINI_MODEL,
    contents="Explain data analysis in two sentences."
)

print("Gemini response:")
print(response.text)