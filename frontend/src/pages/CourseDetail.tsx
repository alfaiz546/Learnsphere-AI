import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import {
  BookOpen,
  Clock,
  CheckCircle2,
  PlayCircle,
  Lock,
  ArrowRight,
  Sparkles
} from 'lucide-react';

export const CourseDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['course', id],
    queryFn: async () => {
      const res = await api.get(`/courses/${id}`);
      return res.data;
    },
  });

  const enrollMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post(`/courses/${id}/enroll`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['course', id] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
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
      <div className="p-8 text-center text-rose-600 font-medium">
        Failed to load course details.
      </div>
    );
  }

  const course = data.data;

  // Find first uncompleted lesson
  let firstLessonId: string | null = null;
  for (const mod of course.modules || []) {
    for (const les of mod.lessons || []) {
      if (les.status !== 'completed' && !firstLessonId) {
        firstLessonId = les.id;
      }
    }
  }
  if (!firstLessonId && course.modules?.[0]?.lessons?.[0]) {
    firstLessonId = course.modules[0].lessons[0].id;
  }

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Course Banner */}
      <Card className="p-8 space-y-6 bg-gradient-to-br from-indigo-950 via-slate-900 to-slate-900 text-white border-indigo-900/60 shadow-xl">
        <div className="flex flex-wrap items-center gap-3">
          <Badge variant="primary" size="sm">
            {course.subject_name || 'STEM'}
          </Badge>
          <Badge variant="neutral" size="sm">
            {course.difficulty}
          </Badge>
          <div className="flex items-center gap-1.5 text-xs text-indigo-300">
            <Clock className="w-3.5 h-3.5" />
            <span>~{course.estimated_hours} Hours Estimated</span>
          </div>
        </div>

        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white mb-3">
            {course.title}
          </h1>
          <p className="text-slate-300 text-sm md:text-base leading-relaxed max-w-3xl">
            {course.description}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-4 pt-2">
          {firstLessonId && (
            <Link to={`/lessons/${firstLessonId}`}>
              <Button size="lg" className="gap-2 shadow-lg shadow-indigo-600/30">
                <PlayCircle className="w-5 h-5" />
                <span>{course.is_enrolled ? 'Resume Learning' : 'Start Course'}</span>
              </Button>
            </Link>
          )}

          {!course.is_enrolled && (
            <Button
              variant="outline"
              size="lg"
              isLoading={enrollMutation.isPending}
              onClick={() => enrollMutation.mutate()}
              className="text-white border-slate-700 hover:bg-slate-800"
            >
              Enroll in Track
            </Button>
          )}
        </div>
      </Card>

      {/* Modules & Lessons Section */}
      <div className="space-y-6">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-indigo-600" />
          <span>Curriculum Modules</span>
        </h2>

        <div className="space-y-4">
          {course.modules?.map((mod: any, mIdx: number) => (
            <Card key={mod.id} className="p-6 space-y-4">
              <div className="border-b border-slate-100 dark:border-slate-800 pb-3">
                <div className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider">
                  Module {mIdx + 1}
                </div>
                <h3 className="text-lg font-bold text-slate-900 dark:text-white mt-0.5">
                  {mod.title}
                </h3>
                {mod.description && (
                  <p className="text-xs text-slate-500 mt-1">{mod.description}</p>
                )}
              </div>

              {/* Lessons List */}
              <div className="space-y-2.5">
                {mod.lessons?.map((lesson: any, lIdx: number) => {
                  const isCompleted = lesson.status === 'completed';

                  return (
                    <Link
                      key={lesson.id}
                      to={`/lessons/${lesson.id}`}
                      className="flex items-center justify-between p-3.5 rounded-xl border border-slate-200/60 dark:border-slate-700/60 bg-slate-50/50 dark:bg-slate-800/40 hover:bg-indigo-50/50 dark:hover:bg-indigo-950/20 hover:border-indigo-300 dark:hover:border-indigo-800 transition-all text-left"
                    >
                      <div className="flex items-center gap-3.5">
                        <div
                          className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
                            isCompleted
                              ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400'
                              : 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-400'
                          }`}
                        >
                          {isCompleted ? (
                            <CheckCircle2 className="w-4 h-4" />
                          ) : (
                            <span className="text-xs font-bold">{lIdx + 1}</span>
                          )}
                        </div>

                        <div>
                          <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                            {lesson.title}
                          </h4>
                          <span className="text-[11px] text-slate-400">
                            ~{lesson.estimated_minutes} min • {lesson.lesson_type}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {isCompleted && (
                          <Badge variant="secondary" size="sm">
                            Completed
                          </Badge>
                        )}
                        <ArrowRight className="w-4 h-4 text-slate-400" />
                      </div>
                    </Link>
                  );
                })}
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};
