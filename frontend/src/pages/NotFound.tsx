import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { ArrowLeft } from 'lucide-react';

export const NotFound: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 text-center">
      <h1 className="text-6xl font-black text-indigo-600 mb-2">404</h1>
      <h2 className="text-xl font-bold text-slate-800 dark:text-slate-200 mb-4">
        Page Not Found
      </h2>
      <p className="text-sm text-slate-500 max-w-sm mb-6">
        The page you are looking for does not exist or has been moved.
      </p>
      <Link to="/dashboard">
        <Button className="gap-2">
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Dashboard</span>
        </Button>
      </Link>
    </div>
  );
};
