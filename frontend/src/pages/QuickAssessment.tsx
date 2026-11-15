import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { ProgressBar } from '../components/ui/ProgressBar';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { MathMarkdown } from '../components/ui/MathMarkdown';
import { Alert } from '../components/ui/Alert';
import {
  CheckCircle2,
  XCircle,
  HelpCircle,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  Award,
  TrendingUp,
  RotateCcw,
  BookOpen,
  CalendarDays,
  Bot,
  Zap,
} from 'lucide-react';

interface QuestionOption {
  id: string;
  option_text: string;
  label: string;
  letter: string;
  display_order: number;
}

interface DiagnosticQuestion {
  id: string;
  subject_name: string;
  question_text: string;
  question_type: string;
  difficulty: string;
  hint?: string;
  tags: string[];
  options: QuestionOption[];
}

export const QuickAssessment: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [assessmentId, setAssessmentId] = useState<string>('');
  const [questions, setQuestions] = useState<DiagnosticQuestion[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [showHint, setShowHint] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [startTime] = useState<number>(Date.now());

  const fetchAssessment = async () => {
    try {
      setLoading(true);
      setError(null);
      setResult(null);
      setAnswers({});
      setCurrentIndex(0);
      setShowHint(false);

      const res = await api.get('/assessments/diagnostic');
      if (res.data?.success && res.data?.data) {
        setAssessmentId(res.data.data.assessment_id);
        setQuestions(res.data.data.questions || []);
      } else {
        setError('Failed to initialize diagnostic assessment.');
      }
    } catch (err: any) {
      console.error('Error fetching diagnostic assessment:', err);
      setError(err?.response?.data?.detail || 'Failed to load assessment. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssessment();
  }, []);

  const handleSelectAnswer = (questionId: string, answer: string) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: answer,
    }));
  };

  const currentQ = questions[currentIndex];
  const totalQuestions = questions.length;
  const answeredCount = Object.keys(answers).length;
  const progressPct = totalQuestions > 0 ? Math.round(((currentIndex + 1) / totalQuestions) * 100) : 0;

  const handleSubmit = async () => {
    if (!assessmentId) return;
    try {
      setIsSubmitting(true);
      const elapsedSeconds = Math.max(1, Math.round((Date.now() - startTime) / 1000));
      const perQuestionTime = Math.max(1, Math.round(elapsedSeconds / Math.max(1, totalQuestions)));

      const formattedAnswers = questions.map((q) => ({
        question_id: q.id,
        student_answer: answers[q.id] || '',
        time_taken_seconds: perQuestionTime,
      }));

      const res = await api.post('/assessments/submit', {
        assessment_id: assessmentId,
        answers: formattedAnswers,
      });

      if (res.data?.success) {
        setResult(res.data.data);
      }
    } catch (err: any) {
      console.error('Error submitting assessment:', err);
      setError(err?.response?.data?.detail || 'Failed to submit assessment.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col h-96 items-center justify-center space-y-4">
        <LoadingSpinner size="lg" />
        <p className="text-sm text-slate-500 font-medium">Preparing diagnostic assessment questions...</p>
      </div>
    );
  }

  if (error && !result) {
    return (
      <div className="max-w-2xl mx-auto p-6 space-y-4">
        <Alert type="error" title="Assessment Error">
          {error}
        </Alert>
        <Button onClick={fetchAssessment} className="gap-2">
          <RotateCcw className="w-4 h-4" />
          <span>Try Again</span>
        </Button>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Results View
  // ---------------------------------------------------------------------------
  if (result) {
    const isPassing = (result.score_percentage || 0) >= 60;
    return (
      <div className="max-w-3xl mx-auto space-y-8 py-4">
        <Card className="p-8 text-center space-y-6 bg-gradient-to-b from-white to-slate-50 dark:from-slate-900 dark:to-slate-950 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="w-16 h-16 mx-auto rounded-3xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center shadow-inner">
            <Award className="w-8 h-8" />
          </div>

          <div className="space-y-2">
            <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 dark:text-white">
              Diagnostic Assessment Complete! 🎉
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 max-w-lg mx-auto">
              Your answers have been analyzed across topics. Your academic profile and weak/strong topics have been updated.
            </p>
          </div>

          {/* Score & XP Banner */}
          <div className="grid grid-cols-3 gap-4 max-w-md mx-auto pt-2">
            <div className="p-4 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700/80">
              <div className="text-xs text-slate-500 font-medium mb-1">Score</div>
              <div className={`text-2xl font-black ${isPassing ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'}`}>
                {Math.round(result.score_percentage || 0)}%
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700/80">
              <div className="text-xs text-slate-500 font-medium mb-1">Correct</div>
              <div className="text-2xl font-black text-slate-800 dark:text-slate-200">
                {result.correct_answers} / {result.total_questions}
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700/80">
              <div className="text-xs text-slate-500 font-medium mb-1">XP Earned</div>
              <div className="text-2xl font-black text-indigo-600 dark:text-indigo-400">
                +{result.xp_earned}
              </div>
            </div>
          </div>

          {/* Action Navigation Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
            <Button
              onClick={() => navigate('/progress')}
              className="w-full sm:w-auto gap-2 bg-indigo-600 hover:bg-indigo-700 text-white"
            >
              <TrendingUp className="w-4 h-4" />
              <span>View Strong & Weak Topics</span>
            </Button>

            <Button
              variant="outline"
              onClick={() => navigate('/study-plan')}
              className="w-full sm:w-auto gap-2"
            >
              <CalendarDays className="w-4 h-4" />
              <span>Generate Study Plan</span>
            </Button>

            <Button
              variant="outline"
              onClick={() => navigate('/ai-tutor')}
              className="w-full sm:w-auto gap-2"
            >
              <Bot className="w-4 h-4" />
              <span>Ask AI Mentor</span>
            </Button>
          </div>
        </Card>

        {/* Question Solutions Breakdown */}
        <div className="space-y-4">
          <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-indigo-600" />
            <span>Question Breakdown & Explanations</span>
          </h2>

          <div className="space-y-3">
            {result.answers?.map((ans: any, idx: number) => {
              const q = questions.find((item) => item.id === ans.question_id);
              return (
                <Card
                  key={idx}
                  className={`p-5 border-l-4 ${
                    ans.is_correct
                      ? 'border-l-emerald-500 bg-emerald-50/20 dark:bg-emerald-950/10'
                      : 'border-l-rose-500 bg-rose-50/20 dark:bg-rose-950/10'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-xs text-slate-500">Q{idx + 1}.</span>
                      {ans.is_correct ? (
                        <Badge variant="success" size="sm" className="gap-1">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>Correct</span>
                        </Badge>
                      ) : (
                        <Badge variant="danger" size="sm" className="gap-1">
                          <XCircle className="w-3 h-3" />
                          <span>Incorrect</span>
                        </Badge>
                      )}
                      {q?.subject_name && (
                        <Badge variant="neutral" size="sm">
                          {q.subject_name}
                        </Badge>
                      )}
                    </div>
                  </div>

                  <div className="text-sm font-medium text-slate-900 dark:text-white mb-3">
                    {q ? <MathMarkdown content={q.question_text} /> : `Question ${idx + 1}`}
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs mb-3">
                    <div className="p-2.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                      <span className="text-slate-400 block mb-0.5">Your Answer:</span>
                      <span className={ans.is_correct ? 'font-bold text-emerald-600' : 'font-bold text-rose-600'}>
                        {answers[ans.question_id] || '(No answer provided)'}
                      </span>
                    </div>

                    <div className="p-2.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                      <span className="text-slate-400 block mb-0.5">Correct Answer:</span>
                      <span className="font-bold text-emerald-600">
                        {ans.correct_answer}
                      </span>
                    </div>
                  </div>

                  {ans.explanation && (
                    <div className="p-3 rounded-lg bg-slate-100 dark:bg-slate-800 text-xs text-slate-600 dark:text-slate-300">
                      <span className="font-semibold block mb-1 text-slate-800 dark:text-slate-200">Explanation:</span>
                      <MathMarkdown content={ans.explanation} />
                    </div>
                  )}
                </Card>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Active Assessment View
  // ---------------------------------------------------------------------------
  if (!currentQ) {
    return (
      <div className="max-w-xl mx-auto p-8 text-center space-y-4">
        <p className="text-slate-500">No questions available in diagnostic test.</p>
        <Button onClick={fetchAssessment}>Reload</Button>
      </div>
    );
  }

  const currentAnswer = answers[currentQ.id] || '';

  return (
    <div className="max-w-3xl mx-auto space-y-6 py-4">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-indigo-50 dark:bg-indigo-950 text-indigo-600 flex items-center justify-center">
              <Zap className="w-4 h-4" />
            </div>
            <h1 className="text-xl md:text-2xl font-extrabold text-slate-900 dark:text-white">
              Quick Skill Assessment
            </h1>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Diagnostic test across Math, Science, Python, and Logic to identify your mastery profile.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Badge variant="primary" size="sm" className="font-semibold">
            {answeredCount} / {totalQuestions} Answered
          </Badge>
        </div>
      </div>

      {/* Progress Bar & Stepper */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs text-slate-500 font-medium">
          <span>Question {currentIndex + 1} of {totalQuestions}</span>
          <span>{progressPct}% Completed</span>
        </div>
        <ProgressBar progress={progressPct} color="primary" />
      </div>

      {/* Question Card */}
      <Card className="p-6 md:p-8 space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Badge variant="primary" size="sm">
              {currentQ.subject_name}
            </Badge>
            <Badge variant="neutral" size="sm" className="capitalize">
              {currentQ.difficulty}
            </Badge>
            {currentQ.tags?.slice(0, 2).map((t, i) => (
              <Badge key={i} variant="neutral" size="sm">
                {t}
              </Badge>
            ))}
          </div>

          {currentQ.hint && (
            <button
              onClick={() => setShowHint(!showHint)}
              className="text-xs text-amber-600 dark:text-amber-400 font-medium flex items-center gap-1 hover:underline"
            >
              <HelpCircle className="w-3.5 h-3.5" />
              <span>{showHint ? 'Hide Hint' : 'Need Hint?'}</span>
            </button>
          )}
        </div>

        {/* Hint Box */}
        {showHint && currentQ.hint && (
          <div className="p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60 text-xs text-amber-800 dark:text-amber-300">
            <span className="font-bold">Hint: </span>
            {currentQ.hint}
          </div>
        )}

        {/* Question Text */}
        <div className="text-base md:text-lg font-semibold text-slate-900 dark:text-slate-100 leading-relaxed">
          <MathMarkdown content={currentQ.question_text} />
        </div>

        {/* Options / Input Form */}
        <div className="pt-2">
          {currentQ.question_type === 'multiple_choice' && (
            <div className="space-y-3">
              {currentQ.options.map((opt) => {
                const isSelected =
                  currentAnswer === opt.letter ||
                  currentAnswer === opt.option_text ||
                  currentAnswer === opt.label.toLowerCase();
                return (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => handleSelectAnswer(currentQ.id, opt.letter)}
                    className={`w-full text-left p-4 rounded-xl border transition-all flex items-center gap-3.5 ${
                      isSelected
                        ? 'border-indigo-600 bg-indigo-50/80 dark:bg-indigo-950/60 text-indigo-900 dark:text-indigo-200 shadow-sm'
                        : 'border-slate-200 dark:border-slate-700/80 hover:bg-slate-50 dark:hover:bg-slate-800/50 text-slate-800 dark:text-slate-200'
                    }`}
                  >
                    <span
                      className={`w-7 h-7 rounded-lg text-xs font-bold flex items-center justify-center shrink-0 ${
                        isSelected
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300'
                      }`}
                    >
                      {opt.label}
                    </span>
                    <span className="text-sm font-medium flex-1">
                      <MathMarkdown content={opt.option_text} inline />
                    </span>
                  </button>
                );
              })}
            </div>
          )}

          {currentQ.question_type === 'true_false' && (
            <div className="grid grid-cols-2 gap-4">
              {['true', 'false'].map((val) => {
                const isSelected = currentAnswer.toLowerCase() === val;
                return (
                  <button
                    key={val}
                    type="button"
                    onClick={() => handleSelectAnswer(currentQ.id, val)}
                    className={`p-4 rounded-xl border text-center font-bold text-sm transition-all capitalize ${
                      isSelected
                        ? 'border-indigo-600 bg-indigo-50/80 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 shadow-sm'
                        : 'border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300'
                    }`}
                  >
                    {val}
                  </button>
                );
              })}
            </div>
          )}

          {(currentQ.question_type === 'numerical' || currentQ.question_type === 'fill_blank') && (
            <div className="space-y-3">
              <label className="block text-xs font-medium text-slate-600 dark:text-slate-400">
                Type your answer below:
              </label>
              <input
                type={currentQ.question_type === 'numerical' ? 'text' : 'text'}
                value={currentAnswer}
                onChange={(e) => handleSelectAnswer(currentQ.id, e.target.value)}
                placeholder="e.g. 4, 37, 20"
                className="w-full px-4 py-3 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium text-sm"
              />
            </div>
          )}
        </div>

        {/* Navigation Buttons */}
        <div className="flex items-center justify-between pt-6 border-t border-slate-100 dark:border-slate-800">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setShowHint(false);
              setCurrentIndex((prev) => Math.max(0, prev - 1));
            }}
            disabled={currentIndex === 0}
            className="gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Previous</span>
          </Button>

          {currentIndex < totalQuestions - 1 ? (
            <Button
              size="sm"
              onClick={() => {
                setShowHint(false);
                setCurrentIndex((prev) => Math.min(totalQuestions - 1, prev + 1));
              }}
              className="gap-2"
            >
              <span>Next</span>
              <ArrowRight className="w-4 h-4" />
            </Button>
          ) : (
            <Button
              size="sm"
              onClick={handleSubmit}
              isLoading={isSubmitting}
              className="gap-2 bg-emerald-600 hover:bg-emerald-700 text-white"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Submit Assessment</span>
            </Button>
          )}
        </div>
      </Card>
    </div>
  );
};
