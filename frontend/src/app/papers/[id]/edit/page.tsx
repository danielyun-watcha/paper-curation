'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Paper } from '@/types';
import { papersApi } from '@/lib/api';
import { PaperForm } from '@/components/papers/PaperForm';

export default function EditPaperPage() {
  const params = useParams();
  const [paper, setPaper] = useState<Paper | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPaper = async () => {
      try {
        const id = params.id as string;
        const data = await papersApi.get(id);
        setPaper(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch paper');
      } finally {
        setLoading(false);
      }
    };

    fetchPaper();
  }, [params.id]);

  if (loading) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 dark:text-gray-400">Loading...</p>
      </div>
    );
  }

  if (error || !paper) {
    return (
      <div className="text-center py-12">
        <p className="text-red-500">{error || 'Paper not found'}</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        Edit Paper
      </h1>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <PaperForm paper={paper} mode="edit" />
      </div>
    </div>
  );
}
