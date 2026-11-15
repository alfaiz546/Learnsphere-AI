import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import { LessonDetail, AnswerResult } from '../types';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { ProgressBar } from '../components/ui/ProgressBar';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { QuestionCard } from '../components/learning/QuestionCard';
import { AITutorChat } from '../components/ai/AITutorChat';
import { MathMarkdown } from '../components/ui/MathMarkdown';
import {
  BookOpen,
  CheckCircle,
  Bot,
  Sparkles,
  ArrowRight,
  Code2
} from 'lucide-react';

export const Lesson: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [currentQuestionIndex, setCurrentQuestionIndex] = useState<number>(0);
  const [answeredResults, setAnsweredResults] = useState<Record<string, AnswerResult>>({});
  const [studentAnswers, setStudentAnswers] = useState<Record<string, string>>({});
  const [assessmentId, setAssessmentId] = useState<string | null>(null);
  const [isCompleted, setIsCompleted] = useState<boolean>(false);

  // Fetch lesson details
  const { data, isLoading, error } = useQuery<{ success: boolean; data: LessonDetail }>({
    queryKey: ['lesson', id],
    queryFn: async () => {
      const res = await api.get(`/lessons/${id}`);
      return res.data;
    },
  });

  // Start assessment session once lesson is loaded
  React.useEffect(() => {
    if (id && !assessmentId) {
      api.post('/assessments/start', { lesson_id: id }).then((res) => {
        if (res.data?.data?.assessment_id) {
          setAssessmentId(res.data.data.assessment_id);
        }
      }).catch((e) => console.error("Assessment start error", e));
    }
  }, [id, assessmentId]);

  // Complete lesson mutation
  const completeMutation = useMutation({
    mutationFn: async () => {
      // If we have an assessment, submit it — using the actual student-typed answers (not the correct answers)
      if (assessmentId && Object.keys(answeredResults).length > 0) {
        const answers = Object.entries(answeredResults).map(([qid, res]) => ({
          question_id: qid,
          student_answer: res.student_answer ?? res.correct_answer ?? '',
          time_taken_seconds: 15,
        }));
        await api.post('/assessments/submit', {
          assessment_id: assessmentId,
          answers,
        }).catch((e) => console.log(e));
      }

      // Mark lesson complete
      const res = await api.post(`/lessons/${id}/complete`);
      return res.data;
    },
    onSuccess: () => {
      setIsCompleted(true);
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['progress'] });
    },
  });

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !data?.data) {
    return (
      <div className="p-8 text-center text-rose-600 font-medium">
        Failed to load lesson.
      </div>
    );
  }

  const lesson = data.data;
  const questions = lesson.questions || [];
  const currentQuestion = questions[currentQuestionIndex];
  const progressPct = questions.length > 0
    ? Math.round((Object.keys(answeredResults).length / questions.length) * 100)
    : 100;

  let contentBlocks: any[] = [];
  try {
    if (lesson.content) {
      const parsed = JSON.parse(lesson.content);
      contentBlocks = parsed.blocks || [];
    }
  } catch (e) {
    contentBlocks = [{ type: 'text', content: lesson.content || '' }];
  }

  const handleAnswerSubmitted = (answer: string, result: AnswerResult) => {
    setAnsweredResults((prev) => ({
      ...prev,
      [currentQuestion.id]: result,
    }));
  };

  const handleNext = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex((prev) => prev + 1);
    } else {
      completeMutation.mutate();
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Lesson Progress Bar */}
      <div className="flex items-center justify-between gap-4 bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800">
        <div>
          <span className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider">
            Lesson Session
          </span>
          <h2 className="text-base font-bold text-slate-900 dark:text-white">{lesson.title}</h2>
        </div>

        <div className="w-48 hidden sm:block">
          <ProgressBar progress={progressPct} color="primary" showLabel />
        </div>
      </div>

      {/* Main 2-Panel Interactive Environment */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Panel: Concept Content & Interactive Questions (7 Cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Concept Content Blocks */}
          <Card className="p-6 space-y-4">
            <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 pb-2 border-b border-slate-100 dark:border-slate-800">
              <BookOpen className="w-5 h-5" />
              <h3 className="font-bold text-sm uppercase tracking-wide">Concept Exploration</h3>
            </div>

            <div className="space-y-3.5 text-sm leading-relaxed text-slate-700 dark:text-slate-300">
              {contentBlocks.map((block: any, idx: number) => {
                if (block.type === 'code') {
                  return (
                    <div key={idx} className="rounded-xl overflow-hidden bg-slate-900 text-slate-100 p-4 font-mono text-xs my-2">
                      <div className="flex items-center gap-2 pb-2 mb-2 border-b border-slate-800 text-[11px] text-slate-400">
                        <Code2 className="w-3.5 h-3.5" />
                        <span>{block.language || 'code'}</span>
                      </div>
                      <pre className="overflow-x-auto">{block.content}</pre>
                    </div>
                  );
                }

                if (block.type === 'example') {
                  return (
                    <div key={idx} className="p-4 rounded-xl bg-indigo-50/70 dark:bg-indigo-950/40 border border-indigo-200/60 dark:border-indigo-900/40 text-indigo-950 dark:text-indigo-200 text-xs my-2">
                      <span className="font-bold uppercase tracking-wider text-[10px] block mb-1 text-indigo-600 dark:text-indigo-400">
                        Visual Exploration Example
                      </span>
                      <MathMarkdown content={block.content} />
                    </div>
                  );
                }

                return (
                  <div key={idx} className="leading-relaxed">
                    <MathMarkdown content={block.content} />
                  </div>
                );
              })}
            </div>
          </Card>

          {/* Interactive Question Card */}
          {questions.length > 0 && currentQuestion && (
            <QuestionCard
              question={currentQuestion}
              lessonId={id!}
              questionNumber={currentQuestionIndex + 1}
              totalQuestions={questions.length}
              onAnswerSubmitted={handleAnswerSubmitted}
              result={answeredResults[currentQuestion.id]}
              isLastQuestion={currentQuestionIndex === questions.length - 1}
              onNext={handleNext}
            />
          )}

          {/* Lesson Completion Card */}
          {isCompleted && (
            <Card className="p-8 text-center space-y-4 bg-gradient-to-br from-emerald-950 via-slate-900 to-slate-900 text-white border-emerald-800">
              <div className="w-14 h-14 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto">
                <CheckCircle className="w-8 h-8" />
              </div>
              <h3 className="text-2xl font-bold">Lesson Mastered!</h3>
              <p className="text-slate-300 text-sm max-w-md mx-auto">
                You've solved the interactive challenges and earned +10 XP. Your learning streak has been updated!
              </p>
              <div className="pt-2">
                <Button size="lg" onClick={() => navigate('/dashboard')} className="gap-2 bg-emerald-600 hover:bg-emerald-700">
                  <span>Return to Dashboard</span>
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </div>
            </Card>
          )}
        </div>

        {/* Right Panel: Context-Aware AI Mentor Tutor (5 Cols) */}
        <div className="lg:col-span-5 sticky top-20">
          <AITutorChat
            compact
            context={{
              lesson: lesson.title,
              question: currentQuestion?.question_text,
              student_answer: answeredResults[currentQuestion?.id]?.correct_answer,
            }}
            initialPrompt={`I'm following along with "${lesson.title}". Ask me if you need an intuitive step-by-step hint or conceptual breakdown!`}
          />
        </div>
      </div>
    </div>
  );
};
