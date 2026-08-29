import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getGuardrails } from '../api/client';
import { DataTable, type Column } from '../components/DataTable';
import { Badge } from '../components/Badge';

interface GuardrailRecord {
  id: string;
  event_id: string;
  rule_name: string;
  passed: boolean;
  reason: string;
  checked_at: string;
}

export const GuardrailLog: React.FC = () => {
  const [logs, setLogs] = useState<GuardrailRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getGuardrails()
      .then((data) => {
        setLogs(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const formatTimestamp = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleString('en-IN', {
        dateStyle: 'medium',
        timeStyle: 'short',
      });
    } catch {
      return dateStr;
    }
  };

  const columns: Column<GuardrailRecord>[] = [
    {
      key: 'event_id',
      header: 'Case ID',
      sortable: true,
      render: (row) => (
        <Link
          to={`/cases/${row.event_id}`}
          className="font-mono font-medium text-accent hover:underline"
        >
          {row.event_id.startsWith('evt_') ? row.event_id.split('_')[1].substring(0, 8) : row.event_id.substring(0, 8)}
        </Link>
      ),
    },
    {
      key: 'rule_name',
      header: 'Compliance Rule',
      sortable: true,
      render: (row) => (
        <span className="font-mono text-xs font-semibold text-text-primary">
          {row.rule_name}
        </span>
      ),
    },
    {
      key: 'passed',
      header: 'Verification Result',
      sortable: true,
      render: (row) => (
        <Badge
          status={row.passed ? 'passed' : 'blocked'}
          label={row.passed ? 'Passed / Clear' : 'Blocked'}
          size="sm"
        />
      ),
    },
    {
      key: 'reason',
      header: 'Compliance Rationale',
      render: (row) => (
        <p className="max-w-md text-xs text-text-secondary italic" title={row.reason}>
          "{row.reason}"
        </p>
      ),
    },
    {
      key: 'checked_at',
      header: 'Timestamp',
      sortable: true,
      render: (row) => (
        <span className="text-xs text-text-secondary tabular-nums">
          {formatTimestamp(row.checked_at)}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Action',
      align: 'right',
      render: (row) => (
        <Link
          to={`/cases/${row.event_id}`}
          className="text-xs font-semibold text-accent hover:underline inline-flex items-center gap-1"
        >
          <span>View Case</span>
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
          <span>Loading compliance logs...</span>
        </div>
      </div>
    );
  }

  const blockedCount = logs.filter((l) => !l.passed).length;
  const passedCount = logs.filter((l) => l.passed).length;

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-text-primary">
            Compliance & Guardrail Logs
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Deterministic FDCPA, RBI, and merchant policy checks applied before any customer intervention.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge status="passed" label={`${passedCount} Cleared`} size="md" />
          <Badge status="blocked" label={`${blockedCount} Intercepted`} size="md" />
        </div>
      </div>

      {/* Main Table */}
      <DataTable
        columns={columns}
        data={logs}
        keyExtractor={(row) => row.id}
        defaultSortKey="checked_at"
        defaultSortOrder="desc"
        emptyMessage="No compliance checks logged yet."
      />
    </div>
  );
};
