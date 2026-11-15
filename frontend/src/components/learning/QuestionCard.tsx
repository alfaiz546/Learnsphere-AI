import React, { useState } from 'react';
import { Question, AnswerResult } from '../../types';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { MultipleChoiceQuestion } from './MultipleChoiceQuestion';
import { TrueFalseQuestion } from './TrueFalseQuestion';
import { NumericalQuestion } from './NumericalQuestion';
import { Lightbulb, CheckCircle2, XCircle, ArrowRight } from 'lucide-react';
import { aiService } from '../../services/ai';
import { MathMarkdown } from '../ui/MathMarkdown';
import api from '../../services/api';

interface QuestionCardProps {
  question: Question;
  lessonId: string;
  questionNumber: number;
  totalQuestions: number;
  onAnswerSubmitted: (answer: string, result: AnswerResult) => void;
  result?: AnswerResult;
  isLastQuestion?: boolean;
  onNext?: () => void;
}

export const QuestionCard: React.FC<QuestionCardProps> = ({
  question,
  lessonId,
  questionNumber,
  totalQuestions,
  onAnswerSubmitted,
  result,
  isLastQuestion,
  onNext,
}) => {
  const [selectedAnswer, setSelectedAnswer] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [hint, setHint] = useState<string | null>(question.hint || null);
  const [showHint, setShowHint] = useState<boolean>(false);
  const [loadingHint, setLoadingHint] = useState<boolean>(false);

  const isSubmitted = !!result;

  const handleSubmit = async () => {
    if (!selectedAnswer.trim()) return;
    setIsSubmitting(true);
    setSubmitError(null);

    try {
      // Always validate server-side — never trust client-side answer comparison
      const res = await api.post(`/lessons/${lessonId}/check-answer`, {
        question_id: question.id,
        student_answer: selectedAnswer.trim(),
      });

      const serverResult = res.data?.data;
      const evaluatedResult: AnswerResult = {
        question_id: question.id,
        is_correct: serverResult.is_correct,
        score: serverResult.score,
        student_answer: selectedAnswer.trim(),
        correct_answer: serverResult.correct_answer ?? serverResult.correct_answer_hint ?? '',
        explanation: serverResult.explanation,
      };

      onAnswerSubmitted(selectedAnswer, evaluatedResult);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || 'Could not validate answer. Please try again.';
      setSubmitError(detail);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRequestHint = async () => {
    if (showHint && hint) return;
    if (hint) {
      setShowHint(true);
      return;
    }
    setLoadingHint(true);
    try {
      const res = await aiService.getHint(question.id, selectedAnswer);
      if (res.data?.hint) {
        setHint(res.data.hint);
        setShowHint(true);
      }
    } catch (err) {
      setHint('Focus on the definitions and break the question into single logical steps.');
      setShowHint(true);
    } finally {
      setLoadingHint(false);
    }
  };

  return (
    <Card className="space-y-6">
      {/* Question Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <Badge variant="primary" size="sm">
            Question {questionNumber} of {totalQuestions}
          </Badge>
          <Badge variant="neutral" size="sm">
            {question.difficulty}
          </Badge>
        </div>

        <button
          onClick={handleRequestHint}
          disabled={loadingHint}
          className="flex items-center gap-1.5 text-xs font-semibold text-amber-600 dark:text-amber-400 hover:text-amber-700 transition-colors"
        >
          <Lightbulb className="w-4 h-4" />
          <span>{loadingHint ? 'Getting hint...' : showHint ? 'Hide Hint' : 'Get Hint'}</span>
        </button>
      </div>

      {/* Question Text */}
      <div className="text-base font-semibold text-slate-900 dark:text-slate-100 leading-relaxed">
        <MathMarkdown content={question.question_text} />
      </div>

      {/* Hint Panel */}
      {showHint && hint && (
        <div className="p-3.5 rounded-xl bg-amber-50/80 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/40 text-xs text-amber-900 dark:text-amber-200 flex items-start gap-2.5">
          <Lightbulb className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-semibold block mb-0.5">Hint: </span>
            <MathMarkdown content={hint} />
          </div>
        </div>
      )}

      {/* Question Answer Component */}
      <div className="py-2">
        {question.question_type === 'multiple_choice' && (
          <MultipleChoiceQuestion
            question={question}
            submitted={isSubmitted}
            isCorrect={result?.is_correct}
            selectedAnswer={selectedAnswer}
            onSelectAnswer={setSelectedAnswer}
          />
        )}

        {question.question_type === 'true_false' && (
          <TrueFalseQuestion
            question={question}
            submitted={isSubmitted}
            isCorrect={result?.is_correct}
            selectedAnswer={selectedAnswer}
            onSelectAnswer={setSelectedAnswer}
          />
        )}

        {(question.question_type === 'numerical' || question.question_type === 'fill_blank') && (
          <NumericalQuestion
            question={question}
            submitted={isSubmitted}
            isCorrect={result?.is_correct}
            selectedAnswer={selectedAnswer}
            onSelectAnswer={setSelectedAnswer}
          />
        )}
      </div>

      {/* Submission Actions & Feedback */}
      <div className="pt-2">
        {!isSubmitted ? (
          <div className="space-y-2">
            <Button
              onClick={handleSubmit}
              disabled={!selectedAnswer.trim() || isSubmitting}
              isLoading={isSubmitting}
              className="w-full sm:w-auto"
            >
              {isSubmitting ? 'Checking...' : 'Check Answer'}
            </Button>
            {submitError && (
              <p className="text-xs text-rose-600 dark:text-rose-400 font-medium">{submitError}</p>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <div
              className={`p-4 rounded-xl border flex items-start gap-3 ${
                result.is_correct
                  ? 'bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-800 text-emerald-900 dark:text-emerald-200'
                  : 'bg-rose-50 dark:bg-rose-950/30 border-rose-200 dark:border-rose-800 text-rose-900 dark:text-rose-200'
              }`}
            >
              {result.is_correct ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
              ) : (
                <XCircle className="w-5 h-5 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
              )}
              <div className="space-y-1 text-sm flex-1">
                <p className="font-semibold">
                  {result.is_correct ? 'Correct! Excellent reasoning.' : 'Incorrect answer. Review the explanation below and try the next question.'}
                </p>
                {result.correct_answer && !result.is_correct && (
                  <p className="text-xs opacity-80">
                    <span className="font-semibold">Correct answer: </span>{result.correct_answer}
                  </p>
                )}
                {result.explanation && (
                  <MathMarkdown content={result.explanation} className="text-xs opacity-90 leading-relaxed" />
                )}
              </div>
            </div>

            {onNext && (
              <div className="flex justify-end">
                <Button onClick={onNext} className="gap-2">
                  <span>{isLastQuestion ? 'Complete Lesson' : 'Next Question'}</span>
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  );
};
