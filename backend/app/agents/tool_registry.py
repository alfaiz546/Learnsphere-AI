from typing import Any, Dict, List
from sqlalchemy.orm import Session
import logging, json, uuid, time

logger = logging.getLogger(__name__)

class ToolRegistry:
    def __init__(self, db: Session, student_id: uuid.UUID):
        self.db = db
        self.student_id = student_id
        self._register_tools()
    
    def _register_tools(self):
        from app.agents.tools.assessment_tool import assess_answer
        from app.agents.tools.weakness_tool import analyze_weaknesses
        from app.agents.tools.study_plan_tool import generate_study_plan
        from app.agents.tools.question_generator import generate_questions
        from app.agents.tools.tutor_tool import get_tutor_explanation
        from app.agents.tools.progress_analyzer import analyze_progress
        from app.agents.tools.recommendation_tool import get_recommendations
        
        self.tools = {
            "assess_answer": assess_answer,
            "analyze_weaknesses": analyze_weaknesses,
            "generate_study_plan": generate_study_plan,
            "generate_questions": generate_questions,
            "get_tutor_explanation": get_tutor_explanation,
            "analyze_progress": analyze_progress,
            "get_recommendations": get_recommendations
        }
    
    def get_tool_schemas(self) -> List[Dict]:
        return [
            {
                "name": "analyze_weaknesses",
                "description": "Analyze student's weak topics based on historical test and practice data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "time_period_days": {"type": "integer", "description": "Number of days of history to analyze", "default": 30}
                    }
                }
            },
            {
                "name": "generate_study_plan",
                "description": "Create a personalized multi-day study plan and save it directly to the database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "goal": {"type": "string", "description": "Student's learning goal"},
                        "available_hours_per_day": {"type": "number", "description": "Hours available per day"},
                        "duration_days": {"type": "integer", "description": "Plan duration in days (e.g. 7 or 30)"}
                    },
                    "required": ["goal", "available_hours_per_day", "duration_days"]
                }
            },
            {
                "name": "get_tutor_explanation",
                "description": "Get an educational explanation for a concept, question, or misconception",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "concept": {"type": "string", "description": "Concept to explain"},
                        "question_id": {"type": "string", "description": "Optional question ID for context"},
                        "student_misconception": {"type": "string", "description": "Student's incorrect answer or confusion"}
                    },
                    "required": ["concept"]
                }
            },
            {
                "name": "analyze_progress",
                "description": "Analyze student's current learning progress, completion rates, and streak",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_recommendations",
                "description": "Get personalized course recommendations based on student's performance",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Number of recommendations", "default": 5}
                    }
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}
        
        start_time = time.time()
        self._log_start(tool_name, params)
        
        try:
            tool_fn = self.tools[tool_name]
            result = tool_fn(self.db, self.student_id, **params)
            elapsed = int((time.time() - start_time) * 1000)
            self._log_success(tool_name, params, result, elapsed)
            return result
        except Exception as e:
            elapsed = int((time.time() - start_time) * 1000)
            logger.error(f"Tool {tool_name} failed: {e}")
            self._log_failure(tool_name, params, str(e), elapsed)
            return {"error": str(e)}
    
    def _log_start(self, tool_name: str, params: dict):
        from app.models.agent_log import AgentExecutionLog
        try:
            log = AgentExecutionLog(
                student_id=self.student_id,
                tool_name=tool_name,
                input_data=json.dumps(params, default=str),
                status="started"
            )
            self.db.add(log)
            self.db.commit()
        except Exception:
            pass
    
    def _log_success(self, tool_name: str, params: dict, result: dict, elapsed: int):
        from app.models.agent_log import AgentExecutionLog
        try:
            log = AgentExecutionLog(
                student_id=self.student_id,
                tool_name=tool_name,
                input_data=json.dumps(params, default=str),
                output_data=json.dumps(result, default=str),
                status="success",
                execution_time_ms=elapsed
            )
            self.db.add(log)
            self.db.commit()
        except Exception:
            pass
    
    def _log_failure(self, tool_name: str, params: dict, error: str, elapsed: int):
        from app.models.agent_log import AgentExecutionLog
        try:
            log = AgentExecutionLog(
                student_id=self.student_id,
                tool_name=tool_name,
                input_data=json.dumps(params, default=str),
                status="failed",
                error_message=error,
                execution_time_ms=elapsed
            )
            self.db.add(log)
            self.db.commit()
        except Exception:
            pass
