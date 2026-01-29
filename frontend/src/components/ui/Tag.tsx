'use client';

import { cn } from '@/lib/utils';

interface TagProps {
  name: string;
  onClick?: () => void;
  onRemove?: () => void;
  className?: string;
}

export function Tag({ name, onClick, onRemove, className }: TagProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full',
        'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
        onClick && 'cursor-pointer hover:bg-blue-200 dark:hover:bg-blue-800',
        className
      )}
      onClick={onClick}
    >
      {name}
      {onRemove && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          className="ml-1 hover:text-blue-600 dark:hover:text-blue-300"
        >
          &times;
        </button>
      )}
    </span>
  );
}
