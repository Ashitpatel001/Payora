import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getCase, resolvePTP, simulatePayment, simulatePtp } from '../api/client';
import { Badge } from '../components/Badge';
import { Timeline, TimelineNode } from '../components/Timeline';

export const CaseDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [caseData, setCaseData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [resolving, setResolving] = useState(false);

  const loadCase = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const data = await getCase(id);
      setCaseData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCase();
  }, [id]);

  const handleResolvePTP = async (status: 'kept' | 'broken') => {
    if (!id) return;
    setResolving(true);
    try {
      await resolvePTP(id, status);
      await loadCase();
    } catch (err) {
      console.error(err);
    } finally {
      setResolving(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 max-w-5xl mx-auto flex items-center justify-center min-h-[50vh]">
        <div className="flex items-center gap-3 text-text-secondary">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-accent border-t-transparent" />
          <span>Loading case timeline and reasoning trace...</span>
        </div>
      </div>
    );
  }

  if (!caseData || !caseData.event) {
    return (
      <div className="p-8 max-w-5xl mx-auto">
        <div className="rounded-xl border border-border bg-surface p-12 text-center text-text-secondary">
          Case not found or invalid identifier.
          <div className="mt-4">
            <Link to="/queue" className="text-accent font-semibold hover:underline">
              ← Return to Case Allocation Queue
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const { event, deliveries, audit_logs: logs, ptp } = caseData;

  

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

  return (
    <div className="p-6 md:p-8 max-w-5xl mx-auto space-y-6">
      {/* Back Navigation & Header */}
      <div className="space-y-3">
        <Link
          to="/queue"
          className="text-xs font-semibold text-text-secondary hover:text-text-primary inline-flex items-center gap-1.5 transition-colors"
        >
          <span>←</span>
          <span>Back to Case Allocation Queue</span>
        </Link>

        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-border pb-6">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-text-primary font-mono">
                Case #{event.id.startsWith('evt_') ? event.id.split('_')[1] : event.id}
              </h1>
              {ptp && (
                <Badge
                  status={ptp.status}
                  label={`PTP ${ptp.status.toUpperCase()}`}
                  size="md"
                />
              )}
            </div>
            <p className="text-xs font-mono text-text-secondary mt-1">
              Customer ID: <span className="text-text-primary font-semibold">{event.customer_id}</span> • Source: <span className="uppercase">{event.source}</span>
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-xs text-text-secondary">Amount at Risk</p>
              <p className="text-xl font-bold text-text-primary tabular-nums">
                ₹{(event.amount / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* PTP Alert Banner if Active */}
      {ptp && (
        <div className="rounded-xl border border-warning-text/20 bg-warning-bg p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-warning-text/10 text-warning-text font-bold">
              ₹
            </div>
            <div>
              <h3 className="font-semibold text-warning-text text-sm">
                Active Promise-to-Pay Commitment ({ptp.status.toUpperCase()})
              </h3>
              <p className="text-xs text-warning-text/80 mt-0.5">
                Customer committed to pay{' '}
                <strong className="font-bold tabular-nums">
                  ₹{(ptp.promised_amount / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </strong>{' '}
                by <strong className="font-bold">{ptp.promised_date}</strong> (detected via {ptp.detected_via}).
              </p>
            </div>
          </div>

          {ptp.status === 'pending' && (
            <div className="flex items-center gap-2 shrink-0">
              <button
                onClick={() => handleResolvePTP('kept')}
                disabled={resolving}
                className="rounded-lg bg-success-text px-4 py-1.5 text-xs font-bold text-surface shadow-xs hover:bg-success-text/90 transition-all disabled:opacity-50"
              >
                Mark Kept (Recovered)
              </button>
              <button
                onClick={() => handleResolvePTP('broken')}
                disabled={resolving}
                className="rounded-lg bg-danger-text px-4 py-1.5 text-xs font-bold text-surface shadow-xs hover:bg-danger-text/90 transition-all disabled:opacity-50"
              >
                Mark Broken
              </button>
            </div>
          )}
        </div>
      )}

      {/* Payment Link Simulation Banner */}
      {!ptp && deliveries && deliveries.length > 0 && deliveries[0].response_payload?.short_url && !['recovered', 'simulated_recovered'].includes(deliveries[0].status) && (
        <div className="rounded-xl border border-info-text/20 bg-info-bg p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-info-text/10 text-info-text font-bold">
              🔗
            </div>
            <div>
              <h3 className="font-semibold text-info-text text-sm">
                Awaiting Payment Confirmation
              </h3>
              <p className="text-xs text-info-text/80 mt-0.5">
                Payment link sent. In test-mode, real webhooks do not fire automatically.
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={async () => {
                setResolving(true);
                try {
                  await simulatePayment(event.id);
                  await loadCase();
                } catch (err: any) {
                  alert(`Simulation failed: ${err.message}`);
                } finally {
                  setResolving(false);
                }
              }}
              disabled={resolving}
              className="rounded-lg bg-info-text px-4 py-1.5 text-xs font-bold text-surface shadow-xs hover:bg-info-text/90 transition-all disabled:opacity-50"
            >
              Simulate Payment Received
            </button>
          </div>
        </div>
      )}

      {/* PTP Simulation Banner */}
      {!ptp && deliveries && deliveries.length > 0 && !deliveries[0].response_payload?.short_url && deliveries[0].status === 'delivered' && (
        <div className="rounded-xl border border-info-text/20 bg-info-bg p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-info-text/10 text-info-text font-bold">
              💬
            </div>
            <div>
              <h3 className="font-semibold text-info-text text-sm">
                Awaiting Customer Response
              </h3>
              <p className="text-xs text-info-text/80 mt-0.5">
                Message delivered. In demo mode, no real WhatsApp connection exists.
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={async () => {
                setResolving(true);
                try {
                  await simulatePtp(event.id);
                  await loadCase();
                } catch (err: any) {
                  alert(`Simulation failed: ${err.message}`);
                } finally {
                  setResolving(false);
                }
              }}
              disabled={resolving}
              className="rounded-lg bg-info-text px-4 py-1.5 text-xs font-bold text-surface shadow-xs hover:bg-info-text/90 transition-all disabled:opacity-50"
            >
              Simulate Customer PTP Response
            </button>
          </div>
        </div>
      )}

      {/* Timeline Section */}
      <div id="guardrails" className="rounded-xl border border-border bg-surface p-6 md:p-8 shadow-sm space-y-6">
        <div className="border-b border-border pb-4">
          <h2 className="text-lg font-bold text-text-primary">Case Execution Timeline</h2>
          <p className="text-xs text-text-secondary mt-0.5">
            Step-by-step audit trail of detection, automated diagnosis, compliance verification, and delivery execution.
          </p>
        </div>

        <Timeline className="pt-2">
          {/* Initial Webhook Detection Event */}
          <TimelineNode
            color="neutral"
            title="Payment Risk Detected"
            timestamp={formatTimestamp(event.created_at)}
            actorFrom="razorpay_webhook"
            actorTo="system"
          >
            <div className="space-y-1.5">
              <p>
                Risk event <span className="font-mono font-semibold text-text-primary">{event.event_type}</span> captured for ₹{(event.amount / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}.
              </p>
              <div className="rounded-lg bg-page border border-border p-3 font-mono text-xs text-text-secondary overflow-x-auto whitespace-pre-wrap">
                {JSON.stringify(
                  {
                    ...event.raw_payload,
                    amount: `${event.raw_payload.amount} paise (₹${(event.raw_payload.amount / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })})`
                  },
                  null,
                  2
                )}
              </div>
            </div>
          </TimelineNode>

          {/* Dynamic Audit Logs (The Ladder) */}
          {logs
            .sort((a: any, b: any) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
            .map((log: any, idx: number) => {
              // Determine aesthetics based on action
              let color: "system" | "warning" | "danger" | "info" | "success" | "neutral" = "system";
              let title = log.action;
              
              if (log.action === "diagnose") {
                color = "system"; title = "Root Cause Diagnosed";
              } else if (log.action === "guardrail_check") {
                color = log.reasoning.includes("limit") || log.reasoning.includes("pending") || log.reasoning.includes("Violation") ? "danger" : "warning";
                title = "Automated Compliance Check";
              } else if (log.action === "policy_decision") {
                color = "info"; title = "Intervention Strategy Formulated";
              } else if (log.action === "execute") {
                color = "success"; title = "Delivery Execution & Customer Engagement";
              } else if (log.action === "awaiting_confirmation") {
                color = "warning"; title = "Awaiting Confirmation";
              } else if (log.action === "confirm_recovery") {
                color = "success"; title = "Confirmed Recovery";
              } else if (log.action === "resolve_ptp") {
                color = "success"; title = "Human Resolution";
              }

              const colorClasses = {
                system: "bg-system-bg text-system-text border-system-text/20",
                warning: "bg-warning-bg text-warning-text border-warning-text/20",
                danger: "bg-danger-bg text-danger-text border-danger-text/20",
                info: "bg-info-bg text-info-text border-info-text/20",
                success: "bg-success-bg text-success-text border-success-text/20",
                neutral: "bg-page text-text-secondary border-border"
              };
              
              return (
                <TimelineNode
                  key={log.id}
                  color={color}
                  title={title}
                  timestamp={formatTimestamp(log.timestamp)}
                  actorFrom={log.actor || "system"}
                  actorTo={log.action === "execute" ? "customer" : "system"}
                  isLast={idx === logs.length - 1}
                >
                  <div className="space-y-2">
                    <div className={`rounded-lg border p-3 text-xs italic ${colorClasses[color]}`}>
                      "{log.reasoning}"
                    </div>

                    {/* Show execution artifacts only on execute node */}
                    {log.action === "execute" && deliveries && deliveries.length > 0 && (
                      <div className="mt-3">
                        {deliveries[0].response_payload?.transcript ? (
                          <div className="rounded-xl border border-cta-dark bg-cta-dark p-4 text-surface font-mono text-xs shadow-inner space-y-3 mt-3">
                            <div className="flex items-center justify-between border-b border-surface/20 pb-2 text-surface/70">
                              <div className="flex items-center gap-2">
                                <span className="h-2 w-2 rounded-full bg-danger-text animate-pulse" />
                                <span className="font-bold">LiveKit Secure Audio Transcript Stream</span>
                              </div>
                              <span className="text-[10px] uppercase font-semibold text-accent">Hinglish PTP Negotiation</span>
                            </div>

                            <div className="space-y-2 max-h-48 overflow-y-auto">
                              {deliveries[0].response_payload.transcript.map((msg: any, i: number) => (
                                <div key={i} className="flex gap-2">
                                  <span className={`font-bold ${msg.speaker === 'agent' ? 'text-accent' : 'text-success-text'}`}>
                                    [{msg.speaker.toUpperCase()}]:
                                  </span>
                                  <span className="text-surface/90">{msg.text}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        ) : null}

                        {deliveries[0].response_payload?.short_url && (
                          <div className="rounded-lg bg-info-bg border border-info-text/20 p-3 mt-3 flex items-center justify-between">
                            <div>
                              <p className="font-semibold text-info-text text-xs uppercase">Proof of Action (Artifact)</p>
                              <p className="text-xs text-text-secondary mt-0.5">Razorpay Test Mode Payment Link generated.</p>
                            </div>
                            <a 
                              href={deliveries[0].response_payload.short_url} 
                              target="_blank" 
                              rel="noopener noreferrer" 
                              className="rounded-lg bg-surface border border-info-text/30 px-3 py-1.5 text-xs font-bold text-info-text hover:bg-info-bg transition-colors flex items-center gap-2"
                            >
                              {deliveries[0].response_payload.short_url}
                            </a>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </TimelineNode>
              );
            })}
        </Timeline>
      </div>
    </div>
  );
};
