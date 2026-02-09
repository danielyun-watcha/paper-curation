'use client';

import { ButtonHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

interface LoadingButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  isLoading?: boolean;
  loadingText?: string;
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
}

const variantStyles = {
  primary: 'bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-400',
  secondary: 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600',
  danger: 'bg-red-600 text-white hover:bg-red-700',
  ghost: 'bg-transparent hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-200',
};

const sizeStyles = {
  sm: 'px-2 py-1 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
};

/**
 * Button component with built-in loading state and spinner
 */
export const LoadingButton = forwardRef<HTMLButtonElement, LoadingButtonProps>(
  (
    {
      children,
      isLoading = false,
      loadingText,
      variant = 'primary',
      size = 'md',
      className,
      disabled,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          'inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      >
        {isLoading && <Spinner className={size === 'sm' ? 'h-3 w-3' : 'h-4 w-4'} />}
        {isLoading && loadingText ? loadingText : children}
      </button>
    );
  }
);

LoadingButton.displayName = 'LoadingButton';

/**
 * Spinner SVG component
 */
function Spinner({ className }: { className?: string }) {
  return (
    <svg
      className={cn('animate-spin', className)}
      viewBox="0 0 24 24"
      fill="none"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
}

export { Spinner };
