import React from 'react';
import { Summary } from '../types';

interface HeaderProps {
  summary: Summary | null;
  policyVersion: string;
  isSample: boolean;
  isStale: boolean;
  onOpenCompare: () => void;
  onDownloadJson: () => void;
  onDownloadHtml: () => void;
  onShowHowMade: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  summary,
  policyVersion,
  isSample,
  isStale,
  onOpenCompare,
  onDownloadJson,
  onDownloadHtml,
  onShowHowMade,
}) => {
  return (
    <header
      style={{
        background: 'var(--surface)',
        borderBottom: '1px solid var(--border)',
        padding: '0.75rem 1.5rem',
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '1rem',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span style={{ fontSize: '1.25rem', fontWeight: 800, letterSpacing: '-0.02em', color: 'var(--ink)' }}>
              SpecShift
            </span>
            <span
              style={{
                fontSize: '0.72rem',
                fontWeight: 600,
                color: 'var(--secondary)',
                background: 'var(--canvas)',
                padding: '0.15rem 0.45rem',
                borderRadius: '4px',
                border: '1px solid var(--border)',
              }}
            >
              Policy {policyVersion}
            </span>
            {isSample && (
              <button
                onClick={onShowHowMade}
                title="View details on how this synthetic comparison was generated"
                style={{
                  background: '#EDF5FD',
                  color: '#1B5492',
                  border: '1px solid #C2DCFA',
                  borderRadius: '4px',
                  padding: '0.15rem 0.5rem',
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.3rem',
                }}
              >
                <span>Recorded example · synthetic data</span>
                <span style={{ textDecoration: 'underline', fontSize: '0.7rem' }}>How this was made</span>
              </button>
            )}
            {isStale && (
              <span
                style={{
                  background: '#FFF3CD',
                  color: '#856404',
                  border: '1px solid #FFEBAA',
                  borderRadius: '4px',
                  padding: '0.15rem 0.5rem',
                  fontSize: '0.72rem',
                  fontWeight: 600,
                }}
              >
                Inputs modified (Results Stale)
              </span>
            )}
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--secondary)', marginTop: '0.1rem' }}>
            Baseline <span style={{ fontWeight: 600 }}>&rarr;</span> Candidate direction review
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
        {summary && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.35rem 0.75rem',
              background: 'var(--canvas)',
              borderRadius: '6px',
              border: '1px solid var(--border)',
              fontSize: '0.82rem',
              fontWeight: 600,
            }}
          >
            <span style={{ color: 'var(--breaking)' }}>{summary.breaking_count} Breaking</span>
            <span style={{ color: 'var(--border)' }}>&bull;</span>
            <span style={{ color: 'var(--review)' }}>{summary.review_count} Review</span>
            <span style={{ color: 'var(--border)' }}>&bull;</span>
            <span style={{ color: 'var(--non-breaking)' }}>{summary.non_breaking_count} Non-breaking</span>
          </div>
        )}

        <button
          onClick={onOpenCompare}
          style={{
            background: 'var(--ink)',
            color: 'var(--surface)',
            border: 'none',
            borderRadius: '6px',
            padding: '0.45rem 0.95rem',
            fontSize: '0.85rem',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Compare contracts
        </button>

        <div style={{ display: 'flex', gap: '0.4rem' }}>
          <button
            onClick={onDownloadJson}
            title="Download full comparison result as JSON"
            style={{
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              padding: '0.45rem 0.75rem',
              fontSize: '0.82rem',
              cursor: 'pointer',
              fontWeight: 500,
            }}
          >
            JSON report
          </button>
          <button
            onClick={onDownloadHtml}
            title="Download self-contained, escaped HTML report"
            style={{
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              padding: '0.45rem 0.75rem',
              fontSize: '0.82rem',
              cursor: 'pointer',
              fontWeight: 500,
            }}
          >
            HTML report
          </button>
        </div>
      </div>
    </header>
  );
};
