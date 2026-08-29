import React from 'react';

export type TimelineColor = 'neutral' | 'system' | 'warning' | 'danger' | 'info' | 'success';

interface TimelineNodeProps {
  color?: TimelineColor;
  title: string;
  timestamp: string;
  actorFrom?: string;
  actorTo?: string;
  isLast?: boolean;
  amountBox?: {
    label: string;
    amount: number | string;
    statusText?: string;
  };
  children?: React.ReactNode;
}

export const TimelineNode: React.FC<TimelineNodeProps> = ({
  color = 'neutral',
  title,
  timestamp,
  actorFrom,
  actorTo,
  isLast = false,
  amountBox,
  children,
}) => {
  // Dot styling per §2.2
  let dotBg = 'bg-neutral-bg text-neutral-text border-neutral-text/20';
  let dotInner = 'bg-neutral-text';

  switch (color) {
    case 'system':
      dotBg = 'bg-system-bg text-system-text border-system-text/20';
      dotInner = 'bg-system-text';
      break;
    case 'warning':
      dotBg = 'bg-warning-bg text-warning-text border-warning-text/20';
      dotInner = 'bg-warning-text';
      break;
    case 'danger':
      dotBg = 'bg-danger-bg text-danger-text border-danger-text/20';
      dotInner = 'bg-danger-text';
      break;
    case 'info':
      dotBg = 'bg-info-bg text-info-text border-info-text/20';
      dotInner = 'bg-info-text';
      break;
    case 'success':
      dotBg = 'bg-success-bg text-success-text border-success-text/20';
      dotInner = 'bg-success-text';
      break;
    case 'neutral':
    default:
      dotBg = 'bg-neutral-bg text-neutral-text border-neutral-text/20';
      dotInner = 'bg-neutral-text';
      break;
  }

  return (
    <div className="relative flex gap-4 md:gap-6">
      {/* Left indicator line & dot */}
      <div className="flex flex-col items-center">
        <div
          className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full border ${dotBg} shadow-sm z-10`}
        >
          <div className={`h-2.5 w-2.5 rounded-full ${dotInner}`} />
        </div>
        {!isLast && (
          <div className="w-0.5 grow bg-border my-1" />
        )}
      </div>

      {/* Node Content Card */}
      <div className={`grow pb-8 ${isLast ? 'pb-0' : ''}`}>
        <div className="rounded-xl border border-border bg-surface p-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-3">
            <div className="flex items-center gap-2.5">
              <h3 className="font-semibold text-text-primary text-base">{title}</h3>
              {actorFrom && actorTo && (
                <div className="inline-flex items-center gap-1 text-xs font-mono px-2 py-0.5 rounded bg-page text-text-secondary border border-border">
                  <span>{actorFrom}</span>
                  <span className="text-text-secondary/50">→</span>
                  <span>{actorTo}</span>
                </div>
              )}
            </div>
            <span className="text-xs text-text-secondary tabular-nums">{timestamp}</span>
          </div>

          <div className="mt-3 text-sm text-text-secondary">{children}</div>

          {/* Green/Success Highlighted Amount Sub-box per Recovr design */}
          {amountBox && (
            <div className="mt-4 rounded-lg border border-success-text/20 bg-success-bg p-4 flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-success-text">{amountBox.label}</p>
                <p className="text-xl font-bold text-success-text tabular-nums mt-0.5">
                  {typeof amountBox.amount === 'number'
                    ? `₹${(amountBox.amount / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`
                    : amountBox.amount}
                </p>
              </div>
              {amountBox.statusText && (
                <span className="rounded-full bg-surface px-3 py-1 text-xs font-semibold text-success-text border border-success-text/20">
                  {amountBox.statusText}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export const Timeline: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => {
  return <div className={`relative ${className}`}>{children}</div>;
};
