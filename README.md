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
  - # 👥 Team Members & Contributions

## Our Team — LearnSphere-AI

LearnSphere-AI was developed through the collective effort, collaboration, and dedication of four team members. Every member played an important role in bringing this project to life.

We worked together throughout the development process, sharing ideas, solving problems, implementing features, testing functionality, and improving the overall platform.

### 🚀 Team Members

| No. | Name | GitHub |
|---|---|---|
| 1 | **Mahammadrajin Shaikh** (Team Leader) | [@instinct-coder1](https://github.com/instinct-coder1) |
| 2 | **Alfaiz Khatik** | [@alfaiz546](https://github.com/alfaiz546) |
| 3 | **Mohd Faiz Ansari** | [@MOHDFAIZ03](https://github.com/MOHDFAIZ03) |
| 4 | **Nit Ahangare** | [@nit-2520](https://github.com/nit-2520) |

---

## 💻 Individual Roles & Contributions

### 1. Mahammadrajin Shaikh — Team Leader
**GitHub:** [@instinct-coder1](https://github.com/instinct-coder1)

**Responsibilities:**
- Led the project idea, brainstorming, and overall planning.
- Contributed to frontend development using React.
- Worked on UI/UX design and website pages.
- Participated in testing, debugging, and fixing errors.
- Managed GitHub activities and repository integration.
- Coordinated deployment and overall project integration.

### 2. Alfaiz Khatik — Backend & AI Development
**GitHub:** [@alfaiz546](https://github.com/alfaiz546)

**Responsibilities:**
- Worked on backend development using Python and FastAPI.
- Contributed to API development and backend functionality.
- Integrated Google's Gemini AI into the platform.
- Worked on AI Mentor functionality.
- Contributed to AI agent development and integration.

### 3. Mohd Faiz Ansari — Database & Documentation
**GitHub:** [@MOHDFAIZ03](https://github.com/MOHDFAIZ03)

**Responsibilities:**
- Contributed to database design and integration.
- Worked on organizing and documenting project information.
- Prepared project presentation materials.
- Contributed to PPT preparation and presentation activities.

### 4. Nit Ahangare — Learning Features & User Management
**GitHub:** [@nit-2520](https://github.com/nit-2520)

**Responsibilities:**
- Contributed to authentication and user management.
- Worked on personalized study plan functionality.
- Contributed to learning-related features.
- Worked on progress tracking and assessment functionality.
- Participated in PPT preparation and project documentation.
- Assisted with deployment and project integration.

---

## 🤝 Equal Team Contribution & GitHub Commit Clarification

**LearnSphere-AI is a collaborative project developed by all four team members.**

We would like to clarify that the project was not developed independently by a single team member.

During the hackathon, our team worked together using a single laptop/device for project development. Due to this shared development environment, GitHub commits and code pushes were primarily performed through one team member's GitHub account.

Consequently, the GitHub commit history may not accurately represent the individual contributions of every team member.

All four members actively participated in the development process through their respective responsibilities, collaborative discussions, implementation, problem-solving, testing, documentation, and project improvement.

We believe that teamwork is not measured only by the number of GitHub commits, but also by the collective effort, ideas, responsibilities, and dedication contributed by every team member.

**LearnSphere-AI represents the combined work and equal team effort of all four members.**

---

## 🏆 Acknowledgment

We are proud to have built LearnSphere-AI together. This experience helped us improve our technical skills, collaboration, problem-solving abilities, and understanding of real-world software development.

**Four Members. One Vision. One Team. One Project.**

Thank you for exploring LearnSphere-AI!
