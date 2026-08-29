import React from 'react';
import { useNavigate, useLocation, useSearchParams } from 'react-router-dom';

interface TopBarProps {
  onSearch?: (query: string) => void;
}

export const TopBar: React.FC<TopBarProps> = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const currentQuery = searchParams.get('search') || '';

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    if (location.pathname !== '/queue') {
      navigate(`/queue?search=${encodeURIComponent(query)}`);
    } else {
      if (query) {
        setSearchParams({ search: query });
      } else {
        setSearchParams({});
      }
    }
  };

  return (
    <header className="sticky top-0 z-20 flex h-16 w-full items-center justify-between border-b border-border bg-surface/95 px-6 backdrop-blur-sm">
      {/* Search Input */}
      <div className="relative w-full max-w-md">
        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-text-secondary">
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <input
          type="text"
          value={currentQuery}
          onChange={handleSearchChange}
          placeholder="Search cases, customers, error codes..."
          className="w-full rounded-lg border border-border bg-page py-2 pl-10 pr-4 text-sm text-text-primary placeholder-text-secondary outline-none transition-all focus:border-accent focus:bg-surface focus:ring-1 focus:ring-accent"
        />
      </div>

      {/* Right Actions & Badges */}
      <div className="flex items-center gap-4">
        {/* Test Mode Badge */}
        <div className="inline-flex items-center gap-2 rounded-full bg-cta-dark px-3 py-1 text-xs font-semibold text-surface shadow-xs">
          <span className="h-2 w-2 rounded-full bg-warning-text animate-pulse" />
          <span>Test Mode</span>
        </div>

        {/* Action Icons */}
        <div className="flex items-center gap-1 text-text-secondary border-l border-border pl-4">
          <button
            title="Notifications"
            className="rounded-lg p-2 hover:bg-page hover:text-text-primary transition-colors relative"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            <span className="absolute top-1.5 right-1.5 h-1.5 w-1.5 rounded-full bg-accent" />
          </button>
          <button
            title="Settings"
            className="rounded-lg p-2 hover:bg-page hover:text-text-primary transition-colors"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
};
