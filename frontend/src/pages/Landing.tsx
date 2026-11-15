import React from 'react';
import { Link } from 'react-router-dom';
import {
  Bot,
  BrainCircuit,
  Calculator,
  Code2,
  Compass,
  FlaskConical,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  Zap,
  Target,
  BarChart3,
  Lightbulb
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';

export const Landing: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col">
      {/* Top Navigation */}
      <header className="h-20 border-b border-slate-200/80 dark:border-slate-800/80 bg-white/70 dark:bg-slate-950/70 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto h-full px-6 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-600 to-indigo-500 flex items-center justify-center text-white shadow-md shadow-indigo-200 dark:shadow-none">
              <Bot className="w-6 h-6" />
            </div>
            <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-indigo-600 via-indigo-500 to-emerald-500 bg-clip-text text-transparent">
              LearnSphere AI
            </span>
          </Link>

          <div className="flex items-center gap-4">
            <Link to="/login">
              <Button variant="ghost" size="sm">
                Sign In
              </Button>
            </Link>
            <Link to="/register">
              <Button size="sm" className="gap-2">
                <span>Start Learning</span>
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-16 pb-24 px-6 md:px-12 text-center max-w-5xl mx-auto">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-200 dark:border-indigo-800 text-indigo-700 dark:text-indigo-300 text-xs font-semibold mb-8">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Brilliant-Inspired Interactive Problem Solving & AI Mentorship</span>
        </div>

        <h1 className="text-4xl md:text-6xl font-black tracking-tight text-slate-900 dark:text-white leading-[1.15] mb-6">
          Learn by Doing.{' '}
          <span className="bg-gradient-to-r from-indigo-600 via-indigo-500 to-emerald-500 bg-clip-text text-transparent">
            Understand by Exploring.
          </span>{' '}
          Improve with AI.
        </h1>

        <p className="text-lg md:text-xl text-slate-600 dark:text-slate-300 max-w-2xl mx-auto mb-10 leading-relaxed">
          Master mathematics, physics, computer science, and logic through interactive visual challenges, instant feedback, and a context-aware AI tutor.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link to="/register" className="w-full sm:w-auto">
            <Button size="lg" className="w-full gap-2 px-8 py-3.5 text-base shadow-lg shadow-indigo-200 dark:shadow-none">
              <span>Start Learning Free</span>
              <ArrowRight className="w-5 h-5" />
            </Button>
          </Link>
          <Link to="/subjects" className="w-full sm:w-auto">
            <Button variant="outline" size="lg" className="w-full px-8 py-3.5 text-base">
              Explore Courses
            </Button>
          </Link>
        </div>

        {/* Floating preview banner */}
        <div className="mt-16 p-4 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl max-w-4xl mx-auto text-left">
          <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-100 dark:border-slate-800">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-rose-500"></span>
              <span className="w-3 h-3 rounded-full bg-amber-500"></span>
              <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
              <span className="ml-2 text-xs font-mono text-slate-400">Interactive Challenge: Newton's 2nd Law</span>
            </div>
            <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
              <Zap className="w-3.5 h-3.5" />
              <span>Instant AI Evaluation</span>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700/60">
              <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200 mb-2">Question</h4>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed mb-3">
                A 5 kg block accelerates at 4 m/s². What net force in Newtons is applied?
              </p>
              <div className="inline-block px-3 py-1.5 rounded-lg bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 font-mono text-xs font-bold">
                Answer: 20 N ✓
              </div>
            </div>
            <div className="p-4 rounded-2xl bg-indigo-50/50 dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-900/40">
              <div className="flex items-center gap-2 mb-2">
                <Bot className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                <h4 className="text-sm font-bold text-indigo-900 dark:text-indigo-200">AI Tutor Analysis</h4>
              </div>
              <p className="text-xs text-indigo-800/90 dark:text-indigo-300 leading-relaxed">
                "Spot on! By using Newton's Second Law $F = ma$, we multiply mass (5 kg) by acceleration (4 m/s²) to find 20 Newtons."
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 4 Core Pillars / Featured Categories */}
      <section className="py-20 px-6 max-w-7xl mx-auto w-full">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-3xl font-extrabold text-slate-900 dark:text-white mb-4">
            Four Core Learning Disciplines
          </h2>
          <p className="text-slate-600 dark:text-slate-400 text-sm md:text-base">
            Structured step-by-step pathways curated for deep conceptual understanding.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card hoverEffect className="space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
              <Calculator className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-lg text-slate-900 dark:text-white">Mathematics</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              Algebra, geometry, calculus, probability, and statistics explained with visual intuition.
            </p>
            <div className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 flex items-center gap-1">
              <span>Explore Algebra & More</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </Card>

          <Card hoverEffect className="space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
              <FlaskConical className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-lg text-slate-900 dark:text-white">Science</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              Classical mechanics, thermodynamics, chemistry, and astronomical models.
            </p>
            <div className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
              <span>Explore Physics & More</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </Card>

          <Card hoverEffect className="space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-amber-50 dark:bg-amber-950 text-amber-600 dark:text-amber-400 flex items-center justify-center">
              <Code2 className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-lg text-slate-900 dark:text-white">Computer Science</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              Python programming, algorithms, data structures, and foundational AI principles.
            </p>
            <div className="text-xs font-semibold text-amber-600 dark:text-amber-400 flex items-center gap-1">
              <span>Explore Python & Logic</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </Card>

          <Card hoverEffect className="space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-rose-50 dark:bg-rose-950 text-rose-600 dark:text-rose-400 flex items-center justify-center">
              <BrainCircuit className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-lg text-slate-900 dark:text-white">Logical Reasoning</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              Puzzles, deductive logic, fallacy identification, and critical thinking challenges.
            </p>
            <div className="text-xs font-semibold text-rose-600 dark:text-rose-400 flex items-center gap-1">
              <span>Explore Puzzles & Logic</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </Card>
        </div>
      </section>

      {/* Autonomous AI Mentor Section */}
      <section className="py-20 bg-indigo-900 text-white px-6">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-800 text-indigo-300 text-xs font-medium">
              <Bot className="w-4 h-4" />
              Autonomous AI Mentor Agent
            </div>
            <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight">
              An AI Tutor that doesn't just give answers — it guides your thinking.
            </h2>
            <p className="text-indigo-200 text-sm md:text-base leading-relaxed">
              Our autonomous AI Mentor agent understands the exact question you're on, checks your prior attempts, detects weak spots from your actual database history, and dynamically offers hints and personalized 7-day or 30-day study plans.
            </p>
            <div className="space-y-3 pt-2">
              <div className="flex items-center gap-3 text-sm">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                <span>Deterministic assessment engine with real Postgres scoring</span>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                <span>Automated weakness analysis from your test performance</span>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                <span>Custom study plans saved directly into your dashboard</span>
              </div>
            </div>
          </div>

          <div className="bg-slate-950/80 border border-indigo-700/60 rounded-3xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-3 pb-4 border-b border-slate-800">
              <div className="w-8 h-8 rounded-xl bg-indigo-600 flex items-center justify-center text-white">
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <h5 className="font-bold text-sm">LearnSphere AI Tutor</h5>
                <p className="text-[11px] text-slate-400">Tool execution: analyze_weaknesses → generate_study_plan</p>
              </div>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-slate-300">
                <strong>Student:</strong> "I want to improve my Python loop skills in 30 days. I have 1 hour daily."
              </div>
              <div className="p-3 rounded-xl bg-indigo-950/60 border border-indigo-800/80 text-indigo-200">
                <strong>AI Mentor:</strong> "I checked your test logs: you scored 60% on list iteration. I've built a 30-day schedule focusing on loops and data structures for 60 min/day, now saved in your Study Plan tab!"
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto border-t border-slate-200 dark:border-slate-800 py-10 px-6 text-center text-xs text-slate-500 dark:text-slate-400">
        <p>© 2026 LearnSphere AI. Brilliant-inspired interactive learning platform with autonomous AI mentoring.</p>
      </footer>
    </div>
  );
};
