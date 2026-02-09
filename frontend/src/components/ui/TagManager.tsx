'use client';

import { useState, useCallback } from 'react';
import { Tag } from './Tag';

interface TagManagerProps {
  tags: string[];
  onTagsChange: (tags: string[]) => void;
  label?: string;
  placeholder?: string;
  className?: string;
}

/**
 * Reusable tag management component with input, add button, and tag list.
 * Handles add/remove logic internally and notifies parent via onTagsChange.
 */
export function TagManager({
  tags,
  onTagsChange,
  label = 'Tags',
  placeholder = 'Add tag and press Enter',
  className = '',
}: TagManagerProps) {
  const [tagInput, setTagInput] = useState('');

  const addTag = useCallback(() => {
    const tag = tagInput.trim().toLowerCase();
    if (tag && !tags.includes(tag)) {
      onTagsChange([...tags, tag]);
    }
    setTagInput('');
  }, [tagInput, tags, onTagsChange]);

  const removeTag = useCallback(
    (tagToRemove: string) => {
      onTagsChange(tags.filter((t) => t !== tagToRemove));
    },
    [tags, onTagsChange]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        addTag();
      }
    },
    [addTag]
  );

  return (
    <div className={className}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          {label}
        </label>
      )}
      <div className="flex gap-2 mb-2">
        <input
          type="text"
          value={tagInput}
          onChange={(e) => setTagInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="button"
          onClick={addTag}
          className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-300 dark:hover:bg-gray-600"
        >
          Add
        </button>
      </div>
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {tags.map((tag) => (
            <Tag key={tag} name={tag} onRemove={() => removeTag(tag)} />
          ))}
        </div>
      )}
    </div>
  );
}
