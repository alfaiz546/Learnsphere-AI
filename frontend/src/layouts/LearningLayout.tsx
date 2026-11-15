import React from 'react';
import { Outlet, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Bot, Award } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export const LearningLayout: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col">
      {/* Top bar */}
      <header className="h-14 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-6 flex items-center justify-between sticky top-0 z-20">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(-1)}
            className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <Link to="/dashboard" className="font-bold text-sm tracking-tight text-indigo-600 dark:text-indigo-400">
            LearnSphere AI
          </Link>
        </div>

        <div className="flex items-center gap-3">
          {user?.profile && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 text-xs font-semibold">
              <Award className="w-3.5 h-3.5" />
              <span>{user.profile.xp_total} XP</span>
            </div>
          )}
        </div>
      </header>

      {/* Main interactive area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 flex flex-col">
        <Outlet />
      </main>
    </div>
  );
};
