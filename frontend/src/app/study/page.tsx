'use client';

import { useState, useEffect, lazy, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Paper } from '@/types';
import { papersApi } from '@/lib/api';
import type { HighlightWithComment } from '@/components/pdf/PdfHighlighter';
import { LatexText } from '@/components/LatexText';

// Dynamically import to avoid SSR issues with PDF.js
const PdfHighlighter = lazy(() => import('@/components/pdf/PdfHighlighter').then(m => ({ default: m.PdfHighlighter })));

// Highlight colors
const HIGHLIGHT_COLORS: Record<string, { background: string; border: string }> = {
  yellow: { background: 'bg-yellow-100', border: 'border-yellow-400' },
  green: { background: 'bg-green-100', border: 'border-green-400' },
  blue: { background: 'bg-blue-100', border: 'border-blue-400' },
  pink: { background: 'bg-pink-100', border: 'border-pink-400' },
  purple: { background: 'bg-purple-100', border: 'border-purple-400' },
};

export default function StudyPage() {
  return (
    <Suspense fallback={<StudyPageLoading />}>
      <StudyPageContent />
    </Suspense>
  );
}

function StudyPageLoading() {
  return (
    <div className="h-[calc(100vh-130px)] flex items-center justify-center">
      <div className="text-gray-500">Loading...</div>
    </div>
  );
}

