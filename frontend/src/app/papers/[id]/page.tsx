'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Paper } from '@/types';
import { papersApi } from '@/lib/api';
import { PaperDetail } from '@/components/papers/PaperDetail';
import { useFavorites } from '@/hooks/useFavorites';

export default function PaperDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [paper, setPaper] = useState<Paper | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isFavorite, toggleFavorite } = useFavorites();

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

  const handleDelete = async () => {
    if (!paper || !confirm('Are you sure you want to delete this paper?')) {
      return;
    }

    try {
      await papersApi.delete(paper.id);
      router.push('/');
      router.refresh();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete paper');
    }
  };

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
    <div className="max-w-4xl mx-auto">
      <PaperDetail
        paper={paper}
        onDelete={handleDelete}
        isFavorite={isFavorite(paper.id)}
        onToggleFavorite={toggleFavorite}
      />
    </div>
  );
}
