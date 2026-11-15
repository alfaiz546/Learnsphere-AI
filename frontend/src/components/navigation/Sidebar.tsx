import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Compass,
  Bot,
  TrendingUp,
  CalendarDays,
  User,
  ShieldAlert,
  LogOut,
  Moon,
  Sun,
  Flame,
  Award,
  Zap,
  GraduationCap
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';

export const Sidebar: React.FC = () => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Skill Assessment', path: '/quick-assessment', icon: Zap },
    { name: 'Explore Subjects', path: '/subjects', icon: Compass },
    { name: 'AI Mentor', path: '/ai-tutor', icon: Bot },
    { name: 'My Progress', path: '/progress', icon: TrendingUp },
    { name: 'College Simulator', path: '/simulator', icon: GraduationCap },
    { name: 'Study Plan', path: '/study-plan', icon: CalendarDays },
    { name: 'Profile', path: '/profile', icon: User },
  ];

  if (user?.role === 'admin') {
    navItems.push({ name: 'Admin CMS', path: '/admin', icon: ShieldAlert });
  }

  return (
    <aside className="w-64 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col h-screen sticky top-0 shrink-0">
      {/* Brand */}
      <div className="p-6 border-b border-slate-100 dark:border-slate-800/80 flex items-center justify-between">
        <NavLink to="/dashboard" className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-500 flex items-center justify-center text-white shadow-md shadow-indigo-200 dark:shadow-none">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <span className="font-bold text-base tracking-tight bg-gradient-to-r from-indigo-600 via-indigo-500 to-emerald-500 bg-clip-text text-transparent">
              LearnSphere
            </span>
            <span className="text-xs font-semibold uppercase tracking-wider text-indigo-600 dark:text-indigo-400 ml-1">
              AI
            </span>
          </div>
        </NavLink>
      </div>

      {/* Navigation links */}
      <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 font-semibold shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-200'
              }`
            }
          >
            <item.icon className="w-4 h-4 shrink-0" />
            <span>{item.name}</span>
          </NavLink>
        ))}
      </nav>

      {/* User stats widget in sidebar */}
      {user?.profile && (
        <div className="px-4 py-3 mx-4 mb-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-700/60 flex items-center justify-around text-xs">
          <div className="flex items-center gap-1.5 text-amber-600 dark:text-amber-400 font-medium">
            <Flame className="w-4 h-4" />
            <span>{user.profile.current_streak}d streak</span>
          </div>
          <div className="h-4 w-px bg-slate-200 dark:bg-slate-700"></div>
          <div className="flex items-center gap-1.5 text-indigo-600 dark:text-indigo-400 font-medium">
            <Award className="w-4 h-4" />
            <span>{user.profile.xp_total} XP</span>
          </div>
        </div>
      )}

      {/* Footer / User Profile & Logout */}
      <div className="p-4 border-t border-slate-100 dark:border-slate-800/80 space-y-2">
        <div className="flex items-center justify-between">
          <button
            onClick={toggleTheme}
            className="p-2 rounded-xl text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            title="Toggle theme"
          >
            {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>

          <button
            onClick={logout}
            className="flex items-center gap-2 px-3 py-1.5 text-xs text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded-xl transition-colors font-medium"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>
    </aside>
  );
};
