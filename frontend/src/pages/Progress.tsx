import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { ProgressBar } from '../components/ui/ProgressBar';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import {
  TrendingUp,
  Award,
  Flame,
  BookOpen,
  CheckCircle2,
  Calendar,
  AlertTriangle,
  Sparkles,
  Zap,
  Bot,
  Target
} from 'lucide-react';

export const Progress: React.FC = () => {
  const { data: summaryData, isLoading: loadingSummary } = useQuery({
    queryKey: ['progress-summary'],
    queryFn: async () => {
      const res = await api.get('/progress');
      return res.data;
    },
  });

  const { data: topicAnalysisData } = useQuery({
    queryKey: ['topic-analysis'],
    queryFn: async () => {
      const res = await api.get('/progress/topic-analysis');
      return res.data;
    },
  });

  const { data: historyData } = useQuery({
    queryKey: ['progress-history'],
    queryFn: async () => {
      const res = await api.get('/progress/history');
      return res.data;
    },
  });

  const { data: achievementsData } = useQuery({
    queryKey: ['achievements'],
    queryFn: async () => {
      const res = await api.get('/gamification/achievements');
      return res.data;
    },
  });

  if (loadingSummary) {
    return (
      <div className="flex h-96 items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const summary = summaryData?.data || {
    total_lessons: 0,
    completed_lessons: 0,
    completion_percentage: 0,
    total_xp: 0,
    current_streak: 0,
    enrolled_courses: 0,
  };

  const analysis = topicAnalysisData?.data || {
    strong_topics: [],
    weak_topics: [],
    moderate_topics: [],
    total_evaluated_topics: 0
  };

  const strongTopics = analysis.strong_topics || [];
  const weakTopics = analysis.weak_topics || [];
  const moderateTopics = analysis.moderate_topics || [];
  const history = historyData?.data || [];
  const achievements = achievementsData?.data || [];

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 dark:text-white">
            Learning Progress & Analytics
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Automated topic-level mastery diagnostics, weak areas remediation, and achievement milestones.
          </p>
        </div>

        <Link to="/quick-assessment">
          <Button className="gap-2 bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm">
            <Zap className="w-4 h-4" />
            <span>Take Skill Assessment</span>
          </Button>
        </Link>
      </div>

      {/* High-level stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-5 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 dark:bg-indigo-950 text-indigo-600 flex items-center justify-center">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-bold">{summary.completion_percentage}%</div>
            <div className="text-xs text-slate-500">Curriculum Completed</div>
          </div>
        </Card>

        <Card className="p-5 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 dark:bg-emerald-950 text-emerald-600 flex items-center justify-center">
            <Award className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-bold">{summary.total_xp}</div>
            <div className="text-xs text-slate-500">Total XP Earned</div>
          </div>
        </Card>

        <Card className="p-5 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-50 dark:bg-amber-950 text-amber-600 flex items-center justify-center">
            <Flame className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-bold">{summary.current_streak} Days</div>
            <div className="text-xs text-slate-500">Active Streak</div>
          </div>
        </Card>

        <Card className="p-5 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-950 text-blue-600 flex items-center justify-center">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-bold">{summary.completed_lessons}</div>
            <div className="text-xs text-slate-500">Lessons Completed</div>
          </div>
        </Card>
      </div>

      {/* Empty State if no tests taken yet */}
      {strongTopics.length === 0 && weakTopics.length === 0 && moderateTopics.length === 0 && (
        <Card className="p-8 text-center space-y-4 border-dashed border-2 border-slate-300 dark:border-slate-700">
          <div className="w-14 h-14 mx-auto rounded-2xl bg-indigo-50 dark:bg-indigo-950 text-indigo-600 flex items-center justify-center">
            <Zap className="w-7 h-7" />
          </div>
          <div className="max-w-md mx-auto space-y-1">
            <h3 className="font-bold text-lg text-slate-900 dark:text-white">
              No Topic Diagnostics Available Yet
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Complete the 10-question Quick Skill Assessment or practice any lesson to generate automatic Strong and Weak Topic analytics.
            </p>
          </div>
          <Link to="/quick-assessment" className="inline-block">
            <Button className="gap-2">
              <Zap className="w-4 h-4" />
              <span>Start Quick Diagnostic Test</span>
            </Button>
          </Link>
        </Card>
      )}

      {/* Dual Strong & Weak Topic Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Strong Topics (Mastered >= 75%) */}
        <Card className="space-y-4 border-t-4 border-t-emerald-500">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-emerald-500" />
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                Strong Topics (Mastered)
              </h2>
            </div>
            <Badge variant="success" size="sm">
              {strongTopics.length} Topics
            </Badge>
          </div>

          {strongTopics.length === 0 ? (
            <p className="text-xs text-slate-500 py-6 text-center">
              Complete more questions with ≥75% accuracy to register strong topics.
            </p>
          ) : (
            <div className="space-y-3">
              {strongTopics.map((item: any, idx: number) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl border border-emerald-200 dark:border-emerald-900/60 bg-emerald-50/30 dark:bg-emerald-950/20 space-y-2"
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <h4 className="font-bold text-sm text-slate-900 dark:text-slate-100">{item.topic}</h4>
                      <span className="text-[11px] text-slate-500 dark:text-slate-400">{item.subject}</span>
                    </div>
                    <Badge variant="success" size="sm">
                      {item.accuracy_rate}% Mastery
                    </Badge>
                  </div>
                  <p className="text-xs text-emerald-800 dark:text-emerald-300 font-medium">
                    {item.recommendation}
                  </p>
                  <ProgressBar progress={item.accuracy_rate} color="primary" />
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Weak Topics (Focus Areas < 60%) */}
        <Card className="space-y-4 border-t-4 border-t-rose-500">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-rose-500" />
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                Focus Areas (Needing Improvement)
              </h2>
            </div>
            <Badge variant="danger" size="sm">
              {weakTopics.length} Topics
            </Badge>
          </div>

          {weakTopics.length === 0 ? (
            <p className="text-xs text-slate-500 py-6 text-center">
              Excellent! No weak topics detected below 60% accuracy.
            </p>
          ) : (
            <div className="space-y-3">
              {weakTopics.map((item: any, idx: number) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl border border-rose-200 dark:border-rose-900/60 bg-rose-50/30 dark:bg-rose-950/20 space-y-2"
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <h4 className="font-bold text-sm text-slate-900 dark:text-slate-100">{item.topic}</h4>
                      <span className="text-[11px] text-slate-500 dark:text-slate-400">{item.subject}</span>
                    </div>
                    <Badge variant="danger" size="sm">
                      {item.accuracy_rate}% Accuracy
                    </Badge>
                  </div>
                  <p className="text-xs text-rose-800 dark:text-rose-300">
                    {item.recommendation}
                  </p>
                  <ProgressBar progress={item.accuracy_rate} color="accent" />
                  <div className="pt-1">
                    <Link to="/ai-tutor">
                      <button className="text-[11px] font-semibold text-rose-700 dark:text-rose-400 hover:underline flex items-center gap-1">
                        <Bot className="w-3.5 h-3.5" />
                        <span>Ask AI Mentor to explain {item.topic}</span>
                      </button>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Moderate Topics (In Progress 60-74%) */}
      {moderateTopics.length > 0 && (
        <Card className="space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
            <div className="flex items-center gap-2">
              <Target className="w-5 h-5 text-amber-500" />
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                Developing Topics (In Progress: 60% - 74%)
              </h2>
            </div>
            <Badge variant="warning" size="sm">
              {moderateTopics.length} Topics
            </Badge>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {moderateTopics.map((item: any, idx: number) => (
              <div
                key={idx}
                className="p-4 rounded-xl border border-amber-200 dark:border-amber-800/60 bg-amber-50/20 dark:bg-amber-950/20 space-y-2"
              >
                <div className="flex justify-between items-center">
                  <div>
                    <h4 className="font-bold text-sm text-slate-800 dark:text-slate-200">{item.topic}</h4>
                    <span className="text-[11px] text-slate-500">{item.subject}</span>
                  </div>
                  <Badge variant="warning" size="sm">
                    {item.accuracy_rate}%
                  </Badge>
                </div>
                <p className="text-xs text-slate-500">{item.recommendation}</p>
                <ProgressBar progress={item.accuracy_rate} color="primary" />
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Badges & Achievements */}
      <Card className="space-y-4">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-100 dark:border-slate-800">
          <Award className="w-5 h-5 text-indigo-600" />
          <h2 className="text-base font-bold text-slate-900 dark:text-white">
            Badges & Milestones
          </h2>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
          {achievements.map((ach: any) => (
            <div
              key={ach.id}
              className={`p-4 rounded-2xl border text-center space-y-2 transition-all ${
                ach.earned
                  ? 'bg-indigo-50/50 dark:bg-indigo-950/40 border-indigo-200 dark:border-indigo-800'
                  : 'bg-slate-50/50 dark:bg-slate-800/30 border-slate-200 dark:border-slate-800 opacity-50 grayscale'
              }`}
            >
              <div className="text-3xl mb-1">{ach.icon || '🏆'}</div>
              <h4 className="font-bold text-xs text-slate-900 dark:text-slate-100">{ach.name}</h4>
              <p className="text-[10px] text-slate-500 leading-tight">{ach.description}</p>
              <Badge variant={ach.earned ? 'primary' : 'neutral'} size="sm">
                +{ach.xp_reward} XP
              </Badge>
            </div>
          ))}
        </div>
      </Card>

      {/* Lesson Activity History */}
      <Card className="space-y-4">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-100 dark:border-slate-800">
          <Calendar className="w-5 h-5 text-indigo-600" />
          <h2 className="text-base font-bold text-slate-900 dark:text-white">
            Lesson Completion Log
          </h2>
        </div>

        {history.length === 0 ? (
          <p className="text-sm text-slate-500 py-4 text-center">
            No lesson history yet. Complete your first lesson to view your log.
          </p>
        ) : (
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {history.map((item: any, idx: number) => (
              <div key={idx} className="py-3 flex items-center justify-between text-xs">
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  <span className="font-medium text-slate-800 dark:text-slate-200">
                    {item.lesson_title}
                  </span>
                </div>
                <div className="text-slate-400">
                  {item.completed_at ? new Date(item.completed_at).toLocaleString() : 'In Progress'}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};
