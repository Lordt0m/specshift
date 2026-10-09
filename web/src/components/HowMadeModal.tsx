import React from 'react';

interface HowMadeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const HowMadeModal: React.FC<HowMadeModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="how-made-title"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(23, 33, 43, 0.65)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '1rem',
      }}
    >
      <div
        style={{
          background: 'var(--surface)',
          borderRadius: '8px',
          border: '1px solid var(--border)',
          width: '100%',
          maxWidth: '650px',
          maxHeight: '85vh',
          overflowY: 'auto',
          padding: '1.5rem',
          boxShadow: '0 8px 30px rgba(0,0,0,0.18)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 id="how-made-title" style={{ fontSize: '1.2rem', fontWeight: 700 }}>
            How This Comparison Was Made
          </h2>
          <button
            onClick={onClose}
            aria-label="Close dialog"
            style={{
              background: 'none',
              border: 'none',
              fontSize: '1.3rem',
              cursor: 'pointer',
              color: 'var(--secondary)',
            }}
          >
            &times;
          </button>
        </div>

        <div style={{ fontSize: '0.88rem', color: 'var(--ink)', lineHeight: 1.5, display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
          <p>
            <strong>Stateless Synthetic Sample:</strong> This view is initialized with a recorded comparison of a fictional
            order management contract. The result was deterministically generated directly by the pure Python comparison
            engine during the project build process.
          </p>

          <p>
            <strong>Compatibility Policy v1:</strong> Assesses replacing the baseline server with the candidate while
            preserving client request acceptance and response guarantees. All classifications cite versioned rules
            (e.g., OP-01, SC-03, SC-04, SC-10).
          </p>

          <p>
            <strong>Explicit Uncertainty:</strong> The presence of unsupported schema composition (such as <code>oneOf</code> in
            <code>Order.discount</code>) generates a <strong>Coverage Gap</strong>. Under SpecShift&apos;s conservative policy,
            coverage gaps prevent an unqualified clean verdict even if no breaking rules trigger.
          </p>

          <p>
            <strong>Live Comparisons:</strong> When you upload or paste your own OpenAPI 3.0 contracts, they are sent to the
            live Python/Django service for strictly in-memory analysis and are not retained.
          </p>
        </div>

        <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end' }}>
          <button
            onClick={onClose}
            style={{
              background: 'var(--ink)',
              color: 'var(--surface)',
              border: 'none',
              borderRadius: '6px',
              padding: '0.5rem 1.25rem',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
