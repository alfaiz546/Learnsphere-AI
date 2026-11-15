import React from 'react';
import { AIMessage } from '../../types';
import { Bot, User, Wrench } from 'lucide-react';
import clsx from 'clsx';
import { MathMarkdown } from '../ui/MathMarkdown';

export const ChatMessage: React.FC<{ message: AIMessage }> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div
      className={clsx(
        'flex gap-3 text-sm leading-relaxed',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      <div
        className={clsx(
          'w-8 h-8 rounded-xl flex items-center justify-center shrink-0 text-white font-bold text-xs',
          isUser
            ? 'bg-slate-700 dark:bg-slate-600'
            : 'bg-gradient-to-tr from-indigo-600 to-indigo-500 shadow-sm'
        )}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      <div
        className={clsx(
          'max-w-[85%] rounded-2xl px-4 py-3 space-y-2',
          isUser
            ? 'bg-indigo-600 text-white'
            : 'bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700 text-slate-900 dark:text-slate-100'
        )}
      >
        <MathMarkdown content={message.content} />

        {message.tools_used && message.tools_used.length > 0 && (
          <div className="pt-2 border-t border-slate-100 dark:border-slate-700 flex flex-wrap gap-1.5 items-center">
            <span className="text-[10px] text-slate-400 dark:text-slate-500 flex items-center gap-1 font-medium">
              <Wrench className="w-3 h-3" /> Tools called:
            </span>
            {message.tools_used.map((t, idx) => (
              <span
                key={idx}
                className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 border border-indigo-200/60 dark:border-indigo-800"
              >
                {t}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
