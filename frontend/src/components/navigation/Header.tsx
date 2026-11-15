import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Award, Flame, User as UserIcon } from 'lucide-react';
import { Badge } from '../ui/Badge';

interface HeaderProps {
  title?: string;
  subtitle?: string;
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle }) => {
  const { user } = useAuth();

  return (
    <header className="h-16 border-b border-slate-200/80 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md sticky top-0 z-20 flex items-center justify-between px-8">
      <div>
        {title && <h1 className="text-lg font-bold text-slate-900 dark:text-slate-100">{title}</h1>}
        {subtitle && <p className="text-xs text-slate-500 dark:text-slate-400">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-4">
        {user?.profile && (
          <div className="hidden sm:flex items-center gap-2">
            <Badge variant="accent" size="md">
              <Flame className="w-3.5 h-3.5" />
              <span>{user.profile.current_streak} Day Streak</span>
            </Badge>

            <Badge variant="secondary" size="md">
              <Award className="w-3.5 h-3.5" />
              <span>{user.profile.xp_total} XP</span>
            </Badge>
          </div>
        )}

        <div className="flex items-center gap-2.5 pl-2">
          <div className="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 flex items-center justify-center font-bold text-xs uppercase border border-indigo-200 dark:border-indigo-800">
            {user?.username ? user.username.slice(0, 2) : <UserIcon className="w-4 h-4" />}
          </div>
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300 hidden md:inline">
            {user?.full_name || user?.username}
          </span>
        </div>
      </div>
    </header>
  );
};
