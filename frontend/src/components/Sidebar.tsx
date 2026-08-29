import React from 'react';
import { Link, useLocation } from 'react-router-dom';

interface NavItemProps {
  to: string;
  icon: React.ReactNode;
  label: string;
  badge?: string | number;
}

const NavItem: React.FC<NavItemProps> = ({ to, icon, label, badge }) => {
  const location = useLocation();
  const isActive =
    (to === '/' && (location.pathname === '/' || location.pathname === '/dashboard')) ||
    (to !== '/' && location.pathname.startsWith(to));

  return (
    <Link
      to={to}
      className={`group flex items-center justify-between rounded-lg px-3.5 py-2.5 text-sm font-medium transition-all ${
        isActive
          ? 'bg-active-nav text-accent font-semibold shadow-xs'
          : 'text-text-secondary hover:bg-page hover:text-text-primary'
      }`}
    >
      <div className="flex items-center gap-3">
        <span className={`h-5 w-5 ${isActive ? 'text-accent' : 'text-text-secondary group-hover:text-text-primary'}`}>
          {icon}
        </span>
        <span>{label}</span>
      </div>
      {badge !== undefined && (
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
            isActive ? 'bg-accent text-surface' : 'bg-neutral-bg text-neutral-text'
          }`}
        >
          {badge}
        </span>
      )}
    </Link>
  );
};

export const Sidebar: React.FC = () => {
  return (
    <aside className="fixed inset-y-0 left-0 z-30 flex w-64 flex-col border-r border-border bg-surface">
      {/* Brand Header */}
      <div className="flex h-16 items-center gap-3 border-b border-border px-6">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent text-surface font-bold text-lg shadow-sm">
          R
        </div>
        <div>
          <span className="text-base font-bold tracking-tight text-text-primary">
            Razorpay <span className="text-accent font-semibold">Recovr</span>
          </span>
          <p className="text-[10px] font-medium tracking-wide uppercase text-text-secondary">
            Revenue Recovery
          </p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1.5 p-4 overflow-y-auto">
        <div className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-text-secondary/70">
          Navigation
        </div>
        <NavItem
          to="/"
          label="Dashboard"
          icon={
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-full h-full">
              <rect width="7" height="9" x="3" y="3" rx="1" />
              <rect width="7" height="5" x="14" y="3" rx="1" />
              <rect width="7" height="9" x="14" y="12" rx="1" />
              <rect width="7" height="5" x="3" y="16" rx="1" />
            </svg>
          }
        />
        <NavItem
          to="/queue"
          label="Case Allocation"
          icon={
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-full h-full">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
              <path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
          }
        />
        <NavItem
          to="/guardrails"
          label="Compliance Logs"
          icon={
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-full h-full">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
              <path d="m9 12 2 2 4-4" />
            </svg>
          }
        />
        <NavItem
          to="/metrics"
          label="Batch Evaluation"
          icon={
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-full h-full">
              <path d="M3 3v18h18" />
              <path d="m19 9-5 5-4-4-3 3" />
            </svg>
          }
        />
      </nav>

      {/* User Profile Footer */}
      <div className="border-t border-border p-4">
        <div className="flex items-center gap-3 rounded-lg p-2 hover:bg-page transition-colors">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-accent/10 text-accent font-semibold text-sm">
            RP
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-text-primary">Razorpay Admin</p>
            <p className="truncate text-xs text-text-secondary">merchant@razorpay.com</p>
          </div>
        </div>
      </div>
    </aside>
  );
};
