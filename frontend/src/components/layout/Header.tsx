import Link from 'next/link';

export function Header() {
  return (
    <header className="bg-white dark:bg-gray-800 shadow-sm">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link
          href="/"
          className="text-xl font-bold text-gray-900 dark:text-white"
        >
          Paper Curation
        </Link>
        <div className="flex items-center gap-3">
          <Link
            href="/search"
            className="px-4 py-2 text-gray-700 dark:text-gray-200 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
          >
            Search
          </Link>
          <Link
            href="/study"
            className="px-4 py-2 text-gray-700 dark:text-gray-200 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
          >
            Study
          </Link>
          <Link
            href="/papers/new"
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Add Paper
          </Link>
        </div>
      </nav>
    </header>
  );
}
