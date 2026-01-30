'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  PdfLoader,
  PdfHighlighter as ReactPdfHighlighter,
  Highlight,
  Popup,
  AreaHighlight,
} from 'react-pdf-highlighter';
import type { IHighlight, NewHighlight, Content, ScaledPosition } from 'react-pdf-highlighter';
import 'react-pdf-highlighter/dist/style.css';

// PDF.js worker is managed by react-pdf-highlighter internally

export interface HighlightWithComment extends IHighlight {
  color: string;
  comment: {
    text: string;
    emoji: string;
  };
}

interface PdfHighlighterProps {
  paperId: string;
  pdfUrl: string;
  onHighlightAdd?: (highlight: HighlightWithComment) => void;
  onHighlightDelete?: (highlightId: string) => void;
  highlights: HighlightWithComment[];
  setHighlights: (highlights: HighlightWithComment[]) => void;
}

// Generate unique ID
const getNextId = () => String(Math.random()).slice(2);

// Highlight colors
const HIGHLIGHT_COLORS: Record<string, { background: string; border: string }> = {
  yellow: { background: 'rgba(255, 226, 143, 0.6)', border: '#ffc107' },
  green: { background: 'rgba(134, 239, 172, 0.6)', border: '#22c55e' },
  blue: { background: 'rgba(147, 197, 253, 0.6)', border: '#3b82f6' },
  pink: { background: 'rgba(249, 168, 212, 0.6)', border: '#ec4899' },
  purple: { background: 'rgba(196, 181, 253, 0.6)', border: '#8b5cf6' },
};

// Comment Input Component
function CommentForm({
  onSubmit,
  onCancel,
}: {
  onSubmit: (comment: string, color: string) => void;
  onCancel: () => void;
}) {
  const [comment, setComment] = useState('');
  const [color, setColor] = useState('yellow');
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(comment, color);
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-xl p-3 w-72 border">
      <div className="flex gap-1 mb-2">
        {Object.entries(HIGHLIGHT_COLORS).map(([c, { border }]) => (
          <button
            key={c}
            type="button"
            onClick={() => setColor(c)}
            className={`w-6 h-6 rounded border-2 transition-all ${
              color === c ? 'scale-110 border-gray-800' : 'border-transparent'
            }`}
            style={{ backgroundColor: border }}
          />
        ))}
      </div>
      <textarea
        ref={inputRef}
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        placeholder="Add a comment (optional)..."
        className="w-full px-2 py-1 text-sm border border-gray-300 rounded resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
        rows={2}
      />
      <div className="flex gap-2 mt-2">
        <button
          type="submit"
          className="flex-1 px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Save
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

export function PdfHighlighter({
  paperId,
  pdfUrl,
  highlights,
  setHighlights,
  onHighlightAdd,
  onHighlightDelete,
}: PdfHighlighterProps) {
  const saveHighlights = useCallback((newHighlights: HighlightWithComment[]) => {
    setHighlights(newHighlights);
    localStorage.setItem(`pdf-highlights-${paperId}`, JSON.stringify(newHighlights));
  }, [paperId, setHighlights]);

  const addHighlight = (highlight: NewHighlight, comment: string, color: string) => {
    const newHighlight: HighlightWithComment = {
      ...highlight,
      id: getNextId(),
      color,
      comment: { text: comment, emoji: '' },
    };
    const newHighlights = [...highlights, newHighlight];
    saveHighlights(newHighlights);
    onHighlightAdd?.(newHighlight);
  };

  const updateHighlight = (highlightId: string, position: Partial<ScaledPosition>, content: Partial<Content>) => {
    saveHighlights(
      highlights.map((h) => {
        if (h.id === highlightId) {
          return {
            ...h,
            position: { ...h.position, ...position },
            content: { ...h.content, ...content },
          };
        }
        return h;
      })
    );
  };

  const deleteHighlight = (highlightId: string) => {
    saveHighlights(highlights.filter((h) => h.id !== highlightId));
    onHighlightDelete?.(highlightId);
  };

  const scrollToHighlight = (highlightId: string) => {
    const highlightElement = document.querySelector(`[data-highlight-id="${highlightId}"]`);
    highlightElement?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  };

  return (
    <div className="h-full flex flex-col">
      {/* Info bar */}
      <div className="flex items-center gap-2 px-3 py-2 bg-gray-100 dark:bg-gray-700 border-b text-sm text-gray-600 dark:text-gray-300">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>Select text to highlight and add comments</span>
        <span className="ml-auto text-xs text-gray-500">{highlights.length} highlights</span>
      </div>

      {/* PDF Viewer */}
      <div className="flex-1 relative overflow-hidden">
        <PdfLoader url={pdfUrl} beforeLoad={<div className="p-4 text-center">Loading PDF...</div>}>
          {(pdfDocument) => (
            <ReactPdfHighlighter
              pdfDocument={pdfDocument}
              enableAreaSelection={(event) => event.altKey}
              onScrollChange={() => {}}
              scrollRef={() => {}}
              onSelectionFinished={(
                position,
                content,
                hideTipAndSelection,
                transformSelection
              ) => (
                <CommentForm
                  onSubmit={(comment, color) => {
                    addHighlight({ content, position, comment: { text: '', emoji: '' } }, comment, color);
                    hideTipAndSelection();
                  }}
                  onCancel={hideTipAndSelection}
                />
              )}
              highlightTransform={(
                highlight,
                index,
                setTip,
                hideTip,
                viewportToScaled,
                screenshot,
                isScrolledTo
              ) => {
                const h = highlight as HighlightWithComment;
                const color = h.color || 'yellow';
                const colorStyle = HIGHLIGHT_COLORS[color] || HIGHLIGHT_COLORS.yellow;

                const isTextHighlight = !highlight.content?.image;

                const component = isTextHighlight ? (
                  <Highlight
                    isScrolledTo={isScrolledTo}
                    position={highlight.position}
                    comment={highlight.comment}
                    style={{
                      background: colorStyle.background,
                    }}
                  />
                ) : (
                  <AreaHighlight
                    isScrolledTo={isScrolledTo}
                    highlight={highlight}
                    onChange={(boundingRect) => {
                      updateHighlight(
                        highlight.id,
                        { boundingRect: viewportToScaled(boundingRect) },
                        { image: screenshot(boundingRect) }
                      );
                    }}
                  />
                );

                return (
                  <Popup
                    popupContent={
                      <div className="bg-white rounded-lg shadow-lg p-3 max-w-xs border">
                        <div className="flex items-start gap-2 mb-2">
                          <span
                            className="w-3 h-3 rounded flex-shrink-0 mt-1"
                            style={{ backgroundColor: colorStyle.border }}
                          />
                          <p className="text-sm text-gray-700 break-words">
                            &ldquo;{highlight.content.text?.slice(0, 100)}{highlight.content.text && highlight.content.text.length > 100 ? '...' : ''}&rdquo;
                          </p>
                        </div>
                        {h.comment?.text && (
                          <p className="text-sm text-gray-600 bg-gray-50 p-2 rounded mb-2">
                            {h.comment.text}
                          </p>
                        )}
                        <button
                          onClick={() => {
                            deleteHighlight(highlight.id);
                            hideTip();
                          }}
                          className="text-xs text-red-500 hover:text-red-700"
                        >
                          Delete highlight
                        </button>
                      </div>
                    }
                    onMouseOver={(popupContent) => setTip(highlight, () => popupContent)}
                    onMouseOut={hideTip}
                    key={index}
                  >
                    {component}
                  </Popup>
                );
              }}
              highlights={highlights}
            />
          )}
        </PdfLoader>
      </div>
    </div>
  );
}
