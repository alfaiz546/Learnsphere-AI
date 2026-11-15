import React, { useState } from 'react';
import { Question } from '../../types';
import clsx from 'clsx';
import { CheckCircle2, XCircle } from 'lucide-react';
import { MathMarkdown } from '../ui/MathMarkdown';

interface MultipleChoiceProps {
  question: Question;
  submitted: boolean;
  isCorrect?: boolean;
  selectedAnswer: string;
  onSelectAnswer: (val: string) => void;
}

export const MultipleChoiceQuestion: React.FC<MultipleChoiceProps> = ({
  question,
  submitted,
  isCorrect,
  selectedAnswer,
  onSelectAnswer,
}) => {
  const letters = ['a', 'b', 'c', 'd', 'e'];

  return (
    <div className="space-y-3">
      {question.options.map((option, idx) => {
        const optionKey = letters[idx] || String(idx);
        const isSelected = selectedAnswer.toLowerCase() === optionKey.toLowerCase();

        return (
          <button
            key={option.id}
            type="button"
            disabled={submitted}
            onClick={() => onSelectAnswer(optionKey)}
            className={clsx(
              'w-full flex items-center justify-between p-4 rounded-xl border text-left transition-all duration-150',
              !submitted && isSelected && 'border-indigo-600 bg-indigo-50/50 dark:bg-indigo-950/30 text-indigo-950 dark:text-indigo-200 ring-2 ring-indigo-500/30',
              !submitted && !isSelected && 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:border-slate-300 dark:hover:border-slate-600 text-slate-800 dark:text-slate-200',
              submitted && isSelected && isCorrect && 'border-emerald-500 bg-emerald-50 dark:bg-emerald-950/30 text-emerald-900 dark:text-emerald-200',
              submitted && isSelected && !isCorrect && 'border-rose-500 bg-rose-50 dark:bg-rose-950/30 text-rose-900 dark:text-rose-200',
              submitted && !isSelected && 'opacity-60 border-slate-200 dark:border-slate-700'
            )}
          >
            <div className="flex items-center gap-3">
              <span
                className={clsx(
                  'w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs uppercase transition-colors',
                  isSelected
                    ? 'bg-indigo-600 text-white dark:bg-indigo-500'
                    : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300'
                )}
              >
                {optionKey}
              </span>
              <span className="text-sm font-medium">
                <MathMarkdown content={option.option_text} inline />
              </span>
            </div>

            {submitted && isSelected && (
              <div>
                {isCorrect ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                ) : (
                  <XCircle className="w-5 h-5 text-rose-600 dark:text-rose-400" />
                )}
              </div>
            )}
          </button>
        );
      })}
    </div>
  );
};
