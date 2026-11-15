export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  role: 'student' | 'admin';
  profile?: StudentProfile;
}

export interface StudentProfile {
  xp_total: number;
  current_streak: number;
  longest_streak: number;
  daily_goal_minutes: number;
  subjects_of_interest: string[];
  current_class?: string;
  board?: string;
  current_marks?: number;
  target_exam?: string;
  career_goal?: string;
  target_year?: number;
  category?: string;
}

export interface Subject {
  id: string;
  name: string;
  slug: string;
  description: string;
  icon: string;
  color: string;
  display_order: number;
  course_count?: number;
}

export interface Course {
  id: string;
  subject_id: string;
  title: string;
  slug: string;
  description: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  estimated_hours: number;
  thumbnail_color?: string;
  lesson_count: number;
  subject_name?: string;
  is_enrolled?: boolean;
}

export interface Module {
  id: string;
  title: string;
  description?: string;
  display_order: number;
  lessons: LessonBrief[];
}

export interface LessonBrief {
  id: string;
  title: string;
  lesson_type: string;
  estimated_minutes: number;
  display_order: number;
  status?: 'not_started' | 'in_progress' | 'completed';
}

export interface QuestionOption {
  id: string;
  option_text: string;
  display_order: number;
}

export interface Question {
  id: string;
  question_text: string;
  question_type: 'multiple_choice' | 'true_false' | 'numerical' | 'fill_blank' | 'coding';
  difficulty: string;
  hint?: string;
  correct_answer?: string;
  explanation?: string;
  options: QuestionOption[];
}

export interface LessonDetail {
  id: string;
  title: string;
  description?: string;
  content?: string;
  lesson_type: string;
  estimated_minutes: number;
  questions: Question[];
}

export interface AnswerSubmit {
  question_id: string;
  student_answer: string;
  time_taken_seconds?: number;
}

export interface AnswerResult {
  question_id: string;
  is_correct: boolean;
  score: number;
  correct_answer: string;
  student_answer?: string;
  explanation?: string;
}

export interface AssessmentResult {
  assessment_id: string;
  total_questions: number;
  correct_answers: number;
  score_percentage: number;
  xp_earned: number;
  answers: AnswerResult[];
}

export interface DashboardData {
  user: {
    id: string;
    username: string;
    full_name: string;
    email: string;
  };
  stats: {
    xp_total: number;
    current_streak: number;
    longest_streak: number;
    daily_goal_minutes: number;
    lessons_completed: number;
    courses_enrolled: number;
  };
  enrolled_courses: {
    id: string;
    title: string;
    total_lessons: number;
    completed_lessons: number;
    progress_pct: number;
    color: string;
  }[];
  recent_results: {
    assessment_id: string;
    lesson_title: string;
    score: number;
    xp_earned: number;
    completed_at: string;
  }[];
  weak_topics: {
    topic: string;
    subject: string;
    accuracy_rate: number;
    attempts: number;
    recommendation: string;
  }[];
  strong_topics?: {
    topic: string;
    subject: string;
    accuracy_rate: number;
    attempts: number;
    recommendation: string;
  }[];
  weekly_xp: {
    date: string;
    xp: number;
  }[];
}

export interface AIConversation {
  id: string;
  student_id: string;
  title?: string;
  context_type: string;
  context_id?: string;
  last_sequence_number: number;
  last_turn_number: number;
  created_at: string;
  updated_at: string;
}

export interface AIMessage {
  id?: string;
  conversation_id?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sequence_number?: number;
  turn_id?: string;
  created_at?: string;
  tools_used?: string[];
  status?: 'generating' | 'completed' | 'failed';
}
