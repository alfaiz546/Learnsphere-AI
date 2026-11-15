import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '../services/api';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Alert } from '../components/ui/Alert';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { ShieldAlert, Plus, BookOpen, Layers, CheckCircle2 } from 'lucide-react';

export const Admin: React.FC = () => {
  const [subjectName, setSubjectName] = useState('');
  const [subjectSlug, setSubjectSlug] = useState('');
  const [subjectDesc, setSubjectDesc] = useState('');

  const [courseTitle, setCourseTitle] = useState('');
  const [courseSlug, setCourseSlug] = useState('');
  const [courseSubjectId, setCourseSubjectId] = useState('');
  const [courseHours, setCourseHours] = useState('8.0');

  const [feedback, setFeedback] = useState<string | null>(null);

  // Fetch admin stats
  const { data: statsData, isLoading: loadingStats } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: async () => {
      const res = await api.get('/admin/stats');
      return res.data;
    },
  });

  // Fetch subjects for course creation dropdown
  const { data: subjectsData } = useQuery({
    queryKey: ['admin-subjects'],
    queryFn: async () => {
      const res = await api.get('/subjects');
      return res.data;
    },
  });

  const createSubjectMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post('/admin/subjects', {
        name: subjectName,
        slug: subjectSlug,
        description: subjectDesc,
        icon: 'book',
        color: '#6366f1',
      });
      return res.data;
    },
    onSuccess: () => {
      setFeedback('Subject created successfully!');
      setSubjectName('');
      setSubjectSlug('');
      setSubjectDesc('');
    },
  });

  const createCourseMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post('/admin/courses', {
        subject_id: courseSubjectId,
        title: courseTitle,
        slug: courseSlug,
        difficulty: 'beginner',
        estimated_hours: parseFloat(courseHours) || 8.0,
      });
      return res.data;
    },
    onSuccess: () => {
      setFeedback('Course created successfully!');
      setCourseTitle('');
      setCourseSlug('');
      setCourseHours('8.0');
    },
  });

  if (loadingStats) {
    return (
      <div className="flex h-96 items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const stats = statsData?.data || {
    total_users: 0,
    total_courses: 0,
    total_lessons: 0,
    total_assessments: 0,
    total_completions: 0,
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2.5">
          <ShieldAlert className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
          <span>Admin Content Management System</span>
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Add new subjects, courses, and review real-time platform statistics.
        </p>
      </div>

      {feedback && (
        <Alert type="success">{feedback}</Alert>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="text-2xl font-black text-indigo-600">{stats.total_users}</div>
          <div className="text-xs text-slate-500">Registered Students</div>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-black text-emerald-600">{stats.total_courses}</div>
          <div className="text-xs text-slate-500">Active Courses</div>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-black text-amber-600">{stats.total_lessons}</div>
          <div className="text-xs text-slate-500">Curated Lessons</div>
        </Card>
        <Card className="p-4">
          <div className="text-2xl font-black text-rose-600">{stats.total_assessments}</div>
          <div className="text-xs text-slate-500">Assessments Taken</div>
        </Card>
      </div>

      {/* Forms Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Create Subject */}
        <Card className="p-6 space-y-4">
          <h3 className="font-bold text-base text-slate-900 dark:text-white pb-2 border-b border-slate-100 dark:border-slate-800 flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-indigo-600" />
            <span>Create New Subject</span>
          </h3>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              createSubjectMutation.mutate();
            }}
            className="space-y-3.5"
          >
            <Input
              label="Subject Name"
              required
              placeholder="e.g. Neuroscience"
              value={subjectName}
              onChange={(e) => setSubjectName(e.target.value)}
            />
            <Input
              label="Slug"
              required
              placeholder="e.g. neuroscience"
              value={subjectSlug}
              onChange={(e) => setSubjectSlug(e.target.value)}
            />
            <Input
              label="Description"
              placeholder="Brief description..."
              value={subjectDesc}
              onChange={(e) => setSubjectDesc(e.target.value)}
            />
            <Button
              type="submit"
              size="sm"
              isLoading={createSubjectMutation.isPending}
              className="gap-2"
            >
              <Plus className="w-4 h-4" />
              <span>Add Subject</span>
            </Button>
          </form>
        </Card>

        {/* Create Course */}
        <Card className="p-6 space-y-4">
          <h3 className="font-bold text-base text-slate-900 dark:text-white pb-2 border-b border-slate-100 dark:border-slate-800 flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-600" />
            <span>Create New Course</span>
          </h3>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              createCourseMutation.mutate();
            }}
            className="space-y-3.5"
          >
            <div className="space-y-1">
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                Select Subject
              </label>
              <select
                required
                value={courseSubjectId}
                onChange={(e) => setCourseSubjectId(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
              >
                <option value="">-- Choose Subject --</option>
                {subjectsData?.data?.map((s: any) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>

            <Input
              label="Course Title"
              required
              placeholder="e.g. Brain Networks"
              value={courseTitle}
              onChange={(e) => setCourseTitle(e.target.value)}
            />
            <Input
              label="Slug"
              required
              placeholder="e.g. brain-networks"
              value={courseSlug}
              onChange={(e) => setCourseSlug(e.target.value)}
            />
            <Input
              label="Estimated Hours"
              type="number"
              step="0.5"
              value={courseHours}
              onChange={(e) => setCourseHours(e.target.value)}
            />
            <Button
              type="submit"
              size="sm"
              isLoading={createCourseMutation.isPending}
              className="gap-2"
            >
              <Plus className="w-4 h-4" />
              <span>Add Course</span>
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
};
