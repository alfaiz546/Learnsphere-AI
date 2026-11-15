from sqlalchemy.orm import Session
import uuid, json
from app.core.config import settings
from app.core.ai_client import get_genai_client

def generate_questions(db: Session, student_id: uuid.UUID, subject_id: str = None, topic: str = "Math", difficulty: str = "beginner", count: int = 5) -> dict:
    client = get_genai_client()
    if not client:
        return {"error": "GEMINI_API_KEY not configured", "questions": []}
    
    try:
        prompt = f"""Generate {count} educational questions about "{topic}" at {difficulty} level.
Return ONLY valid JSON in this exact format:
{{
  "questions": [
    {{
      "question_text": "...",
      "question_type": "multiple_choice",
      "correct_answer": "a",
      "explanation": "...",
      "hint": "...",
      "options": [
        {{"text": "Option A", "is_correct": true}},
        {{"text": "Option B", "is_correct": false}},
        {{"text": "Option C", "is_correct": false}},
        {{"text": "Option D", "is_correct": false}}
      ]
    }}
  ]
}}"""
        
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt
        )
        text = response.text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        
        data = json.loads(text)
        return {"questions": data.get("questions", []), "count": len(data.get("questions", []))}
    except Exception as e:
        return {"error": f"Question generation failed: {str(e)}", "questions": []}
