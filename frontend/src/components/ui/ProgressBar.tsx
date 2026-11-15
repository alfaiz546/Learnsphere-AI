import React from 'react';
import clsx from 'clsx';

interface ProgressBarProps {
  progress: number;
  max?: number;
  className?: string;
  showLabel?: boolean;
  color?: 'primary' | 'secondary' | 'accent';
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  max = 100,
  className,
  showLabel = false,
  color = 'primary',
}) => {
  const percentage = Math.min(100, Math.max(0, Math.round((progress / max) * 100)));

  const colorStyles = {
    primary: 'bg-indigo-600',
    secondary: 'bg-emerald-500',
    accent: 'bg-amber-500',
  };

  return (
    <div className={clsx('w-full', className)}>
      {showLabel && (
        <div className="flex justify-between items-center text-xs font-medium text-slate-500 dark:text-slate-400 mb-1.5">
          <span>Progress</span>
          <span>{percentage}%</span>
        </div>
      )}
      <div className="w-full h-2.5 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
        <div
          className={clsx('h-full transition-all duration-300 rounded-full', colorStyles[color])}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};
