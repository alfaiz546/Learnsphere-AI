import React, { useState, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { aiService } from '../services/ai';
import { useAuth } from '../contexts/AuthContext';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Badge } from '../components/ui/Badge';
import { Alert } from '../components/ui/Alert';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import {
  CalendarDays,
  Sparkles,
  Clock,
  Target,
  CheckCircle2,
  BookOpen,
  RotateCcw
} from 'lucide-react';

export const StudyPlan: React.FC = () => {
  const { user } = useAuth();
  const profile = user?.profile;
  const defaultGoal = profile?.target_exam
    ? `Comprehensive prep for ${profile.target_exam} focusing on weak topics`
    : 'Master Python fundamentals and STEM problem-solving in 30 days';

  const [goal, setGoal] = useState(defaultGoal);
  const [hours, setHours] = useState<number>(1.5);
  const [duration, setDuration] = useState<number>(30);
  const [createdPlan, setCreatedPlan] = useState<any | null>(null);

  // Fetch active study plan if already generated
  const { data: currentPlanRes, isLoading: loadingCurrent } = useQuery({
    queryKey: ['current-study-plan'],
    queryFn: async () => {
      const res = await aiService.getCurrentStudyPlan();
      return res;
    },
  });

  useEffect(() => {
    if (currentPlanRes?.data && !createdPlan) {
      setCreatedPlan(currentPlanRes.data);
    }
  }, [currentPlanRes]);

  const planMutation = useMutation({
    mutationFn: async () => {
      const res = await aiService.generateStudyPlan({
        goal,
        available_hours_per_day: hours,
        duration_days: duration,
      });
      return res.data;
    },
    onSuccess: (data) => {
      setCreatedPlan(data);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    planMutation.mutate();
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2.5">
          <CalendarDays className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
          <span>AI-Powered Study Plan Generator</span>
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Our AI mentor uses your test accuracy history and academic profile to construct a custom daily roadmap saved to your profile.
        </p>
      </div>

      {/* Generator Form */}
      <Card className="p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <Input
              label="What is your learning goal or target exam?"
              required
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              helperText="e.g. Master Linear Equations, JEE Advanced Physics, or NEET Biology Prep"
            />
            {profile?.target_exam && (
              <div className="mt-2 flex items-center gap-2">
                <span className="text-xs text-slate-500">Quick Suggestion:</span>
                <button
                  type="button"
                  onClick={() => setGoal(`Target ${profile.target_exam} High-Scoring Mastery Plan`)}
                  className="text-xs text-indigo-600 dark:text-indigo-400 font-semibold hover:underline"
                >
                  Target {profile.target_exam} High-Scoring Mastery Plan
                </button>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Daily Study Time: <span className="font-bold text-indigo-600">{hours} Hours</span>
              </label>
              <input
                type="range"
                min="0.5"
                max="4.0"
                step="0.5"
                value={hours}
                onChange={(e) => setHours(parseFloat(e.target.value))}
                className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg cursor-pointer accent-indigo-600"
              />
              <div className="flex justify-between text-[11px] text-slate-400">
                <span>30 min</span>
                <span>2 hours</span>
                <span>4 hours</span>
              </div>
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Plan Duration
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setDuration(7)}
                  className={`py-2.5 px-4 rounded-xl border text-xs font-bold transition-colors ${
                    duration === 7
                      ? 'bg-indigo-600 text-white border-indigo-600'
                      : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700'
                  }`}
                >
                  7-Day Sprint
                </button>
                <button
                  type="button"
                  onClick={() => setDuration(30)}
                  className={`py-2.5 px-4 rounded-xl border text-xs font-bold transition-colors ${
                    duration === 30
                      ? 'bg-indigo-600 text-white border-indigo-600'
                      : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700'
                  }`}
                >
                  30-Day Mastery
                </button>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button
              type="submit"
              isLoading={planMutation.isPending}
              className="gap-2 bg-indigo-600 hover:bg-indigo-700 text-white"
            >
              <Sparkles className="w-4 h-4" />
              <span>{createdPlan ? 'Regenerate Study Plan' : 'Generate & Save Study Plan'}</span>
            </Button>
          </div>
        </form>
      </Card>

      {/* Plan Result */}
      {loadingCurrent && !createdPlan && (
        <div className="flex justify-center py-8">
          <LoadingSpinner size="md" />
        </div>
      )}

      {createdPlan && (
        <div className="space-y-6">
          <Alert type="success" title="Active Study Plan Loaded">
            {createdPlan.title || 'Personalized Study Roadmap'} — structured and saved to your profile.
          </Alert>

          {createdPlan.ai_summary && (
            <Card className="p-6 bg-indigo-50/60 dark:bg-indigo-950/40 border-indigo-200 dark:border-indigo-900/50 space-y-2">
              <h3 className="font-bold text-sm text-indigo-900 dark:text-indigo-200 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                <span>AI Mentor Strategy & Motivation</span>
              </h3>
              <p className="text-xs text-indigo-800/90 dark:text-indigo-300 leading-relaxed whitespace-pre-wrap">
                {createdPlan.ai_summary}
              </p>
            </Card>
          )}

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Daily Schedule ({createdPlan.plan_data?.schedule?.length || 0} Days)
              </h3>
              <Badge variant="primary" size="sm">
                {createdPlan.plan_data?.hours_per_day || hours}h/day
              </Badge>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {createdPlan.plan_data?.schedule?.map((item: any, idx: number) => (
                <Card key={idx} className="p-4 space-y-2.5 hover:border-indigo-300 transition-all">
                  <div className="flex justify-between items-center pb-2 border-b border-slate-100 dark:border-slate-800">
                    <span className="font-bold text-xs text-indigo-600 dark:text-indigo-400">
                      Day {item.day}
                    </span>
                    <Badge variant="neutral" size="sm">
                      <Clock className="w-3 h-3" />
                      <span>{item.study_minutes} min</span>
                    </Badge>
                  </div>
                  <div className="text-xs text-slate-700 dark:text-slate-300 space-y-1">
                    {item.activities?.map((act: string, aIdx: number) => (
                      <p key={aIdx} className="leading-snug flex items-start gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
                        <span>{act}</span>
                      </p>
                    ))}
                  </div>
                </Card>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
