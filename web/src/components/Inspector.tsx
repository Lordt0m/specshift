import React from 'react';
import { Finding, Summary } from '../types';

interface InspectorProps {
  selectedFinding: Finding | null;
  summary: Summary | null;
  onClearSelection: () => void;
}

export const Inspector: React.FC<InspectorProps> = ({
  selectedFinding,
  summary,
  onClearSelection,
}) => {
  if (!selectedFinding) {
    return (
      <aside
        style={{
          background: 'var(--surface)',
          borderLeft: '1px solid var(--border)',
          padding: '1.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.25rem',
          overflowY: 'auto',
        }}
      >
        <div>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '0.4rem' }}>
            Evidence Inspector
          </h2>
          <p style={{ fontSize: '0.82rem', color: 'var(--secondary)' }}>
            Select any finding or operation to inspect exact before/after contract values, policy assumptions, and source pointers.
          </p>
        </div>

        {summary && (
          <div
            style={{
              padding: '1rem',
              background: 'var(--canvas)',
              borderRadius: '6px',
              border: '1px solid var(--border)',
            }}
          >
            <div style={{ fontSize: '0.78rem', textTransform: 'uppercase', color: 'var(--secondary)', fontWeight: 600 }}>
              Audit Conclusion
            </div>
            <div style={{ fontSize: '0.95rem', fontWeight: 700, margin: '0.4rem 0' }}>
              {summary.conclusion}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--secondary)', marginTop: '0.5rem', lineHeight: 1.4 }}>
              Covered: {summary.covered_operations} of {summary.total_operations} operations &bull; {summary.coverage_gap_count} coverage gaps
            </div>
          </div>
        )}
      </aside>
    );
  }

  const {
    id,
    rule_id,
    classification,
    context,
    origin_pointer,
    candidate_pointer,
    before,
    before_presence,
    after,
    after_presence,
    explanation,
    policy_rule,
    affected_operations,
  } = selectedFinding;

  const renderValue = (val: unknown, presence: string) => {
    if (presence === 'absent') {
      return <span style={{ color: 'var(--secondary)', fontStyle: 'italic' }}>&lang;Absent&rang;</span>;
    }
    if (presence === 'null') {
      return <span style={{ color: 'var(--secondary)', fontStyle: 'italic' }}>&lang;null&rang;</span>;
    }
    if (typeof val === 'object' && val !== null) {
      return <pre style={{ margin: 0, fontSize: '0.75rem', overflowX: 'auto' }}>{JSON.stringify(val, null, 2)}</pre>;
    }
    return <span>{String(val)}</span>;
  };

  return (
    <aside
      style={{
        background: 'var(--surface)',
        borderLeft: '1px solid var(--border)',
        padding: '1.25rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
        overflowY: 'auto',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '1.05rem', fontWeight: 700 }}>{rule_id}</span>
            <span className={`badge badge-${classification}`}>
              {classification.replace('_', ' ')}
            </span>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--secondary)', marginTop: '0.2rem' }}>
            {policy_rule}
          </p>
        </div>
        <button
          onClick={onClearSelection}
          title="Clear selection"
          style={{
            background: 'none',
            border: 'none',
            fontSize: '1.1rem',
            cursor: 'pointer',
            color: 'var(--secondary)',
          }}
        >
          &times;
        </button>
      </div>

      <div
        style={{
          background: 'var(--canvas)',
          padding: '0.75rem 1rem',
          borderRadius: '6px',
          border: '1px solid var(--border)',
          fontSize: '0.85rem',
          lineHeight: 1.45,
        }}
      >
        <div style={{ fontWeight: 600, marginBottom: '0.2rem' }}>Explanation:</div>
        <div>{explanation}</div>
      </div>

      <div>
        <div style={{ fontSize: '0.78rem', textTransform: 'uppercase', color: 'var(--secondary)', fontWeight: 600, marginBottom: '0.4rem' }}>
          Exact Contract Evidence
        </div>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '0.75rem',
            background: 'var(--canvas)',
            padding: '0.75rem',
            borderRadius: '6px',
            border: '1px solid var(--border)',
          }}
        >
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--secondary)', fontWeight: 600, marginBottom: '0.2rem' }}>
              Baseline [{before_presence}]
            </div>
            <div className="mono" style={{ fontSize: '0.8rem', background: 'var(--surface)', padding: '0.4rem', borderRadius: '4px', border: '1px solid var(--border-light)' }}>
              {renderValue(before, before_presence)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--secondary)', fontWeight: 600, marginBottom: '0.2rem' }}>
              Candidate [{after_presence}]
            </div>
            <div className="mono" style={{ fontSize: '0.8rem', background: 'var(--surface)', padding: '0.4rem', borderRadius: '4px', border: '1px solid var(--border-light)' }}>
              {renderValue(after, after_presence)}
            </div>
          </div>
        </div>
      </div>

      <div>
        <div style={{ fontSize: '0.78rem', textTransform: 'uppercase', color: 'var(--secondary)', fontWeight: 600, marginBottom: '0.4rem' }}>
          Source Pointers
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.78rem' }}>
          <div>
            <span style={{ color: 'var(--secondary)' }}>Origin: </span>
            <code className="mono" style={{ wordBreak: 'break-all' }}>
              {origin_pointer || '(Added in candidate)'}
            </code>
          </div>
          {candidate_pointer && (
            <div>
              <span style={{ color: 'var(--secondary)' }}>Candidate: </span>
              <code className="mono" style={{ wordBreak: 'break-all' }}>
                {candidate_pointer}
              </code>
            </div>
          )}
        </div>
      </div>

      <div>
        <div style={{ fontSize: '0.78rem', textTransform: 'uppercase', color: 'var(--secondary)', fontWeight: 600, marginBottom: '0.4rem' }}>
          Affected Operations ({affected_operations.length})
        </div>
        <p style={{ fontSize: '0.75rem', color: 'var(--secondary)', marginBottom: '0.4rem' }}>
          Reachability shows contract use; actual client failure depends on consumer behavior.
        </p>
        <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
          {affected_operations.map((op) => (
            <li
              key={op}
              style={{
                fontSize: '0.78rem',
                fontFamily: 'var(--font-mono)',
                background: 'var(--canvas)',
                padding: '0.35rem 0.6rem',
                borderRadius: '4px',
                border: '1px solid var(--border-light)',
              }}
            >
              {op}
            </li>
          ))}
        </ul>
      </div>

      <div style={{ marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid var(--border)', fontSize: '0.72rem', color: 'var(--secondary)' }}>
        Finding ID: <code>{id}</code> &bull; Context: <strong>{context}</strong>
      </div>
    </aside>
  );
};
