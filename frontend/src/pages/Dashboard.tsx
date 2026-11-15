import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { DashboardData } from '../types';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { ProgressBar } from '../components/ui/ProgressBar';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { EmptyState } from '../components/ui/EmptyState';
import {
  Flame,
  Award,
  BookOpen,
  Target,
  ArrowRight,
  TrendingDown,
  Sparkles,
  Bot,
  Zap,
  CheckCircle2,
  CalendarDays,
  GraduationCap
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

export const Dashboard: React.FC = () => {
  const { data, isLoading, error } = useQuery<{ success: boolean; data: DashboardData }>({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const res = await api.get('/student/dashboard');
      return res.data;
    },
  });

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !data?.data) {
    return (
      <div className="p-8 text-center">
        <p className="text-rose-600 font-medium">Failed to load student dashboard data.</p>
      </div>
    );
  }

  const dash = data.data;
  const userProfile = (dash.user as any)?.profile;
  const strongTopics = dash.strong_topics || [];
  const weakTopics = dash.weak_topics || [];

  return (
    <div className="space-y-8">
      {/* Welcome Banner & Academic Profile Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200/60 dark:border-slate-800">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 dark:text-white">
              Welcome back, {dash.user.full_name || dash.user.username}! 🎓
            </h1>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            "Learn by Doing, Understand by Exploring, Improve with AI."
          </p>

          {/* Academic Profile Badges */}
          {userProfile && (userProfile.current_class || userProfile.target_exam || userProfile.career_goal) && (
            <div className="flex flex-wrap items-center gap-2 pt-1">
              {userProfile.current_class && (
                <Badge variant="primary" size="sm" className="gap-1">
                  <GraduationCap className="w-3 h-3" />
                  <span>{userProfile.current_class}</span>
                </Badge>
              )}
              {userProfile.board && (
                <Badge variant="neutral" size="sm">
                  {userProfile.board}
                </Badge>
              )}
              {userProfile.target_exam && (
                <Badge variant="warning" size="sm" className="gap-1 font-semibold">
                  <Target className="w-3 h-3" />
                  <span>Target: {userProfile.target_exam}</span>
                </Badge>
              )}
              {userProfile.career_goal && (
                <Badge variant="success" size="sm">
                  Goal: {userProfile.career_goal}
                </Badge>
              )}
              <Link to="/profile" className="text-[11px] text-indigo-600 dark:text-indigo-400 font-semibold hover:underline ml-1">
                Edit Profile
              </Link>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2.5">
          <Link to="/quick-assessment">
            <Button variant="outline" className="gap-2 text-indigo-600 border-indigo-200 hover:bg-indigo-50 dark:hover:bg-indigo-950/40">
              <Zap className="w-4 h-4 text-indigo-600" />
              <span>Diagnostic Test</span>
            </Button>
          </Link>
          <Link to="/subjects">
            <Button className="gap-2 shadow-sm bg-indigo-600 hover:bg-indigo-700 text-white">
              <span>Continue Learning</span>
              <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
        </div>
      </div>

      {/* Stats Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="flex items-center gap-4 p-5">
          <div className="w-12 h-12 rounded-2xl bg-amber-50 dark:bg-amber-950/60 text-amber-600 flex items-center justify-center shrink-0">
            <Flame className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-black text-slate-900 dark:text-white">
              {dash.stats.current_streak} <span className="text-xs font-medium text-slate-400">days</span>
            </div>
            <div className="text-xs text-slate-500 font-medium">Learning Streak</div>
          </div>
        </Card>

        <Card className="flex items-center gap-4 p-5">
          <div className="w-12 h-12 rounded-2xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 flex items-center justify-center shrink-0">
            <Award className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-black text-slate-900 dark:text-white">
              {dash.stats.xp_total}
            </div>
            <div className="text-xs text-slate-500 font-medium">Total XP Earned</div>
          </div>
        </Card>

        <Card className="flex items-center gap-4 p-5">
          <div className="w-12 h-12 rounded-2xl bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 flex items-center justify-center shrink-0">
            <BookOpen className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-black text-slate-900 dark:text-white">
              {dash.stats.lessons_completed}
            </div>
            <div className="text-xs text-slate-500 font-medium">Lessons Mastered</div>
          </div>
        </Card>

        <Card className="flex items-center gap-4 p-5">
          <div className="w-12 h-12 rounded-2xl bg-blue-50 dark:bg-blue-950/60 text-blue-600 flex items-center justify-center shrink-0">
            <Target className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-black text-slate-900 dark:text-white">
              {dash.stats.daily_goal_minutes} <span className="text-xs font-medium text-slate-400">min</span>
            </div>
            <div className="text-xs text-slate-500 font-medium">Daily Goal</div>
          </div>
        </Card>
      </div>

      {/* Main 2-column section: Courses & Weekly Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column (Courses in Progress) */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">Courses in Progress</h3>
            <Link to="/subjects" className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline">
              View All Courses
            </Link>
          </div>

          {dash.enrolled_courses.length === 0 ? (
            <EmptyState
              title="No courses enrolled yet"
              description="Explore our interactive Mathematics, Physics, Python, or Logic tracks to start your learning streak."
              actionText="Explore Subjects"
              onAction={() => window.location.href = '/subjects'}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {dash.enrolled_courses.map((course) => (
                <Card key={course.id} hoverEffect className="space-y-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-bold text-slate-900 dark:text-white text-base">{course.title}</h4>
                      <p className="text-xs text-slate-500 mt-0.5">
                        {course.completed_lessons} of {course.total_lessons} lessons completed
                      </p>
                    </div>
                    <span
                      className="w-3 h-3 rounded-full shrink-0"
                      style={{ backgroundColor: course.color || '#6366f1' }}
                    />
                  </div>

                  <ProgressBar progress={course.progress_pct} color="primary" showLabel />

                  <Link to={`/courses/${course.id}`} className="block">
                    <Button variant="outline" size="sm" className="w-full text-xs">
                      Continue Course
                    </Button>
                  </Link>
                </Card>
              ))}
            </div>
          )}

          {/* Weekly Performance Bar Chart */}
          <Card className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">Weekly Performance (XP)</h3>
              <Badge variant="primary" size="sm">Last 7 Days</Badge>
            </div>

            <div className="h-56 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={dash.weekly_xp}>
                  <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickLine={false} />
                  <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      borderColor: '#334155',
                      borderRadius: '0.75rem',
                      color: '#fff',
                      fontSize: '12px',
                    }}
                  />
                  <Bar dataKey="xp" fill="#6366f1" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>

        {/* Right Column (AI Mentor & Topic Mastery) */}
        <div className="space-y-6">
          {/* AI Mentor Quick Access Widget */}
          <Card className="bg-gradient-to-br from-indigo-900 to-indigo-950 text-white border-indigo-800 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-indigo-600 flex items-center justify-center text-white">
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-bold text-sm">Autonomous AI Mentor</h4>
                <p className="text-[11px] text-indigo-300">Personalized feedback & study plans</p>
              </div>
            </div>
            <p className="text-xs text-indigo-200 leading-relaxed">
              Targeted hints, weakness remediation, and custom study plans tailored to your goal.
            </p>
            <div className="flex gap-2">
              <Link to="/ai-tutor" className="flex-1">
                <Button size="sm" className="w-full bg-white text-indigo-900 hover:bg-indigo-50 font-semibold text-xs">
                  Ask AI Mentor
                </Button>
              </Link>
              <Link to="/study-plan" className="flex-1">
                <Button size="sm" variant="outline" className="w-full text-white border-indigo-400 hover:bg-indigo-800 text-xs">
                  Study Plan
                </Button>
              </Link>
            </div>
          </Card>

          {/* Strong Topics Widget */}
          <Card className="space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-700/80">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-emerald-500" />
                <span>Strong Topics (Mastered)</span>
              </h3>
              <Link to="/progress" className="text-xs text-indigo-600 dark:text-indigo-400 font-medium">
                View All
              </Link>
            </div>

            {strongTopics.length === 0 ? (
              <p className="text-xs text-slate-500 py-2 text-center">
                Take the <Link to="/quick-assessment" className="text-indigo-600 font-semibold underline">Diagnostic Test</Link> to discover your strong topics.
              </p>
            ) : (
              <div className="space-y-2.5">
                {strongTopics.slice(0, 3).map((topic, idx) => (
                  <div key={idx} className="space-y-1">
                    <div className="flex justify-between text-xs font-medium">
                      <span className="text-slate-800 dark:text-slate-200">{topic.topic}</span>
                      <span className="text-emerald-600 font-semibold">{topic.accuracy_rate}%</span>
                    </div>
                    <ProgressBar progress={topic.accuracy_rate} color="primary" />
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Weak Topics Analysis */}
          <Card className="space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-700/80">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <TrendingDown className="w-4 h-4 text-rose-500" />
                <span>Focus Areas (Weak Topics)</span>
              </h3>
              <Link to="/progress" className="text-xs text-indigo-600 dark:text-indigo-400 font-medium">
                Analysis
              </Link>
            </div>

            {weakTopics.length === 0 ? (
              <p className="text-xs text-slate-500 py-2 text-center">
                No weak topics detected. Practice questions to identify growth areas.
              </p>
            ) : (
              <div className="space-y-2.5">
                {weakTopics.slice(0, 3).map((topic, idx) => (
                  <div key={idx} className="space-y-1">
                    <div className="flex justify-between text-xs font-medium">
                      <span className="text-slate-800 dark:text-slate-200">{topic.topic}</span>
                      <span className="text-rose-600 font-semibold">{topic.accuracy_rate}% accuracy</span>
                    </div>
                    <ProgressBar progress={topic.accuracy_rate} color="accent" />
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Recent Test Results */}
          <Card className="space-y-4">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white pb-2 border-b border-slate-100 dark:border-slate-700/80">
              Recent Assessments
            </h3>

            {dash.recent_results.length === 0 ? (
              <p className="text-xs text-slate-500 py-3 text-center">
                No assessments taken yet. Open any lesson to solve challenges!
              </p>
            ) : (
              <div className="space-y-2.5">
                {dash.recent_results.map((res, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-700/40 text-xs"
                  >
                    <div>
                      <div className="font-semibold text-slate-800 dark:text-slate-200">
                        {res.lesson_title || 'STEM Assessment'}
                      </div>
                      <div className="text-[10px] text-slate-400">
                        {res.completed_at ? new Date(res.completed_at).toLocaleDateString() : 'Completed'}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-emerald-600 dark:text-emerald-400">
                        {Math.round(res.score)}%
                      </div>
                      <div className="text-[10px] text-slate-400">+{res.xp_earned} XP</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};
