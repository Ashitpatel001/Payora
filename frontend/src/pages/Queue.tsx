import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { getEvents } from '../api/client';
import { DataTable, type Column } from '../components/DataTable';
import { Badge } from '../components/Badge';

export interface RiskEventRow {
  id: string;
  source: string;
  event_type: string;
  customer_id: string;
  amount: number;
  currency: string;
  created_at: string;
  status: string;
  channel?: string;
  reason?: string;
  diagnosis?: {
    risk_quadrant?: string;
    confidence?: number;
    root_cause?: string;
  };
  ptp?: {
    amount: number;
    date: string;
    status: string;
  };
}

export const Queue: React.FC = () => {
  const [events, setEvents] = useState<RiskEventRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchParams] = useSearchParams();
  const searchQuery = (searchParams.get('search') || '').toLowerCase().trim();

  useEffect(() => {
    getEvents()
      .then((data) => {
        setEvents(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const calculateAging = (dateStr: string) => {
    const created = new Date(dateStr).getTime();
    const now = Date.now();
    const diffDays = Math.max(0, Math.floor((now - created) / (1000 * 60 * 60 * 24)));
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return '1 day';
    return `${diffDays} days`;
  };

  const filteredEvents = React.useMemo(() => {
    if (!searchQuery) return events;
    return events.filter((e) => {
      const caseId = (e.id || '').toLowerCase();
      const customer = (e.customer_id || '').toLowerCase();
      const type = (e.event_type || '').toLowerCase();
      const reason = (e.reason || '').toLowerCase();
      const quadrant = (e.diagnosis?.risk_quadrant || '').toLowerCase();
      const status = (e.status || '').toLowerCase();

      return (
        caseId.includes(searchQuery) ||
        customer.includes(searchQuery) ||
        type.includes(searchQuery) ||
        reason.includes(searchQuery) ||
        quadrant.includes(searchQuery) ||
        status.includes(searchQuery)
      );
    });
  }, [events, searchQuery]);

  const columns: Column<RiskEventRow>[] = [
    {
      key: 'id',
      header: 'Case ID',
      sortable: true,
      render: (row) => (
        <div>
          <Link
            to={`/cases/${row.id}`}
            className="font-mono font-medium text-accent hover:underline inline-block"
          >
            {row.id.startsWith('evt_') ? row.id.split('_')[1].substring(0, 8) : row.id.substring(0, 8)}
          </Link>
          {row.ptp && (
            <div className="mt-1">
              <Badge status={row.ptp.status} label={`PTP ${row.ptp.status}`} size="sm" />
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'customer_id',
      header: 'Customer',
      sortable: true,
      render: (row) => (
        <span className="font-mono text-xs text-text-secondary">{row.customer_id}</span>
      ),
    },
    {
      key: 'amount',
      header: 'Amount At Risk',
      sortable: true,
      align: 'right',
      render: (row) => (
        <span className="font-bold text-text-primary tabular-nums">
          ₹{(row.amount / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
        </span>
      ),
    },
    {
      key: 'created_at',
      header: 'Aging',
      sortable: true,
      render: (row) => (
        <span className="text-text-secondary text-xs">{calculateAging(row.created_at)}</span>
      ),
    },
    {
      key: 'diagnosis',
      header: 'AI Priority & Profile',
      render: (row) => {
        if (!row.diagnosis?.risk_quadrant) {
          return <span className="text-text-secondary/60 text-xs italic">Unassigned</span>;
        }
        const confPercent = Math.round((row.diagnosis.confidence || 0.95) * 100);
        return (
          <Badge
            status={row.diagnosis.risk_quadrant}
            label={`${row.diagnosis.risk_quadrant.replace('_', ' ')} (${confPercent}%)`}
            size="sm"
          />
        );
      },
    },
    {
      key: 'status',
      header: 'Status',
      sortable: true,
      render: (row) => <Badge status={row.status} size="sm" />,
    },
    {
      key: 'channel',
      header: 'Channel',
      render: (row) => (
        <span className="font-mono text-xs text-text-secondary uppercase">
          {row.channel && row.channel !== '-' ? row.channel : '—'}
        </span>
      ),
    },
    {
      key: 'reason',
      header: 'Reasoning & Audit Trail',
      render: (row) => (
        <p className="max-w-xs truncate text-xs text-text-secondary" title={row.reason}>
          {row.reason || '—'}
        </p>
      ),
    },
    {
      key: 'actions',
      header: 'Action',
      align: 'right',
      render: (row) => (
        <Link
          to={`/cases/${row.id}`}
          className="text-xs font-semibold text-accent hover:underline inline-flex items-center gap-1"
        >
          <span>View Details</span>
          <span>→</span>
        </Link>
      ),
    },
  ];

  if (loading) {
    return (
      <div className="p-8 max-w-7xl mx-auto flex items-center justify-center min-h-[50vh]">
        <div className="flex items-center gap-3 text-text-secondary">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-accent border-t-transparent" />
          <span>Loading active recovery cases...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-text-primary">
            Case Allocation Queue
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Overdue accounts and failed payment events allocated for automated or human-assisted recovery.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="rounded-full bg-surface border border-border px-3 py-1 text-xs font-semibold text-text-secondary shadow-xs tabular-nums">
            {filteredEvents.length} of {events.length} Cases
          </span>
        </div>
      </div>

      {/* Main Table */}
      <DataTable
        columns={columns}
        data={filteredEvents}
        keyExtractor={(row) => row.id}
        defaultSortKey="amount"
        defaultSortOrder="desc"
        emptyMessage={
          searchQuery
            ? `No cases matching "${searchQuery}".`
            : 'No recovery cases found in the queue.'
        }
      />
    </div>
  );
};
