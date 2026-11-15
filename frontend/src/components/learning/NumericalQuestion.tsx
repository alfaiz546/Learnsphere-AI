import React from 'react';
import { Question } from '../../types';
import { Input } from '../ui/Input';

interface NumericalProps {
  question: Question;
  submitted: boolean;
  isCorrect?: boolean;
  selectedAnswer: string;
  onSelectAnswer: (val: string) => void;
}

export const NumericalQuestion: React.FC<NumericalProps> = ({
  submitted,
  isCorrect,
  selectedAnswer,
  onSelectAnswer,
}) => {
  return (
    <div className="max-w-xs space-y-2">
      <Input
        type="number"
        step="any"
        placeholder="Enter your numerical answer..."
        value={selectedAnswer}
        disabled={submitted}
        onChange={(e) => onSelectAnswer(e.target.value)}
        className="text-lg font-semibold tracking-wide"
      />
      {submitted && (
        <p className={`text-xs font-medium ${isCorrect ? 'text-emerald-600' : 'text-rose-600'}`}>
          {isCorrect ? '✓ Numerical answer confirmed' : '✗ Incorrect numerical answer'}
        </p>
      )}
    </div>
  );
};
