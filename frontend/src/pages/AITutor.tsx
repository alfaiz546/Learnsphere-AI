import React from 'react';
import { AITutorChat } from '../components/ai/AITutorChat';
import { Card } from '../components/ui/Card';
import { Bot, Sparkles, Brain, Target, ShieldCheck } from 'lucide-react';

export const AITutor: React.FC = () => {
  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2.5">
          <Bot className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
          <span>LearnSphere AI Mentor</span>
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Your personal autonomous tutor powered by Google Gemini and real database tool integration.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 dark:bg-indigo-950 text-indigo-600 flex items-center justify-center shrink-0">
            <Brain className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200">Weakness Analysis</h4>
            <p className="text-[11px] text-slate-400">Queries your real test answers to find weak spots</p>
          </div>
        </Card>

        <Card className="p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 dark:bg-emerald-950 text-emerald-600 flex items-center justify-center shrink-0">
            <Target className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200">Personalized Study Plans</h4>
            <p className="text-[11px] text-slate-400">Generates 7-day and 30-day scheduled roadmaps</p>
          </div>
        </Card>

        <Card className="p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-50 dark:bg-amber-950 text-amber-600 flex items-center justify-center shrink-0">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200">Brilliant-Style Socratic Tutoring</h4>
            <p className="text-[11px] text-slate-400">Guides through problem-solving without spoiling answers</p>
          </div>
        </Card>
      </div>

      <AITutorChat />
    </div>
  );
};
