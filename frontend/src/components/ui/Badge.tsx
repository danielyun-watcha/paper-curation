'use client';

import { cn } from '@/lib/utils';
import { Category } from '@/types';

const categoryColors: Record<Category, string> = {
  recsys: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  ml: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  nlp: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  cv: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  rl: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  other: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
};

interface BadgeProps {
  category: Category;
  className?: string;
}

export function CategoryBadge({ category, className }: BadgeProps) {
  return (
    <span
      className={cn(
        'px-2 py-1 text-xs font-semibold rounded uppercase',
        categoryColors[category],
        className
      )}
    >
      {category}
    </span>
  );
}
