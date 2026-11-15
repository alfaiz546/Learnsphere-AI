# LearnSphere AI 🎓
> **Brilliant-Inspired Interactive STEM & Logic Learning Platform with an Autonomous AI Mentor Agent**

LearnSphere AI is a full-stack educational web application designed around the philosophy:
> *"Learn by Doing, Understand by Exploring, Improve with AI."*

Taking core inspiration from Brilliant.org's interactive, problem-solving-based pedagogy, LearnSphere AI features custom interactive lessons, dynamic question validations, gamification (streaks & XP), and an autonomous **AI Mentor Agent** integrated with 7 real database tools.

---

## 🏗 Architecture & Tech Stack

### Frontend
- **Framework:** React 18 + TypeScript + Vite
- **Styling:** Tailwind CSS (Dark/Light mode support)
- **Routing:** React Router v6 (Protected student and admin routes)
- **Data Fetching:** TanStack React Query v5
- **Visual Analytics:** Recharts
- **Icons:** Lucide React

### Backend
- **Framework:** Python FastAPI
- **Data Validation:** Pydantic v2
- **ORM:** SQLAlchemy 2.0
- **Database:** PostgreSQL 16 (with seed content)
- **Authentication:** JWT (Access & Refresh tokens) with bcrypt password hashing
- **Caching:** Redis 5 (with graceful degradation fallback)
- **Rate Limiting:** SlowAPI / in-memory rate limiting
- **AI Agent Orchestrator:** Google Gemini API with native function/tool calling

---

## 🧠 Central AI Mentor Agent & 7 Backend Tools

LearnSphere AI includes a centralized AI orchestrator with a tool registry. When a student interacts with the AI Tutor, the agent selects and executes backend tools:

1. **Assessment Tool (`assess_answer`)**: Real-time deterministic evaluation of question attempts, scoring, and PostgreSQL storage.
2. **Weakness Analysis Tool (`analyze_weaknesses`)**: Analyzes the student's actual historical answer accuracy to flag weak concepts and recurring mistakes.
3. **Study Plan Generator (`generate_study_plan`)**: Generates personalized 7-day and 30-day schedules based on student goals, available hours, and detected weak topics.
4. **Question Generator (`generate_questions`)**: Generates subject-specific questions with difficulty tiers, hints, and explanations in structured JSON.
5. **AI Tutor Tool (`get_tutor_explanation`)**: Socratic-style guided conceptual explanation and misconception resolution.
6. **Progress Analyzer (`analyze_progress`)**: Evaluates real-time completion rates, active streak, and XP transactions.
7. **Recommendation Tool (`get_recommendations`)**: Recommends next lessons and courses based on student track progress and prerequisites.

---

## 🗄 Database Design (PostgreSQL)

The platform includes normalized tables:
- `users`: User identity, hashed credentials, and role (`student` / `admin`).
- `student_profiles`: XP total, streak counters, daily learning targets.
- `subjects`: Core STEM tracks (Mathematics, Science, Computer Science, Logical Reasoning).
- `courses`: Modules, estimated hours, difficulty levels.
- `modules`: Course curriculum divisions.
- `lessons`: Concepts, visual diagram blocks, interactive challenges.
- `questions`: Question text, types (`multiple_choice`, `true_false`, `numerical`, `coding`), hints, explanations.
- `question_options`: Deterministic multiple choice choices.
- `assessments` & `student_answers` & `assessment_results`: Student submission logs, scores, and performance history.
- `learning_progress`: Lesson completion status and percentages.
- `learning_paths`: Course enrollments.
- `study_plans`: Generated multi-day schedules stored in JSON format.
- `ai_conversations` & `ai_messages`: Contextual conversation logs.
- `agent_execution_logs`: Audit trail for tool executions (status, execution time ms, inputs/outputs).
- `achievements` & `student_achievements`: Gamified badges and milestones.
- `xp_transactions`: Audit log of XP rewards.

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- PostgreSQL 16
- Redis

### 2. Backend Setup
```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start services
brew services start postgresql@16
brew services start redis

# Setup environment variables
cp .env.example .env
# Optional: Add your Google Gemini API key to .env:
# GEMINI_API_KEY=your_gemini_api_key

# Run database setup & seeding
python -c "from app.database.init_db import init_db; init_db()"

# Run tests
PYTHONPATH=. pytest app/tests/ -v

# Start backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API documentation will be available at:
`http://localhost:8000/docs`

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run build
npm run dev
```
The application will launch on `http://localhost:5173`.

---

## 🔑 Default Accounts

- **Administrator:**
  - Email: `admin@learnsphere.ai`
  - Password: `Admin123!`
- **Student:**
  - Create any new student account via the `/register` page with instant access.
