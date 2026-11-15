import React from 'react';
import clsx from 'clsx';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  hoverEffect?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  hoverEffect = false,
  className,
  ...props
}) => {
  return (
    <div
      className={clsx(
        'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700/60 rounded-2xl p-6 shadow-sm',
        hoverEffect && 'transition-all duration-200 hover:shadow-md hover:border-indigo-300 dark:hover:border-slate-600',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};