function StudyPageContent() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedPaperId, setSelectedPaperId] = useState<string>('');
  const [loadingPapers, setLoadingPapers] = useState(true);

  // Full paper processing states
  const [fullSummarizing, setFullSummarizing] = useState(false);
  const [fullSummarized, setFullSummarized] = useState(false);
  const [fullSummary, setFullSummary] = useState<string | null>(null);

  // Highlights
  const [highlights, setHighlights] = useState<HighlightWithComment[]>([]);

  // Right panel (Summary + Highlights)
  const [showRightPanel, setShowRightPanel] = useState(false);

  // Collapsible panels
  const [showSummaryContent, setShowSummaryContent] = useState(true);
  const [showHighlightsContent, setShowHighlightsContent] = useState(true);

  // Save notification
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  // URL search params
  const searchParams = useSearchParams();
  const urlPaperId = searchParams.get('paper');

  // Helper function to load paper data
  const loadPaperData = (paper: Paper, paperId: string) => {
    setSelectedPaperId(paperId);

    // Load highlights from localStorage
    const savedHighlights = localStorage.getItem(`pdf-highlights-${paperId}`);
    if (savedHighlights) {
      setHighlights(JSON.parse(savedHighlights));
    } else {
      setHighlights([]);
    }

    // Load summary from localStorage (per-browser storage)
    const savedSummary = localStorage.getItem(`pdf-summary-${paperId}`);
    if (savedSummary) {
      setFullSummary(savedSummary);
      setFullSummarized(true);
      setShowRightPanel(true);
    } else {
      setFullSummary(null);
      setFullSummarized(false);
    }
  };

  // Load papers and restore session
  useEffect(() => {
    const fetchPapers = async () => {
      try {
        const response = await papersApi.list({ limit: 100 });
        setPapers(response.items);

        // Priority 1: Check URL parameter
        if (urlPaperId) {
          const paper = response.items.find((p: Paper) => p.id === urlPaperId);
          if (paper) {
            loadPaperData(paper, urlPaperId);
            setLoadingPapers(false);
            return;
          }
        }

        // Priority 2: Restore from localStorage
        const lastSession = localStorage.getItem('study-session');
        if (lastSession) {
          const session = JSON.parse(lastSession);
          if (session.paperId) {
            const paper = response.items.find((p: Paper) => p.id === session.paperId);
            if (paper) {
              loadPaperData(paper, session.paperId);
              setShowRightPanel(session.showRightPanel || (paper.full_summary ? true : false));
            }
          }
        }
      } catch (err) {
        console.error('Failed to fetch papers:', err);
      } finally {
        setLoadingPapers(false);
      }
    };
    fetchPapers();
  }, [urlPaperId]);

  // Save study session
  const saveStudySession = () => {
    if (!selectedPaperId) return;

    const session = {
      paperId: selectedPaperId,
      showRightPanel,
      savedAt: new Date().toISOString(),
    };

    localStorage.setItem('study-session', JSON.stringify(session));

    // Show save message
    setSaveMessage('저장되었습니다!');
    setTimeout(() => setSaveMessage(null), 2000);
  };

  const selectedPaper = papers.find(p => p.id === selectedPaperId);

  const hasPdfSource = (paper: Paper): boolean => {
    return !!(paper.arxiv_id || paper.pdf_path);
  };

  const getPdfUrl = (paper: Paper): string | null => {
    if (paper.pdf_path) {
      return `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/papers/${paper.id}/pdf-file`;
    }
    if (paper.arxiv_id) {
      return `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/papers/${paper.id}/pdf`;
    }
    return null;
  };

  const handlePaperSelect = (paperId: string) => {
    setSelectedPaperId(paperId);

    // Load summary from localStorage (per-browser storage)
    const savedSummary = localStorage.getItem(`pdf-summary-${paperId}`);
    if (savedSummary) {
      setFullSummary(savedSummary);
      setFullSummarized(true);
      setShowRightPanel(true);
    } else {
      setFullSummary(null);
      setFullSummarized(false);
    }

    setFullSummarizing(false);
    setShowSummaryContent(true);
    setShowHighlightsContent(true);

    // Load highlights from localStorage
    const savedHighlights = localStorage.getItem(`pdf-highlights-${paperId}`);
    if (savedHighlights) {
      setHighlights(JSON.parse(savedHighlights));
    } else {
      setHighlights([]);
    }
  };

  const handleFullSummarize = async () => {
    if (!selectedPaperId) return;
    setFullSummarizing(true);
    setFullSummarized(false);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/papers/${selectedPaperId}/summarize-full`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Summary failed');
      const data = await response.json();
      setFullSummary(data.summary);
      setFullSummarized(true);
      setShowRightPanel(true);
      // Save summary to localStorage (per-browser storage)
      localStorage.setItem(`pdf-summary-${selectedPaperId}`, data.summary);
    } catch (err) {
      console.error('Full summary error:', err);
      setFullSummarized(false);
    } finally {
      setFullSummarizing(false);
    }
  };

  const deleteHighlight = (highlightId: string) => {
    const newHighlights = highlights.filter(h => h.id !== highlightId);
    setHighlights(newHighlights);
    localStorage.setItem(`pdf-highlights-${selectedPaperId}`, JSON.stringify(newHighlights));
  };

  const pdfUrl = selectedPaper ? getPdfUrl(selectedPaper) : null;

  return (
    <div className="h-[calc(100vh-100px)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-2 flex-shrink-0">
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">
          Study
        </h1>
        <div className="flex items-center gap-2">
          {loadingPapers ? (
            <span className="text-gray-500">Loading papers...</span>
          ) : (
            <>
              <select
                value={selectedPaperId}
                onChange={(e) => handlePaperSelect(e.target.value)}
                className="w-72 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md
                         bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                         focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Select a paper --</option>
                {papers.map((paper) => (
                  <option key={paper.id} value={paper.id}>
                    {paper.title.length > 40 ? paper.title.substring(0, 40) + '...' : paper.title}
                  </option>
                ))}
              </select>

              {selectedPaper && (
                <>
                  <button
                    onClick={handleFullSummarize}
                    disabled={fullSummarizing || !selectedPaper || !hasPdfSource(selectedPaper)}
                    className="px-3 py-2 text-sm bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center gap-1"
                    title="Summarize full paper"
                  >
                    {fullSummarizing ? (
                      <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                    ) : fullSummarized ? (
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    ) : (
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    )}
                    Summary
                  </button>

                  <button
                    onClick={() => setShowRightPanel(!showRightPanel)}
                    className={`px-3 py-2 text-sm rounded-md transition-colors flex items-center gap-1 ${
                      showRightPanel
                        ? 'bg-emerald-500 text-white'
                        : 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'
                    }`}
                    title="Toggle notes panel"
                  >
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                    Notes {(fullSummary || highlights.length > 0) && `(${(fullSummary ? 1 : 0) + highlights.length})`}
                  </button>

                  {/* Save Button */}
                  <div className="relative">
                    <button
                      onClick={saveStudySession}
                      className="px-3 py-2 text-sm bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors flex items-center gap-1"
                      title="Save study session"
                    >
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                      </svg>
                      Save
                    </button>
                    {saveMessage && (
                      <div className="absolute top-full mt-1 left-1/2 -translate-x-1/2 px-3 py-1 bg-green-600 text-white text-xs rounded shadow-lg whitespace-nowrap z-50">
                        {saveMessage}
                      </div>
                    )}
                  </div>
                </>
              )}
            </>
          )}
        </div>
      </div>

      {/* Main Content */}
      {selectedPaper ? (
        <div className="flex-1 flex gap-4 min-h-0">
          {/* PDF Viewer with Highlighter */}
          <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden flex-1 ${
            showRightPanel ? '' : 'w-full'
          }`}>
            {hasPdfSource(selectedPaper) ? (
              <Suspense fallback={<div className="p-4 text-center">Loading PDF viewer...</div>}>
                <PdfHighlighter
                  paperId={selectedPaperId}
                  pdfUrl={pdfUrl!}
                  highlights={highlights}
                  setHighlights={setHighlights}
                />
              </Suspense>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
                <div className="text-center max-w-md">
                  <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                  <p className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Study를 진행할 수 없습니다
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    현재 arXiv 버전이 없는 논문은 Study 기능을 이용할 수 없습니다.
                    추후 업데이트를 통해 지원할 예정입니다.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Right Panel - Summary + Highlights */}
          {showRightPanel && (
            <div className="w-96 bg-white dark:bg-gray-800 rounded-lg shadow-md flex flex-col overflow-hidden">
              <div className="p-3 border-b border-gray-200 dark:border-gray-700">
                <h3 className="font-bold text-gray-900 dark:text-white">Notes</h3>
              </div>
              <div className="flex-1 overflow-y-auto p-3 space-y-3">
                {/* Summary Section */}
                {fullSummary && (
                  <div className="border border-purple-200 dark:border-purple-800 rounded overflow-hidden">
                    <button
                      onClick={() => setShowSummaryContent(!showSummaryContent)}
                      className="w-full flex items-center justify-between p-3 bg-purple-50 dark:bg-purple-900/20 hover:bg-purple-100 dark:hover:bg-purple-900/30 transition-colors"
                    >
                      <h4 className="text-sm font-medium text-purple-700 dark:text-purple-400 flex items-center gap-2">
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        Summary
                      </h4>
                      <svg
                        className={`w-4 h-4 text-purple-600 transition-transform ${showSummaryContent ? 'rotate-180' : ''}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                    {showSummaryContent && (
                      <div className="p-3 bg-white dark:bg-gray-800 border-t border-purple-200 dark:border-purple-800">
                        <div className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                          <LatexText text={fullSummary} />
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Highlights Section */}
                <div className="border border-yellow-200 dark:border-yellow-800 rounded overflow-hidden">
                  <button
                    onClick={() => setShowHighlightsContent(!showHighlightsContent)}
                    className="w-full flex items-center justify-between p-3 bg-yellow-50 dark:bg-yellow-900/20 hover:bg-yellow-100 dark:hover:bg-yellow-900/30 transition-colors"
                  >
                    <h4 className="text-sm font-medium text-yellow-700 dark:text-yellow-400 flex items-center gap-2">
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                      Highlights & Comments {highlights.length > 0 && `(${highlights.length})`}
                    </h4>
                    <svg
                      className={`w-4 h-4 text-yellow-600 transition-transform ${showHighlightsContent ? 'rotate-180' : ''}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  {showHighlightsContent && (
                    <div className="p-3 bg-white dark:bg-gray-800 border-t border-yellow-200 dark:border-yellow-800 space-y-2">
                      {highlights.length === 0 ? (
                        <p className="text-gray-500 dark:text-gray-400 text-sm text-center py-2">
                          Select text in PDF to highlight
                        </p>
                      ) : (
                        highlights.map((highlight) => {
                          const colorClasses = HIGHLIGHT_COLORS[highlight.color] || HIGHLIGHT_COLORS.yellow;
                          return (
                            <div
                              key={highlight.id}
                              className={`p-2 rounded border-l-4 ${colorClasses.background} ${colorClasses.border} relative group cursor-pointer hover:shadow-md transition-shadow`}
                            >
                              <div className="flex items-start justify-between gap-2">
                                <p className="text-xs text-gray-700 dark:text-gray-800 italic">
                                  &ldquo;{highlight.content.text?.slice(0, 100)}{highlight.content.text && highlight.content.text.length > 100 ? '...' : ''}&rdquo;
                                </p>
                                <button
                                  onClick={() => deleteHighlight(highlight.id)}
                                  className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-opacity flex-shrink-0"
                                >
                                  <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                  </svg>
                                </button>
                              </div>
                              {highlight.comment?.text && (
                                <div className="mt-1 pt-1 border-t border-gray-200">
                                  <p className="text-xs text-gray-600 dark:text-gray-700">
                                    {highlight.comment.text}
                                  </p>
                                </div>
                              )}
                              <p className="text-xs text-gray-400 mt-1">
                                p.{highlight.position?.pageNumber || '?'}
                              </p>
                            </div>
                          );
                        })
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center bg-white dark:bg-gray-800 rounded-lg shadow-md">
          <div className="text-center text-gray-500 dark:text-gray-400">
            <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <p>Select a paper to start studying</p>
          </div>
        </div>
      )}
    </div>
  );
}
