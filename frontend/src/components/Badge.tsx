import React from 'react';

export type StatusType =
  | 'recovered'
  | 'in_progress'
  | 'blocked'
  | 'exhausted'
  | 'detected'
  | 'passed'
  | 'failed'
  | 'pending'
  | 'kept'
  | 'broken'
  | 'high'
  | 'medium'
  | 'low'
  | 'high_value'
  | 'serial_non_payer'
  | 'strategic_defaulter'
  | 'hardship'
  | 'technical'
  | 'forgetful'
  | string;

interface BadgeProps {
  status: StatusType;
  label?: string;
  className?: string;
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  status,
  label,
  className = '',
  size = 'sm',
}) => {
  const normalizedStatus = (status || '').toLowerCase().trim();

  // Color mappings per §2.2
  let bgClass = 'bg-neutral-bg text-neutral-text';
  let dotClass = 'bg-neutral-text';

  switch (normalizedStatus) {
    case 'recovered':
    case 'passed':
    case 'clear':
    case 'kept':
      bgClass = 'bg-success-bg text-success-text';
      dotClass = 'bg-success-text';
      break;

    case 'in_progress':
    case 'pending':
    case 'medium':
      bgClass = 'bg-warning-bg text-warning-text';
      dotClass = 'bg-warning-text';
      break;

    case 'blocked':
    case 'exhausted':
    case 'failed':
    case 'broken':
    case 'high':
    case 'high_value':
      bgClass = 'bg-danger-bg text-danger-text';
      dotClass = 'bg-danger-text';
      break;

    case 'hardship':
    case 'strategic_defaulter':
    case 'serial_non_payer':
      bgClass = 'bg-warning-bg text-warning-text';
      dotClass = 'bg-warning-text';
      break;

    case 'technical':
    case 'forgetful':
    case 'info':
      bgClass = 'bg-info-bg text-info-text';
      dotClass = 'bg-info-text';
      break;

    case 'system':
      bgClass = 'bg-system-bg text-system-text';
      dotClass = 'bg-system-text';
      break;

    case 'detected':
    case 'low':
    default:
      bgClass = 'bg-neutral-bg text-neutral-text';
      dotClass = 'bg-neutral-text';
      break;
  }

  const formatText = (text: string) => {
    return text
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const displayText = label || formatText(normalizedStatus);

  const sizeClasses =
    size === 'sm'
      ? 'px-2.5 py-0.5 text-xs font-medium'
      : 'px-3 py-1 text-sm font-medium';

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full ${sizeClasses} ${bgClass} ${className}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${dotClass}`} />
      <span>{displayText}</span>
    </span>
  );
};
