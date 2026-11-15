import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { Bot, Sparkles } from 'lucide-react';

export const AuthLayout: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col justify-center items-center p-4 bg-slate-50 dark:bg-slate-950">
      <Link to="/" className="flex items-center gap-2 mb-8">
        <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-600 to-indigo-500 flex items-center justify-center text-white shadow-lg shadow-indigo-200 dark:shadow-none">
          <Bot className="w-6 h-6" />
        </div>
        <span className="font-extrabold text-2xl tracking-tight bg-gradient-to-r from-indigo-600 via-indigo-500 to-emerald-500 bg-clip-text text-transparent">
          LearnSphere AI
        </span>
      </Link>

      <div className="w-full max-w-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-8 shadow-xl shadow-slate-200/50 dark:shadow-none">
        <Outlet />
      </div>

      <div className="mt-8 flex items-center gap-2 text-xs text-slate-400">
        <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
        <span>Brilliant-inspired interactive STEM & reasoning with AI guidance</span>
      </div>
    </div>
  );
};
