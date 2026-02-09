'use client';

import { useMemo } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';

interface LatexTextProps {
  text: string;
  className?: string;
}

/**
 * Component that renders text with LaTeX equations.
 * Supports inline math ($...$, \(...\)) and display math ($$...$$, \[...\])
 */
export function LatexText({ text, className = '' }: LatexTextProps) {
  const renderedContent = useMemo(() => {
    if (!text) return '';

    // Patterns for LaTeX:
    // 1. Display math: $$...$$ or \[...\]
    // 2. Inline math: $...$ or \(...\)

    const parts: { type: 'text' | 'inline' | 'display'; content: string }[] = [];

    // Combined regex to match all LaTeX patterns
    // Order matters: check display math first ($$) before inline ($)
    const latexRegex = /(\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\]|\$[^$\n]+?\$|\\\([\s\S]*?\\\))/g;

    let lastIndex = 0;
    let match;

    while ((match = latexRegex.exec(text)) !== null) {
      // Add text before the match
      if (match.index > lastIndex) {
        parts.push({
          type: 'text',
          content: text.slice(lastIndex, match.index)
        });
      }

      const matched = match[0];
      let latex: string;
      let type: 'inline' | 'display';

      if (matched.startsWith('$$') && matched.endsWith('$$')) {
        latex = matched.slice(2, -2);
        type = 'display';
      } else if (matched.startsWith('\\[') && matched.endsWith('\\]')) {
        latex = matched.slice(2, -2);
        type = 'display';
      } else if (matched.startsWith('$') && matched.endsWith('$')) {
        latex = matched.slice(1, -1);
        type = 'inline';
      } else if (matched.startsWith('\\(') && matched.endsWith('\\)')) {
        latex = matched.slice(2, -2);
        type = 'inline';
      } else {
        // Shouldn't happen, but fallback
        parts.push({ type: 'text', content: matched });
        lastIndex = match.index + matched.length;
        continue;
      }

      parts.push({ type, content: latex });
      lastIndex = match.index + matched.length;
    }

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push({
        type: 'text',
        content: text.slice(lastIndex)
      });
    }

    return parts;
  }, [text]);

  if (!renderedContent || renderedContent.length === 0) {
    return <span className={className}>{text}</span>;
  }

  return (
    <span className={className}>
      {renderedContent.map((part, index) => {
        if (part.type === 'text') {
          return <span key={index}>{part.content}</span>;
        }

        try {
          const html = katex.renderToString(part.content, {
            throwOnError: false,
            displayMode: part.type === 'display',
            output: 'html',
          });

          if (part.type === 'display') {
            return (
              <span
                key={index}
                className="block my-2 text-center overflow-x-auto"
                dangerouslySetInnerHTML={{ __html: html }}
              />
            );
          }

          return (
            <span
              key={index}
              dangerouslySetInnerHTML={{ __html: html }}
            />
          );
        } catch (e) {
          // If KaTeX fails, show the original text
          console.warn('KaTeX render error:', e);
          return <span key={index}>{part.type === 'display' ? `$$${part.content}$$` : `$${part.content}$`}</span>;
        }
      })}
    </span>
  );
}
