import React from 'react';
import { Question } from '../../types';
import clsx from 'clsx';
import { CheckCircle2, XCircle } from 'lucide-react';

interface TrueFalseProps {
  question: Question;
  submitted: boolean;
  isCorrect?: boolean;
  selectedAnswer: string;
  onSelectAnswer: (val: string) => void;
}

export const TrueFalseQuestion: React.FC<TrueFalseProps> = ({
  submitted,
  isCorrect,
  selectedAnswer,
  onSelectAnswer,
}) => {
  const options = [
    { label: 'True', val: 'true' },
    { label: 'False', val: 'false' },
  ];

  return (
    <div className="grid grid-cols-2 gap-4">
      {options.map((opt) => {
        const isSelected = selectedAnswer.toLowerCase() === opt.val.toLowerCase();

        return (
          <button
            key={opt.val}
            type="button"
            disabled={submitted}
            onClick={() => onSelectAnswer(opt.val)}
            className={clsx(
              'flex flex-col items-center justify-center py-6 px-4 rounded-2xl border text-center font-semibold text-base transition-all duration-150',
              !submitted && isSelected && 'border-indigo-600 bg-indigo-50/50 dark:bg-indigo-950/30 text-indigo-700 dark:text-indigo-300 ring-2 ring-indigo-500/30',
              !submitted && !isSelected && 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:border-slate-300 text-slate-800 dark:text-slate-200',
              submitted && isSelected && isCorrect && 'border-emerald-500 bg-emerald-50 text-emerald-800',
              submitted && isSelected && !isCorrect && 'border-rose-500 bg-rose-50 text-rose-800',
              submitted && !isSelected && 'opacity-60 border-slate-200'
            )}
          >
            <span>{opt.label}</span>
            {submitted && isSelected && (
              <span className="mt-2">
                {isCorrect ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                ) : (
                  <XCircle className="w-5 h-5 text-rose-600" />
                )}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};
