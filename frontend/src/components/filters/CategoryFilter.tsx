'use client';

import { Category, CATEGORIES } from '@/types';
import { cn } from '@/lib/utils';

interface CategoryFilterProps {
  value: Category | undefined;
  onChange: (value: Category | undefined) => void;
}

export function CategoryFilter({ value, onChange }: CategoryFilterProps) {
  return (
    <div className="flex flex-wrap gap-2">
      <button
        onClick={() => onChange(undefined)}
        className={cn(
          'px-3 py-1 text-sm rounded-full transition-colors',
          !value
            ? 'bg-blue-600 text-white'
            : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600'
        )}
      >
        All
      </button>
      {CATEGORIES.map((cat) => (
        <button
          key={cat.value}
          onClick={() => onChange(cat.value === value ? undefined : cat.value)}
          className={cn(
            'px-3 py-1 text-sm rounded-full transition-colors',
            cat.value === value
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600'
          )}
        >
          {cat.label}
        </button>
      ))}
    </div>
  );
}
