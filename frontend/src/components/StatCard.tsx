import React from 'react';

interface StatCardProps {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  trend?: {
    value: string;
    isPositive?: boolean;
    label?: string;
  };
  subtitle?: string;
  className?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  icon,
  trend,
  subtitle,
  className = '',
}) => {
  return (
    <div
      className={`rounded-xl border border-border bg-surface p-5 md:p-6 shadow-sm transition-all hover:shadow ${className}`}
    >
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-text-secondary">{label}</p>
        {icon && (
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-page text-text-secondary">
            {icon}
          </div>
        )}
      </div>

      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-2xl md:text-3xl font-bold tracking-tight text-text-primary tabular-nums">
          {value}
        </span>
      </div>

      {(trend || subtitle) && (
        <div className="mt-2 flex items-center gap-1.5 text-xs text-text-secondary">
          {trend && (
            <span
              className={`font-semibold inline-flex items-center gap-0.5 ${
                trend.isPositive ? 'text-success-text' : 'text-danger-text'
              }`}
            >
              {trend.isPositive ? '↑' : '↓'} {trend.value}
            </span>
          )}
          {trend?.label && <span>{trend.label}</span>}
          {subtitle && !trend && <span>{subtitle}</span>}
        </div>
      )}
    </div>
  );
};
