import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { Subject, Course } from '../types';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import {
  Calculator,
  FlaskConical,
  Code2,
  BrainCircuit,
  Search,
  Clock,
  BookOpen,
  ArrowRight
} from 'lucide-react';

export const Subjects: React.FC = () => {
  const [selectedExam, setSelectedExam] = useState<string>('general-learning');
  const [selectedSubject, setSelectedSubject] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const { data: subjectsData, isLoading: loadingSubjects } = useQuery<{ success: boolean; data: Subject[] }>({
    queryKey: ['subjects', selectedExam],
    queryFn: async () => {
      const url = selectedExam === 'general-learning'
        ? '/subjects'
        : `/subjects?exam_slug=${selectedExam}`;
      const res = await api.get(url);
      return res.data;
    },
  });

  const { data: coursesData, isLoading: loadingCourses } = useQuery<{ success: boolean; data: Course[] }>({
    queryKey: ['courses', selectedSubject],
    queryFn: async () => {
      const url = selectedSubject === 'all' ? '/courses' : `/courses?subject_id=${selectedSubject}`;
      const res = await api.get(url);
      return res.data;
    },
  });

  const getSubjectIcon = (slug: string) => {
    switch (slug) {
      case 'mathematics':
        return <Calculator className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />;
      case 'science':
        return <FlaskConical className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />;
      case 'computer-science':
        return <Code2 className="w-5 h-5 text-amber-600 dark:text-amber-400" />;
      case 'logical-reasoning':
        return <BrainCircuit className="w-5 h-5 text-rose-600 dark:text-rose-400" />;
      default:
        return <BookOpen className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />;
    }
  };

  const examSubjectIds = new Set(
    (subjectsData?.data || []).map((subject) => subject.id)
  );

  const filteredCourses = (coursesData?.data || []).filter((c) => {
    const belongsToExam = examSubjectIds.has(c.subject_id);
    const matchesSearch =
      c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (c.description || '').toLowerCase().includes(searchQuery.toLowerCase());

    return belongsToExam && matchesSearch;
  });

  return (
    <div className="space-y-8">
      {/* Header & Search */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200/80 dark:border-slate-800">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 dark:text-white">
            Explore Subjects & Courses
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Choose a subject track and build intuitive mastery through guided problem-solving.
          </p>
        </div>

        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search courses or topics..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 text-sm rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-slate-900 dark:text-slate-100"
          />
        </div>
      </div>

      {/* Exam Category Tabs */}
      <div className="flex flex-wrap items-center gap-3">
        {[
          { id: 'general-learning', label: 'General Learning' },
          { id: 'jee', label: 'IIT JEE' },
          { id: 'neet', label: 'NEET UG' },
        ].map((exam) => (
          <button
            key={exam.id}
            onClick={() => {
              setSelectedExam(exam.id);
              setSelectedSubject('all');
            }}
            className={`px-5 py-3 rounded-xl text-sm font-bold transition-all ${
              selectedExam === exam.id
                ? 'bg-indigo-600 text-white shadow-md'
                : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:border-indigo-400'
            }`}
          >
            {exam.label}
          </button>
        ))}
      </div>

      {/* Category Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 no-scrollbar">
        <button
          onClick={() => setSelectedSubject('all')}
          className={`px-4 py-2 rounded-xl text-xs font-semibold shrink-0 transition-colors ${
            selectedSubject === 'all'
              ? 'bg-indigo-600 text-white'
              : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700/60 border border-slate-200 dark:border-slate-700'
          }`}
        >
          All Subjects
        </button>

        {subjectsData?.data?.map((subject) => (
          <button
            key={subject.id}
            onClick={() => setSelectedSubject(subject.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold shrink-0 transition-colors ${
              selectedSubject === subject.id
                ? 'bg-indigo-600 text-white'
                : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700/60 border border-slate-200 dark:border-slate-700'
            }`}
          >
            {getSubjectIcon(subject.slug)}
            <span>{subject.name}</span>
          </button>
        ))}
      </div>

      {/* Courses Grid */}
      {loadingCourses ? (
        <div className="flex h-64 items-center justify-center">
          <LoadingSpinner size="lg" />
        </div>
      ) : filteredCourses.length === 0 ? (
        <div className="text-center py-16 text-slate-500">
          <p className="text-base font-medium">No courses found matching your search.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCourses.map((course) => (
            <Card key={course.id} hoverEffect className="flex flex-col justify-between space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Badge variant="primary" size="sm">
                    {course.subject_name || 'STEM'}
                  </Badge>
                  <Badge variant="neutral" size="sm">
                    {course.difficulty}
                  </Badge>
                </div>

                <h3 className="font-bold text-lg text-slate-900 dark:text-white leading-snug">
                  {course.title}
                </h3>

                <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 leading-relaxed">
                  {course.description}
                </p>
              </div>

              <div className="pt-4 border-t border-slate-100 dark:border-slate-800 space-y-3">
                <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                  <div className="flex items-center gap-1.5">
                    <BookOpen className="w-3.5 h-3.5" />
                    <span>{course.lesson_count} Lessons</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5" />
                    <span>~{course.estimated_hours} Hours</span>
                  </div>
                </div>

                <Link to={`/courses/${course.id}`} className="block">
                  <Button size="sm" className="w-full gap-2 text-xs">
                    <span>Start Learning</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Button>
                </Link>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
