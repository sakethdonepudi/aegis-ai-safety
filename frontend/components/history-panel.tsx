"use client";

import { History, Loader2 } from "lucide-react";

import { Card } from "@/components/ui/card";
import { cn, formatDate, truncate } from "@/lib/utils";
import type { VerificationSummary } from "@/lib/types";

interface HistoryPanelProps {
  sessions: VerificationSummary[];
  activeSessionId: number | null;
  loading: boolean;
  onOpen: (sessionId: number) => void;
}

export function HistoryPanel({ sessions, activeSessionId, loading, onOpen }: HistoryPanelProps) {
  return (
    <Card id="history" className="scroll-mt-24">
      <div className="flex items-center justify-between border-b border-border px-5 py-4">
        <div className="flex items-center gap-2.5">
          <History className="h-4 w-4 text-accent" aria-hidden="true" />
          <div>
            <h3 className="text-sm font-semibold">Verification history</h3>
            <p className="mt-0.5 font-mono text-[10px] text-muted">
              Persisted in IBM Db2 · reopen any earlier session
            </p>
          </div>
        </div>
        {loading ? <Loader2 className="h-4 w-4 animate-spin text-muted" /> : null}
      </div>

      {sessions.length === 0 ? (
        <div className="px-5 py-10 text-center">
          <p className="text-xs text-fg">No verification sessions yet</p>
          <p className="mt-1 text-[11px] text-muted">
            Completed and failed verification runs will be listed here.
          </p>
        </div>
      ) : (
        <ul className="divide-y divide-border">
          {sessions.map((session) => {
            const active = session.session_id === activeSessionId;
            return (
              <li key={session.session_id}>
                <button
                  type="button"
                  onClick={() => onOpen(session.session_id)}
                  className={cn(
                    "flex w-full flex-wrap items-center gap-x-5 gap-y-2 px-5 py-3.5 text-left transition-colors",
                    active ? "bg-panel-2" : "hover:bg-panel-2/60"
                  )}
                >
                  <span className="font-mono text-[10px] text-muted">
                    #{String(session.session_id).padStart(3, "0")}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-xs text-fg">
                      {truncate(session.preview.replace(/\s+/g, " "), 150)}
                    </span>
                    <span className="mt-1 block font-mono text-[9px] text-muted">
                      {formatDate(session.created_at)} · {session.model_provider} ·{" "}
                      {session.status.toLowerCase()}
                    </span>
                  </span>
                  <span className="flex items-center gap-1.5 font-mono text-[9px]">
                    <span className="rounded bg-supported/10 px-1.5 py-0.5 text-supported">
                      S {session.counts.supported}
                    </span>
                    <span className="rounded bg-contradicted/10 px-1.5 py-0.5 text-contradicted">
                      C {session.counts.contradicted}
                    </span>
                    <span className="rounded bg-insufficient/10 px-1.5 py-0.5 text-insufficient">
                      I {session.counts.insufficient_evidence}
                    </span>
                    {session.counts.verification_error > 0 ? (
                      <span className="rounded bg-verror/10 px-1.5 py-0.5 text-verror">
                        E {session.counts.verification_error}
                      </span>
                    ) : null}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </Card>
  );
}
