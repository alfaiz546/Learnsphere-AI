import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { authService } from '../services/auth';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Badge } from '../components/ui/Badge';
import { Alert } from '../components/ui/Alert';
import { User, Award, Flame, Target, Shield, Check, GraduationCap, Compass, BookOpen } from 'lucide-react';

export const Profile: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [dailyGoal, setDailyGoal] = useState<number>(user?.profile?.daily_goal_minutes || 30);
  const [currentClass, setCurrentClass] = useState<string>(user?.profile?.current_class || 'Class 12');
  const [board, setBoard] = useState<string>(user?.profile?.board || 'CBSE');
  const [currentMarks, setCurrentMarks] = useState<number>(user?.profile?.current_marks || 85);
  const [targetExam, setTargetExam] = useState<string>(user?.profile?.target_exam || 'JEE Main');
  const [careerGoal, setCareerGoal] = useState<string>(user?.profile?.career_goal || 'Computer Science & AI');
  const [targetYear, setTargetYear] = useState<number>(user?.profile?.target_year || 2025);
  const [category, setCategory] = useState<string>(user?.profile?.category || 'General');

  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      setFullName(user.full_name || '');
      if (user.profile) {
        setDailyGoal(user.profile.daily_goal_minutes || 30);
        setCurrentClass(user.profile.current_class || 'Class 12');
        setBoard(user.profile.board || 'CBSE');
        setCurrentMarks(user.profile.current_marks ?? 85);
        setTargetExam(user.profile.target_exam || 'JEE Main');
        setCareerGoal(user.profile.career_goal || 'Computer Science & AI');
        setTargetYear(user.profile.target_year || 2025);
        setCategory(user.profile.category || 'General');
      }
    }
  }, [user]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage(null);
    try {
      await authService.updateProfile({
        full_name: fullName,
        daily_goal_minutes: dailyGoal,
        current_class: currentClass,
        board: board,
        current_marks: currentMarks,
        target_exam: targetExam,
        career_goal: careerGoal,
        target_year: targetYear,
        category: category,
      });
      await refreshUser();
      setMessage('Profile and academic preferences updated successfully!');
    } catch (err: any) {
      setMessage('Failed to update profile.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 dark:text-white">
          Student Academic Profile
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Manage your academic credentials, target exam milestones, and career ambitions.
        </p>
      </div>

      {message && (
        <Alert type={message.includes('success') ? 'success' : 'error'}>
          {message}
        </Alert>
      )}

      {/* User Info Overview */}
      <Card className="p-6 flex flex-col sm:flex-row items-center gap-6">
        <div className="w-20 h-20 rounded-3xl bg-indigo-600 text-white flex items-center justify-center font-bold text-2xl uppercase shadow-lg shadow-indigo-200 dark:shadow-none shrink-0">
          {user?.username ? user.username.slice(0, 2) : <User className="w-10 h-10" />}
        </div>

        <div className="space-y-1.5 text-center sm:text-left flex-1">
          <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">
              {user?.full_name || user?.username}
            </h2>
            <Badge variant="primary" size="sm">
              {user?.profile?.current_class || 'Class 12'}
            </Badge>
            <Badge variant="neutral" size="sm">
              {user?.profile?.target_exam || 'JEE Main'}
            </Badge>
          </div>
          <p className="text-xs text-slate-500">{user?.email} • @{user?.username}</p>
          {user?.profile?.career_goal && (
            <p className="text-xs text-indigo-600 dark:text-indigo-400 font-semibold flex items-center justify-center sm:justify-start gap-1">
              <Compass className="w-3.5 h-3.5" />
              <span>Goal: {user.profile.career_goal}</span>
            </p>
          )}
        </div>

        <div className="flex items-center gap-4 text-center">
          <div className="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/80 border border-slate-100 dark:border-slate-700/60 min-w-20">
            <div className="text-lg font-bold text-indigo-600">{user?.profile?.xp_total || 0}</div>
            <div className="text-[10px] text-slate-400 uppercase font-bold">XP</div>
          </div>
          <div className="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/80 border border-slate-100 dark:border-slate-700/60 min-w-20">
            <div className="text-lg font-bold text-amber-600">{user?.profile?.current_streak || 0}d</div>
            <div className="text-[10px] text-slate-400 uppercase font-bold">Streak</div>
          </div>
        </div>
      </Card>

      {/* Edit Form */}
      <Card className="p-6">
        <form onSubmit={handleSave} className="space-y-6">
          <h3 className="font-bold text-base text-slate-900 dark:text-white pb-3 border-b border-slate-100 dark:border-slate-800 flex items-center gap-2">
            <GraduationCap className="w-5 h-5 text-indigo-600" />
            <span>Academic Profile & Exam Goals</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Current Class / Education Level
              </label>
              <select
                value={currentClass}
                onChange={(e) => setCurrentClass(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 text-slate-800 dark:text-slate-100"
              >
                <option value="Class 10">Class 10</option>
                <option value="Class 11">Class 11</option>
                <option value="Class 12">Class 12</option>
                <option value="Undergraduate">Undergraduate (College)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Education Board / Curriculum
              </label>
              <select
                value={board}
                onChange={(e) => setBoard(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 text-slate-800 dark:text-slate-100"
              >
                <option value="CBSE">CBSE (Central Board)</option>
                <option value="ICSE">ICSE / ISC</option>
                <option value="State Board">State Board</option>
                <option value="IB">International Baccalaureate (IB)</option>
                <option value="Cambridge">Cambridge IGCSE / A-Levels</option>
              </select>
            </div>

            <Input
              label="Academic Marks / Score Percentage (%)"
              type="number"
              min={0}
              max={100}
              step={0.1}
              value={currentMarks}
              onChange={(e) => setCurrentMarks(parseFloat(e.target.value) || 0)}
              helperText="Previous board or current term percentage"
            />

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Target Entrance / Competitive Exam
              </label>
              <select
                value={targetExam}
                onChange={(e) => setTargetExam(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 text-slate-800 dark:text-slate-100"
              >
                <option value="JEE Main">JEE Main (Engineering)</option>
                <option value="JEE Advanced">JEE Advanced (IITs)</option>
                <option value="NEET">NEET (Medical / MBBS)</option>
                <option value="BITSAT">BITSAT (BITS Pilani)</option>
                <option value="CUET">CUET (Central Universities)</option>
                <option value="SAT">SAT / International</option>
                <option value="General STEM">General STEM & Logic</option>
              </select>
            </div>

            <Input
              label="Career Goal / Desired Specialization"
              value={careerGoal}
              onChange={(e) => setCareerGoal(e.target.value)}
              placeholder="e.g. Computer Science & AI, Medicine / MBBS, Data Science"
            />

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Admission / Target Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 text-slate-800 dark:text-slate-100"
              >
                <option value="General">General / Open</option>
                <option value="OBC-NCL">OBC-NCL</option>
                <option value="EWS">EWS (Economically Weaker Section)</option>
                <option value="SC">SC (Scheduled Caste)</option>
                <option value="ST">ST (Scheduled Tribe)</option>
              </select>
            </div>
          </div>

          <h3 className="font-bold text-base text-slate-900 dark:text-white pt-4 pb-2 border-t border-slate-100 dark:border-slate-800 flex items-center gap-2">
            <Target className="w-5 h-5 text-indigo-600" />
            <span>Account Details & Daily Habit</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Full Name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />

            <Input
              label="Daily Learning Goal (minutes)"
              type="number"
              min={5}
              max={240}
              value={dailyGoal}
              onChange={(e) => setDailyGoal(parseInt(e.target.value) || 30)}
            />
          </div>

          <Button type="submit" isLoading={saving} className="gap-2">
            <Check className="w-4 h-4" />
            <span>Save Academic Profile</span>
          </Button>
        </form>
      </Card>
    </div>
  );
};
