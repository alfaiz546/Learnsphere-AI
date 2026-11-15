from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.ai_client import get_genai_client
from app.models.question import Question
import uuid

def get_tutor_explanation(db: Session, student_id: uuid.UUID, concept: str, question_id: str = None, student_misconception: str = None) -> dict:
    client = get_genai_client()
    if not client:
        return {
            "error": "GEMINI_API_KEY not configured. Add your API key in .env",
            "explanation": None
        }
    
    context = f"Concept: {concept}\n"
    if question_id:
        try:
            q = db.query(Question).filter(Question.id == uuid.UUID(question_id)).first()
            if q:
                context += f"Question: {q.question_text}\nCorrect Answer: {q.correct_answer}\nExplanation: {q.explanation}\n"
        except Exception:
            pass
    if student_misconception:
        context += f"Student's answer/confusion: {student_misconception}\n"
    
    try:
        prompt = f"""You are LearnSphere AI Tutor, a brilliant, patient, and engaging educator inspired by Brilliant.org's guided learning philosophy.
{context}

Provide a clear, engaging explanation appropriate for a student learning this concept:
- Use simple, intuitive language and concrete real-world analogies
- Break down complex ideas step-by-step
- If addressing a mistake or misconception, gently explain WHY it happened without making them feel bad
- Provide an intuitive mini-example
- Encourage the student to think critically and try the next step

Respond in a warm, encouraging, conversational tone."""
        
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt
        )
        return {
            "explanation": response.text,
            "concept": concept,
            "has_context": bool(question_id or student_misconception)
        }
    except Exception as e:
        return {"error": f"AI explanation failed: {str(e)}", "explanation": None}
