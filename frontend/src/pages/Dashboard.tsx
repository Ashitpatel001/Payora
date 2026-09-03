import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getDashboardStats } from '../api/client';
import { StatCard } from '../components/StatCard';
import { Badge } from '../components/Badge';

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboardStats()
      .then((data) => {
        setStats(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="p-8 max-w-7xl mx-auto flex items-center justify-center min-h-[50vh]">
        <div className="flex items-center gap-3 text-text-secondary">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-accent border-t-transparent" />
          <span>Loading recovery intelligence...</span>
        </div>
      </div>
    );
  }

  const {
    total_at_risk = 0,
    recovered_amount = 0,
    recovery_rate = 0,
    total_cases = 0,
    active_cases = 0,
    guardrail_blocks = 0,
    quadrant_distribution = {},
    batch_trends = [],
  } = stats || {};

  const maxQuadrantVal = Math.max(...Object.values(quadrant_distribution).map((v: any) => Number(v) || 0), 1);

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6 md:space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-text-primary">
            Revenue Recovery Dashboard
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Real-time pipeline monitoring, automated diagnosis, and recovery intelligence.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/queue"
            className="rounded-lg border border-border bg-surface px-4 py-2 text-sm font-semibold text-text-primary shadow-xs hover:bg-page transition-colors"
          >
            View Cases
          </Link>
          <Link
            to="/metrics"
            className="rounded-lg bg-cta-dark px-4 py-2 text-sm font-semibold text-surface shadow-xs hover:bg-cta-dark/90 transition-colors inline-flex items-center gap-2"
          >
            <span>Run Evaluation</span>
            <span>→</span>
          </Link>
        </div>
      </div>

      {/* Recovr Style CTA Banner: Blue "Run Held-Out Batch Evaluation" */}
      <div className="rounded-xl border border-accent/20 bg-gradient-to-r from-accent to-indigo-700 p-6 text-surface shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-2 rounded-full bg-surface/20 px-3 py-0.5 text-xs font-semibold text-surface backdrop-blur-xs">
              <span>Model Evaluation</span>
              <span>•</span>
              <span>Zero-Shot Holdout</span>
            </div>
            <h2 className="text-lg md:text-xl font-bold">
              Run Held-Out Batch Evaluation
            </h2>
            <p className="text-sm text-surface/80 max-w-2xl">
              Execute the complete multi-agent recovery graph against the untouched 30-case holdout split to compute unbiased recovery rates, financial yield, and guardrail precision.
            </p>
          </div>
          <Link
            to="/metrics"
            className="shrink-0 rounded-lg bg-surface px-5 py-2.5 text-sm font-bold text-accent shadow-sm hover:bg-surface/95 transition-all text-center"
          >
            Launch Evaluation Harness
          </Link>
        </div>
      </div>

      {/* 4 Stat Cards Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total ₹ At Risk"
          value={`₹${(total_at_risk / 100).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`}
          subtitle={`Across ${total_cases} detected recovery events`}
          icon={
            <svg className="w-5 h-5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
        <StatCard
          label="Recovery Rate"
          value={`${recovery_rate}%`}
          trend={{ value: 'Real-time', isPositive: true, label: `₹${(recovered_amount / 100).toLocaleString('en-IN', { maximumFractionDigits: 0 })} recovered` }}
          icon={
            <svg className="w-5 h-5 text-success-text" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
        <StatCard
          label="Active Cases"
          value={active_cases}
          subtitle="Under active automated engagement"
          icon={
            <svg className="w-5 h-5 text-warning-text" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          }
        />
        <StatCard
          label="Compliance Blocks"
          value={guardrail_blocks}
          subtitle="Prevented unsafe / illegal interventions"
          icon={
            <svg className="w-5 h-5 text-danger-text" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          }
        />
      </div>

      {/* Two Column Layout: Recovery Performance Trend + Risk Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trend Widget */}
        <div className="lg:col-span-2 rounded-xl border border-border bg-surface p-6 shadow-sm">
          <div className="flex items-center justify-between border-b border-border pb-4 mb-4">
            <div>
              <h3 className="font-semibold text-text-primary text-base">Batch Recovery Performance History</h3>
              <p className="text-xs text-text-secondary mt-0.5">Evaluation performance tracked across holdout runs</p>
            </div>
            <Link to="/metrics" className="text-xs font-semibold text-accent hover:underline">
              Full Evaluation Suite →
            </Link>
          </div>

          {batch_trends.length === 0 ? (
            <div className="py-12 text-center text-text-secondary text-sm">
              No batch evaluation runs recorded yet. Click{' '}
              <Link to="/metrics" className="text-accent font-medium hover:underline">
                Run Held-Out Batch
              </Link>{' '}
              to generate trend data.
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                {batch_trends.slice(-3).reverse().map((run: any, i: number) => (
                  <div key={i} className="rounded-lg border border-border bg-page p-4">
                    <p className="text-xs text-text-secondary font-mono">{run.date}</p>
                    <p className="text-xl font-bold text-text-primary mt-1 tabular-nums">
                      {run.recovery_rate}%
                    </p>
                    <p className="text-xs text-success-text font-medium mt-0.5 tabular-nums">
                      ₹{(run.amount_recovered / 100).toLocaleString('en-IN', { maximumFractionDigits: 0 })} recovered
                    </p>
                  </div>
                ))}
              </div>

              {/* Visual chart bar representations */}
              <div className="pt-4 border-t border-border">
                <div className="flex items-end justify-between gap-3 h-32 pt-6">
                  {batch_trends.slice(-8).map((run: any, idx: number) => (
                    <div key={idx} className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end group">
                      <span className="text-[11px] font-semibold text-text-primary opacity-0 group-hover:opacity-100 transition-opacity tabular-nums">
                        {run.recovery_rate}%
                      </span>
                      <div
                        className="w-full bg-accent/80 hover:bg-accent rounded-t transition-all"
                        style={{ height: `${Math.max(run.recovery_rate, 10)}%` }}
                      />
                      <div className="flex flex-col items-center text-center w-full mt-1" title={run.date}>
                        <span className="text-[10px] text-text-secondary leading-none">
                          {run.date.split(',')[0]}
                        </span>
                        <span className="text-[9px] text-text-secondary/70 leading-none mt-0.5">
                          {run.date.split(',')[1]?.trim()}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Risk Distribution Breakdown */}
        <div className="rounded-xl border border-border bg-surface p-6 shadow-sm">
          <div className="border-b border-border pb-4 mb-4">
            <h3 className="font-semibold text-text-primary text-base">Risk Profile Distribution</h3>
            <p className="text-xs text-text-secondary mt-0.5">Diagnosed customer quadrants</p>
          </div>

          <div className="space-y-4">
            {Object.entries(quadrant_distribution).map(([quadrant, count]: [string, any]) => {
              const percentage = Math.round((Number(count) / maxQuadrantVal) * 100);
              return (
                <div key={quadrant} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <Badge status={quadrant} size="sm" />
                    <span className="font-semibold text-text-primary tabular-nums">
                      {count} cases
                    </span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-page overflow-hidden border border-border">
                    <div
                      className="h-full rounded-full bg-accent transition-all duration-500"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
