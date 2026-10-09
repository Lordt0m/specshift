import React, { useState } from 'react';
import { Finding, CoverageGap } from '../types';

interface OperationsListProps {
  findings: Finding[];
  coverageGaps: CoverageGap[];
  selectedFindingId: string | null;
  onSelectFinding: (finding: Finding) => void;
}

export const OperationsList: React.FC<OperationsListProps> = ({
  findings,
  coverageGaps,
  selectedFindingId,
  onSelectFinding,
}) => {
  const [filter, setFilter] = useState<string>('all');

  const filteredFindings = findings.filter((f) => {
    if (filter === 'all') return true;
    return f.classification === filter;
  });

  return (
    <section
      aria-label="Findings and operations list"
      style={{
        background: 'var(--surface)',
        borderTop: '1px solid var(--border)',
        padding: '1rem 1.5rem',
      }}
    >
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '0.75rem',
          marginBottom: '1rem',
        }}
      >
        <div>
          <h2 style={{ fontSize: '1rem', fontWeight: 700 }}>Contract Findings &amp; Gaps</h2>
          <p style={{ fontSize: '0.78rem', color: 'var(--secondary)' }}>
            Complete keyboard-accessible findings list with direct evidence links.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
          {[
            { id: 'all', label: `All (${findings.length})` },
            { id: 'breaking', label: `Breaking (${findings.filter((f) => f.classification === 'breaking').length})` },
            { id: 'review_required', label: `Review (${findings.filter((f) => f.classification === 'review_required').length})` },
            { id: 'non_breaking', label: `Non-breaking (${findings.filter((f) => f.classification === 'non_breaking').length})` },
            { id: 'gaps', label: `Gaps (${coverageGaps.length})` },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilter(tab.id)}
              style={{
                background: filter === tab.id ? 'var(--canvas)' : 'none',
                border: filter === tab.id ? '1px solid var(--border)' : '1px solid transparent',
                borderRadius: '4px',
                padding: '0.25rem 0.6rem',
                fontSize: '0.78rem',
                fontWeight: filter === tab.id ? 600 : 400,
                cursor: 'pointer',
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {filter === 'gaps' ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
          {coverageGaps.map((gap) => (
            <div
              key={gap.id}
              style={{
                padding: '0.75rem 1rem',
                borderRadius: '6px',
                border: '1px solid var(--review-border)',
                background: 'var(--review-bg)',
                fontSize: '0.82rem',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <span style={{ fontWeight: 700, color: 'var(--review)' }}>
                  Construct: <code>{gap.construct}</code>
                </span>
                <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--secondary)' }}>
                  {gap.pointer}
                </span>
              </div>
              <div>{gap.reason}</div>
              <div style={{ marginTop: '0.4rem', fontSize: '0.75rem', color: 'var(--secondary)' }}>
                Contaminates: {gap.affected_operations.join(', ')}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '280px', overflowY: 'auto' }}>
          {filteredFindings.map((f) => {
            const isSelected = f.id === selectedFindingId;
            return (
              <div
                key={f.id}
                role="button"
                tabIndex={0}
                onClick={() => onSelectFinding(f)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onSelectFinding(f);
                  }
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.6rem 0.9rem',
                  borderRadius: '6px',
                  border: isSelected ? '2px solid var(--highlight)' : '1px solid var(--border-light)',
                  background: isSelected ? 'var(--highlight-bg)' : 'var(--surface)',
                  cursor: 'pointer',
                  fontSize: '0.82rem',
                  gap: '1rem',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flex: 1, minWidth: 0 }}>
                  <span className={`badge badge-${f.classification}`} style={{ flexShrink: 0 }}>
                    {f.rule_id}
                  </span>
                  <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    <span style={{ fontWeight: 600 }}>{f.explanation}</span>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexShrink: 0, fontSize: '0.75rem', color: 'var(--secondary)' }}>
                  <span className="mono" style={{ maxWidth: '160px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {f.origin_pointer || '(new)'}
                  </span>
                  <span>{f.affected_operations.length} affected</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
};
