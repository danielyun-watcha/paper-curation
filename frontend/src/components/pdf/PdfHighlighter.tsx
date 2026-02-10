'use client';

import { useState, useEffect, useCallback, useRef, Component, ReactNode } from 'react';
import {
  PdfLoader,
  PdfHighlighter as ReactPdfHighlighter,
  Highlight,
  Popup,
  AreaHighlight,
} from 'react-pdf-highlighter';
import type { IHighlight, NewHighlight, Content, ScaledPosition } from 'react-pdf-highlighter';
import 'react-pdf-highlighter/dist/style.css';

// Suppress PDF.js annotation editor errors (known issue with pdfjs-dist)
if (typeof window !== 'undefined') {
  const originalError = console.error;
  console.error = (...args) => {
    const msg = args[0]?.toString?.() || '';
    if (msg.includes('#editorTypes') || msg.includes('is not iterable')) {
      return; // Suppress this specific error
    }
    originalError.apply(console, args);
  };

  // Also suppress unhandled errors from PDF.js
  window.addEventListener('error', (event) => {
    if (event.message?.includes('#editorTypes') || event.message?.includes('is not iterable')) {
      event.preventDefault();
      event.stopPropagation();
      return false;
    }
  });
}

// Error boundary for PDF viewer
class PdfErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean }> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error) {
    // Ignore PDF.js annotation editor errors
    if (error.message?.includes('#editorTypes')) {
      this.setState({ hasError: false });
      return;
    }
    console.error('PDF Error:', error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 text-center text-red-500">
          PDF 로딩 중 오류가 발생했습니다. 새로고침해주세요.
        </div>
      );
    }
    return this.props.children;
  }
}

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

// Comment Input Component with Translation
function CommentForm({
  onSubmit,
  onCancel,
  selectedText,
}: {
  onSubmit: (comment: string, color: string) => void;
  onCancel: () => void;
  selectedText?: string;
}) {
  const [comment, setComment] = useState('');
  const [color, setColor] = useState('yellow');
  const [translating, setTranslating] = useState(false);
  const [translation, setTranslation] = useState<string | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(comment, color);
  };

  const handleTranslate = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    console.log('Translate clicked, selectedText:', selectedText);

    if (!selectedText?.trim() || translating) {
      console.log('No text to translate or already translating');
      setTranslation('[선택된 텍스트가 없습니다]');
      return;
    }

    setTranslating(true);
    setTranslation(null);

    try {
      const apiUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/papers/translate-text`;
      console.log('Calling translate API:', apiUrl);

      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: selectedText }),
      });

      console.log('API response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Translation API error:', response.status, errorText);
        throw new Error('Translation failed');
      }

      const data = await response.json();
      console.log('Translation result:', data);
      setTranslation(data.translated);
    } catch (err) {
      console.error('Translation error:', err);
      setTranslation('[번역 실패]');
    } finally {
      setTranslating(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-xl p-3 w-80 border max-h-96 overflow-y-auto">
      {/* Translation Section */}
      {selectedText && (
        <div className="mb-3 pb-3 border-b border-gray-200">
          <button
            type="button"
            onClick={handleTranslate}
            disabled={translating}
            className="w-full px-3 py-2 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400 flex items-center justify-center gap-2"
          >
            {translating ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                번역 중...
              </>
            ) : (
              <>
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                </svg>
                번역하기
              </>
            )}
          </button>
          {translation && (
            <div className="mt-2 p-2 bg-green-50 rounded text-sm text-gray-700 whitespace-pre-wrap">
              {translation}
            </div>
          )}
        </div>
      )}

      {/* Highlight Section */}
      <form onSubmit={handleSubmit}>
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
            Highlight
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
    </div>
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
  const [scale, setScale] = useState(1.0);
  const scrollToRef = useRef<((highlight: { pageNumber: number; top?: number }) => void) | null>(null);
  const hasScrolledRef = useRef(false);

  const zoomIn = () => setScale((s) => Math.min(s + 0.2, 3.0));
  const zoomOut = () => setScale((s) => Math.max(s - 0.2, 0.6));
  const resetZoom = () => setScale(1.0);

  // Reset scroll flag when PDF URL changes
  useEffect(() => {
    hasScrolledRef.current = false;
  }, [pdfUrl]);

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

  // Scroll to highlight - exported for external use
  const _scrollToHighlight = useCallback((highlightId: string) => {
    const highlightElement = document.querySelector(`[data-highlight-id="${highlightId}"]`);
    highlightElement?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, []);

  // Expose scroll function via window for external access (e.g., highlight list sidebar)
  useEffect(() => {
    (window as unknown as { scrollToHighlight?: typeof _scrollToHighlight }).scrollToHighlight = _scrollToHighlight;
    return () => {
      delete (window as unknown as { scrollToHighlight?: typeof _scrollToHighlight }).scrollToHighlight;
    };
  }, [_scrollToHighlight]);

  return (
    <div className="h-full flex flex-col">
      {/* Info bar with zoom controls */}
      <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 dark:bg-gray-700 border-b text-sm text-gray-600 dark:text-gray-300">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span className="text-xs">Select text to highlight</span>

        {/* Zoom controls */}
        <div className="ml-auto flex items-center gap-1">
          <button
            onClick={zoomOut}
            className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
            title="Zoom out"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
            </svg>
          </button>
          <button
            onClick={resetZoom}
            className="px-2 py-0.5 text-xs hover:bg-gray-200 dark:hover:bg-gray-600 rounded min-w-[50px]"
            title="Reset zoom"
          >
            {Math.round(scale * 100)}%
          </button>
          <button
            onClick={zoomIn}
            className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
            title="Zoom in"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </button>
          <span className="ml-2 text-xs text-gray-500">{highlights.length} highlights</span>
        </div>
      </div>

      {/* PDF Viewer */}
      <div className="flex-1 relative overflow-auto">
        <PdfErrorBoundary>
        <PdfLoader key={`pdf-${scale}`} url={pdfUrl} beforeLoad={<div className="p-4 text-center">Loading PDF...</div>}>
          {(pdfDocument) => (
            <ReactPdfHighlighter
              pdfDocument={pdfDocument}
              pdfScaleValue={String(scale)}
              enableAreaSelection={(event) => event.altKey}
              onScrollChange={() => {}}
              scrollRef={(scrollTo) => {
                scrollToRef.current = scrollTo;
                // Scroll to top on initial load (only once per PDF)
                if (!hasScrolledRef.current) {
                  hasScrolledRef.current = true;
                  setTimeout(() => scrollTo({ pageNumber: 1, top: 0 }), 150);
                }
              }}
              // eslint-disable-next-line @typescript-eslint/no-unused-vars
              onSelectionFinished={(position, content, hideTipAndSelection, transformSelection) => (
                <CommentForm
                  onSubmit={(comment, color) => {
                    addHighlight({ content, position, comment: { text: '', emoji: '' } }, comment, color);
                    hideTipAndSelection();
                  }}
                  onCancel={hideTipAndSelection}
                  selectedText={content.text}
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
        </PdfErrorBoundary>
      </div>
    </div>
  );
}
