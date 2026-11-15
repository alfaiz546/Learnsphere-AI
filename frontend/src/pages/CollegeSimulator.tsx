import React, { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { Alert } from '../components/ui/Alert';
import {
  GraduationCap,
  Building2,
  MapPin,
  TrendingUp,
  Sparkles,
  Target,
  ShieldCheck,
  Compass,
  Bot,
  CalendarDays,
  Zap,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Info
} from 'lucide-react';

const BRANCH_OPTIONS_BY_EXAM: Record<string, { value: string; label: string }[]> = {
  'NEET': [
    { value: 'All', label: 'All Medical Programs' },
    { value: 'MBBS', label: 'MBBS (Medicine & Surgery)' },
    { value: 'BDS', label: 'BDS (Dental Surgery)' },
    { value: 'B.Pharm', label: 'B.Pharm (Pharmacy)' },
    { value: 'B.Sc Nursing', label: 'B.Sc Nursing' },
  ],
  'JEE Main': [
    { value: 'All', label: 'All Engineering Branches' },
    { value: 'Computer Science & Engineering', label: 'Computer Science & Engineering (CSE)' },
    { value: 'Data Science & Artificial Intelligence', label: 'Data Science & AI / ML' },
    { value: 'Electronics & Communication Engineering', label: 'Electronics & Communication (ECE)' },
    { value: 'Electrical Engineering', label: 'Electrical Engineering' },
    { value: 'Mechanical Engineering', label: 'Mechanical Engineering' },
  ],
  'JEE Advanced': [
    { value: 'All', label: 'All Engineering Branches' },
    { value: 'Computer Science & Engineering', label: 'Computer Science & Engineering (CSE)' },
    { value: 'Data Science & Artificial Intelligence', label: 'Data Science & AI' },
    { value: 'Electrical Engineering', label: 'Electrical Engineering' },
    { value: 'Mechanical Engineering', label: 'Mechanical Engineering' },
  ],
  'BITSAT': [
    { value: 'All', label: 'All BITS Branches' },
    { value: 'Computer Science', label: 'Computer Science' },
    { value: 'Electrical & Electronics', label: 'Electrical & Electronics' },
    { value: 'Mechanical Engineering', label: 'Mechanical Engineering' },
  ],
  'CUET': [
    { value: 'All', label: 'All University Courses' },
    { value: 'Computer Science', label: 'B.Sc Computer Science' },
    { value: 'Economics', label: 'B.A. (Hons) Economics' },
  ]
};

export const CollegeSimulator: React.FC = () => {
  const { user } = useAuth();
  const profile = user?.profile;

  const initialExam = profile?.target_exam && profile.target_exam in BRANCH_OPTIONS_BY_EXAM
    ? profile.target_exam
    : 'JEE Main';

  const [exam, setExam] = useState(initialExam);
  const [marks, setMarks] = useState<number>(profile?.current_marks || 88.0);
  const [category, setCategory] = useState(profile?.category || 'General');
  const [branch, setBranch] = useState('All');
  const [targetYear, setTargetYear] = useState<number>(profile?.target_year || 2025);
  const [selectedTier, setSelectedTier] = useState<'safe' | 'target' | 'reach'>('safe');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const simulationMutation = useMutation({
    mutationFn: async (payload: any) => {
      setErrorMessage(null);
      const res = await api.post('/simulator/predict-admission', payload);
      return res.data?.data;
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail || 'Simulation error occurred. Please verify your selected exam and branch options.';
      setErrorMessage(detail);
    }
  });

  const availableBranches = BRANCH_OPTIONS_BY_EXAM[exam] || [
    { value: 'All', label: 'All Branches' }
  ];

  const handleExamChange = (newExam: string) => {
    setExam(newExam);
    setErrorMessage(null);
    const validBranches = BRANCH_OPTIONS_BY_EXAM[newExam] || [];
    const isBranchValid = validBranches.some((b) => b.value === branch);
    if (!isBranchValid) {
      setBranch('All');
    }
  };

  useEffect(() => {
    simulationMutation.mutate({
      target_exam: exam,
      current_score_or_pct: marks,
      category,
      branch_preference: branch,
      target_year: targetYear,
    });
  }, []);

  const handleSimulate = (e: React.FormEvent) => {
    e.preventDefault();
    simulationMutation.mutate({
      target_exam: exam,
      current_score_or_pct: marks,
      category,
      branch_preference: branch,
      target_year: targetYear,
    });
  };

  const simData = simulationMutation.data;
  const isSimulating = simulationMutation.isPending;

  const safeList = simData?.categorized_colleges?.safe || [];
  const targetList = simData?.categorized_colleges?.target || [];
  const reachList = simData?.categorized_colleges?.reach || [];
  const currentList = selectedTier === 'safe' ? safeList : selectedTier === 'target' ? targetList : reachList;

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2.5">
          <GraduationCap className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
          <span>College Admission & Exam Outcome Simulator</span>
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Predict your exam percentile standing and college admission eligibility using reliable, year-specific cutoff benchmarks (JoSAA & MCC 2024).
        </p>
      </div>

      {/* Control Simulation Form */}
      <Card className="p-6">
        <form onSubmit={handleSimulate} className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                Target Exam
              </label>
              <select
                value={exam}
                onChange={(e) => handleExamChange(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm font-medium focus:ring-2 focus:ring-indigo-500"
              >
                <option value="JEE Main">JEE Main (NITs, IIITs, CFTIs)</option>
                <option value="JEE Advanced">JEE Advanced (IITs)</option>
                <option value="NEET">NEET-UG (Medical / MBBS & BDS)</option>
                <option value="BITSAT">BITSAT (BITS Pilani, Goa, Hyd)</option>
                <option value="CUET">CUET (Central Universities / DU)</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                Reservation Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm font-medium focus:ring-2 focus:ring-indigo-500"
              >
                <option value="General">General / Open (CRL)</option>
                <option value="OBC-NCL">OBC-NCL</option>
                <option value="EWS">GEN-EWS</option>
                <option value="SC">Scheduled Caste (SC)</option>
                <option value="ST">Scheduled Tribe (ST)</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center justify-between">
                <span>Course / Branch</span>
                <span className="text-[10px] text-indigo-500 font-normal">Filtered for {exam}</span>
              </label>
              <select
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm font-medium focus:ring-2 focus:ring-indigo-500"
              >
                {availableBranches.map((b) => (
                  <option key={b.value} value={b.value}>
                    {b.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                Target Year
              </label>
              <select
                value={targetYear}
                onChange={(e) => setTargetYear(parseInt(e.target.value))}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm font-medium focus:ring-2 focus:ring-indigo-500"
              >
                <option value={2025}>2025 Admissions</option>
                <option value={2026}>2026 Admissions</option>
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <label className="font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                <span>Mock Test Score / Marks Percentage:</span>
                <span className="text-slate-400 font-normal">(Calibrated to official percentile curve)</span>
              </label>
              <span className="font-bold text-indigo-600 dark:text-indigo-400 text-base">
                {marks}%
              </span>
            </div>
            <input
              type="range"
              min="50"
              max="99.9"
              step="0.5"
              value={marks}
              onChange={(e) => setMarks(parseFloat(e.target.value))}
              className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg cursor-pointer accent-indigo-600"
            />
            <div className="flex justify-between text-[11px] text-slate-400 font-medium">
              <span>50% (Baseline)</span>
              <span>75% (Competitive)</span>
              <span>90% (Top 1% Tier)</span>
              <span>99.9% (Top Tier Benchmark)</span>
            </div>
          </div>

          {errorMessage && (
            <Alert type="error" title="Incompatible Combination">
              {errorMessage}
            </Alert>
          )}

          <Button
            type="submit"
            isLoading={isSimulating}
            className="w-full sm:w-auto gap-2 bg-indigo-600 hover:bg-indigo-700 text-white"
          >
            <Sparkles className="w-4 h-4" />
            <span>Recalculate College Admission Chances</span>
          </Button>
        </form>
      </Card>

      {/* Simulator Results */}
      {isSimulating && (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      )}

      {simData && !isSimulating && (
        <div className="space-y-8">
          {/* Distinct Metrics Breakdown Cards (College Eligibility Summary) */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card className="p-4 flex flex-col justify-between">
              <div className="text-xs text-slate-500 font-medium flex items-center gap-1">
                <span>Mock Test Marks</span>
                <Info className="w-3 h-3 text-slate-400" />
              </div>
              <div className="text-2xl font-black text-slate-800 dark:text-slate-200 mt-2">
                {simData.metrics_breakdown?.mock_marks_percentage ?? marks}%
              </div>
              <div className="text-[10px] text-slate-400 mt-1">Raw performance score</div>
            </Card>

            <Card className="p-4 flex flex-col justify-between border-l-4 border-l-indigo-500">
              <div className="text-xs text-slate-500 font-medium flex items-center gap-1">
                <span>Predicted Percentile</span>
                <Target className="w-3 h-3 text-indigo-500" />
              </div>
              <div className="text-2xl font-black text-indigo-600 dark:text-indigo-400 mt-2">
                {simData.metrics_breakdown?.predicted_percentile}%
              </div>
              <div className="text-[10px] text-indigo-600/80 dark:text-indigo-300 mt-1">Calibrated score distribution</div>
            </Card>

            <Card className="p-4 flex flex-col justify-between border-l-4 border-l-emerald-500">
              <div className="text-xs text-slate-500 font-medium flex items-center gap-1">
                <span>Eligible Programs</span>
                <ShieldCheck className="w-3 h-3 text-emerald-500" />
              </div>
              <div className="text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-2">
                {simData.metrics_breakdown?.eligible_programs_count ?? (safeList.length + targetList.length)} Programs
              </div>
              <div className="text-[10px] text-emerald-600/80 dark:text-emerald-300 mt-1">
                {safeList.length} Safe • {targetList.length} Target choices
              </div>
            </Card>

            <Card className="p-4 flex flex-col justify-between border-l-4 border-l-amber-500">
              <div className="text-xs text-slate-500 font-medium flex items-center gap-1">
                <span>Admission Outlook</span>
                <TrendingUp className="w-3 h-3 text-amber-500" />
              </div>
              <div className="text-lg font-bold text-slate-800 dark:text-slate-200 mt-2">
                {simData.metrics_breakdown?.admission_outlook ?? "Competitive Standing"}
              </div>
              <div className="text-[10px] text-amber-600/80 dark:text-amber-300 mt-1">
                Category: {category} • {targetYear}
              </div>
            </Card>
          </div>

          {/* Classification Methodology Guide: Historical Cutoff Benchmarks */}
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/70 text-xs">
            <div className="font-semibold text-slate-800 dark:text-slate-200 mb-2 flex items-center gap-1.5">
              <Info className="w-4 h-4 text-indigo-500" />
              <span>College Classification Standards (Historical Cutoff Comparisons)</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-slate-600 dark:text-slate-300">
              <div className="flex items-start gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500 mt-1 shrink-0" />
                <div>
                  <span className="font-bold text-emerald-600 dark:text-emerald-400">Safe:</span> Score comfortably clears historical cutoff thresholds with high admission confidence.
                </div>
              </div>
              <div className="flex items-start gap-2">
                <span className="w-2 h-2 rounded-full bg-amber-500 mt-1 shrink-0" />
                <div>
                  <span className="font-bold text-amber-600 dark:text-amber-400">Target:</span> Score closely aligns within competitive historical cutoff boundaries (&plusmn;15% margin).
                </div>
              </div>
              <div className="flex items-start gap-2">
                <span className="w-2 h-2 rounded-full bg-indigo-500 mt-1 shrink-0" />
                <div>
                  <span className="font-bold text-indigo-600 dark:text-indigo-400">Dream / Reach:</span> Ambitious programs with cutoffs higher than current score; achievable via targeted topic mastery.
                </div>
              </div>
            </div>
          </div>

          {/* Benchmark Transparency & Reliability Label Banner */}
          <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-3 rounded-2xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 text-xs">
            <div className="flex items-center gap-2">
              <Badge variant={simData.benchmark_metadata?.is_verified ? 'success' : 'warning'} size="sm">
                {simData.benchmark_metadata?.label || 'Verified 2024 Cutoff Data'}
              </Badge>
              <span className="text-slate-600 dark:text-slate-300 font-medium">
                Benchmark Year: <span className="font-bold text-slate-900 dark:text-white">{simData.benchmark_metadata?.benchmark_year || 2024}</span>
              </span>
            </div>
            <div className="text-slate-500 dark:text-slate-400">
              <span>Source: </span>
              <span className="font-semibold text-slate-700 dark:text-slate-200">{simData.benchmark_metadata?.data_source}</span>
            </div>
          </div>

          {/* Topic Remediation Impact Banner */}
          {simData.topic_impact && (
            <Card className="p-6 bg-gradient-to-r from-indigo-50 via-white to-purple-50 dark:from-indigo-950/40 dark:via-slate-900 dark:to-purple-950/30 border-indigo-200 dark:border-indigo-800 space-y-3">
              <div className="flex items-center gap-2 text-indigo-900 dark:text-indigo-200">
                <Zap className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                <h3 className="font-bold text-sm">
                  Smart Skill Impact & Cutoff Upgrade Opportunity
                </h3>
              </div>
              <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                {simData.topic_impact.recommendation || simData.topic_impact.message}
              </p>
              {simData.topic_impact.status === 'actionable' && (
                <div className="flex flex-wrap items-center gap-4 pt-1 text-xs">
                  <div className="flex items-center gap-1.5 font-bold text-emerald-600 dark:text-emerald-400">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Projected Percentile Boost: {simData.topic_impact.projected_percentile_gain}</span>
                  </div>
                  {simData.topic_impact.projected_score_gain && (
                    <span className="text-slate-500 dark:text-slate-400 font-medium">
                      Score Gain: {simData.topic_impact.projected_score_gain}
                    </span>
                  )}
                  <Link to="/ai-tutor">
                    <Button size="sm" variant="outline" className="text-xs gap-1 py-1 h-auto">
                      <Bot className="w-3.5 h-3.5" />
                      <span>Practice with AI Tutor</span>
                    </Button>
                  </Link>
                  <Link to="/study-plan">
                    <Button size="sm" variant="outline" className="text-xs gap-1 py-1 h-auto">
                      <CalendarDays className="w-3.5 h-3.5" />
                      <span>Add to Study Plan</span>
                    </Button>
                  </Link>
                </div>
              )}
            </Card>
          )}

          {/* Categorized Tier Navigation Tabs */}
          <div className="space-y-4">
            <div className="flex border-b border-slate-200 dark:border-slate-800 gap-2">
              <button
                type="button"
                onClick={() => setSelectedTier('safe')}
                className={`py-3 px-5 text-sm font-bold border-b-2 transition-all flex items-center gap-2 ${
                  selectedTier === 'safe'
                    ? 'border-emerald-600 text-emerald-600 dark:text-emerald-400'
                    : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
                }`}
              >
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span>Safe Colleges ({safeList.length})</span>
              </button>

              <button
                type="button"
                onClick={() => setSelectedTier('target')}
                className={`py-3 px-5 text-sm font-bold border-b-2 transition-all flex items-center gap-2 ${
                  selectedTier === 'target'
                    ? 'border-amber-600 text-amber-600 dark:text-amber-400'
                    : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
                }`}
              >
                <Target className="w-4 h-4 text-amber-600" />
                <span>Target Colleges ({targetList.length})</span>
              </button>

              <button
                type="button"
                onClick={() => setSelectedTier('reach')}
                className={`py-3 px-5 text-sm font-bold border-b-2 transition-all flex items-center gap-2 ${
                  selectedTier === 'reach'
                    ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
                    : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
                }`}
              >
                <Sparkles className="w-4 h-4 text-indigo-600" />
                <span>Dream / Reach Colleges ({reachList.length})</span>
              </button>
            </div>

            {/* College Cards Grid or Clear Helpful Empty State */}
            {currentList.length === 0 ? (
              <Card className="p-8 text-center space-y-3">
                <div className="w-10 h-10 mx-auto rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-400">
                  <AlertCircle className="w-5 h-5" />
                </div>
                <div className="max-w-md mx-auto space-y-1">
                  <h4 className="font-bold text-sm text-slate-800 dark:text-slate-200">
                    No colleges found in {selectedTier.toUpperCase()} tier
                  </h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                    No programs matched for <span className="font-semibold">{exam}</span> with branch <span className="font-semibold">{branch}</span> in this tier under category <span className="font-semibold">{category}</span>.
                  </p>
                </div>
                <div className="pt-2 flex justify-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setBranch('All')}
                    className="text-xs"
                  >
                    Select All Branches
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setSelectedTier(selectedTier === 'safe' ? 'target' : 'reach')}
                    className="text-xs"
                  >
                    View Other Tiers
                  </Button>
                </div>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {currentList.map((col: any) => (
                  <Card key={col.id} className="p-5 space-y-3.5 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h4 className="font-bold text-slate-900 dark:text-white text-base flex items-center gap-1.5">
                          <Building2 className="w-4 h-4 text-slate-400 shrink-0" />
                          <span>{col.college_name}</span>
                        </h4>
                        <p className="text-xs text-indigo-600 dark:text-indigo-400 font-semibold mt-0.5">
                          {col.branch} ({col.degree})
                        </p>
                      </div>

                      <Badge
                        variant={
                          col.tier === 'safe'
                            ? 'success'
                            : col.tier === 'target'
                            ? 'warning'
                            : 'neutral'
                        }
                        size="sm"
                        className="font-bold shrink-0"
                      >
                        {col.admission_probability}% Chance
                      </Badge>
                    </div>

                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500 dark:text-slate-400">
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5" />
                        <span>{col.location}</span>
                      </span>
                      <span>NIRF #{col.nirf_rank}</span>
                    </div>

                    <div className="pt-2 border-t border-slate-100 dark:border-slate-800 space-y-1 text-[11px] text-slate-400">
                      <div className="flex items-center justify-between">
                        <span className="text-slate-600 dark:text-slate-300 font-medium">
                          Cutoff Comparison: <span className="text-slate-700 dark:text-slate-200">{col.cutoff_comparison || 'Historical Cutoff Standard'}</span>
                        </span>
                        <span className="capitalize font-semibold text-slate-600 dark:text-slate-300">
                          Tier: {col.tier}
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-400">
                        Source: {col.source} ({col.cutoff_year})
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
