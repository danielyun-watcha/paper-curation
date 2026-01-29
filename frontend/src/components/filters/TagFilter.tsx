'use client';

import { TagWithCount } from '@/types';
import { cn } from '@/lib/utils';

interface TagFilterProps {
  tags: TagWithCount[];
  selectedTags: string[];
  onChange: (tags: string[]) => void;
}

export function TagFilter({ tags, selectedTags, onChange }: TagFilterProps) {
  const toggleTag = (tagName: string) => {
    if (selectedTags.includes(tagName)) {
      onChange(selectedTags.filter((t) => t !== tagName));
    } else {
      onChange([...selectedTags, tagName]);
    }
  };

  if (tags.length === 0) {
    return (
      <p className="text-sm text-gray-500 dark:text-gray-400">No tags yet</p>
    );
  }

  return (
    <div className="flex flex-wrap gap-2">
      {tags.map((tag) => (
        <button
          key={tag.id}
          onClick={() => toggleTag(tag.name)}
          className={cn(
            'px-3 py-1 text-sm rounded-full transition-colors',
            selectedTags.includes(tag.name)
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600'
          )}
        >
          {tag.name} ({tag.paper_count})
        </button>
      ))}
    </div>
  );
}
