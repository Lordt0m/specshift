import React, { useState } from 'react';
import { useDialogFocus } from '../useDialogFocus';

interface InputModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCompare: (baseline: string, candidate: string) => Promise<void>;
  isLoading: boolean;
  errorMessage: string | null;
  onInputChange: () => void;
}

export const InputModal: React.FC<InputModalProps> = ({
  isOpen,
  onClose,
  onCompare,
  isLoading,
  errorMessage,
  onInputChange,
}) => {
  const [baselineText, setBaselineText] = useState<string>('');
  const [candidateText, setCandidateText] = useState<string>('');
  const [localError, setLocalError] = useState<string | null>(null);
  useDialogFocus(isOpen, onClose);

  if (!isOpen) return null;

  const handleFileUpload = (
    e: React.ChangeEvent<HTMLInputElement>,
    setter: (val: string) => void,
    sideName: string
  ) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 1024 * 1024) {
      setLocalError(`${sideName} exceeds the 1 MiB size cap (${(file.size / 1024).toFixed(0)} KB).`);
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      setter(content);
      onInputChange();
      setLocalError(null);
    };
    reader.onerror = () => {
      setLocalError(`Failed to read ${sideName} file.`);
    };
    reader.readAsText(file, 'utf-8');
  };

  const handleSwap = () => {
    const temp = baselineText;
    setBaselineText(candidateText);
    setCandidateText(temp);
    onInputChange();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!baselineText.trim()) {
      setLocalError('Please provide a baseline specification.');
      return;
    }
    if (!candidateText.trim()) {
      setLocalError('Please provide a candidate specification.');
      return;
    }
    if ([baselineText, candidateText].some((value) => new TextEncoder().encode(value).length > 1024 * 1024)) {
      setLocalError('Each document must be at most 1 MiB in UTF-8.');
      return;
    }
    setLocalError(null);
    try {
      await onCompare(baselineText, candidateText);
      onClose();
    } catch {
      // Error handled via props errorMessage
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
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
          maxWidth: '850px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 8px 30px rgba(0,0,0,0.18)',
        }}
      >
        <div
          style={{
            padding: '1.25rem 1.5rem',
            borderBottom: '1px solid var(--border)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <h2 id="modal-title" style={{ fontSize: '1.15rem', fontWeight: 700 }}>
              Compare OpenAPI Contracts
            </h2>
            <p style={{ fontSize: '0.82rem', color: 'var(--secondary)', marginTop: '0.2rem' }}>
              Upload files or paste raw OpenAPI 3.0.0 &ndash; 3.0.3 (JSON or restricted YAML).
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close dialog"
            style={{
              background: 'none',
              border: 'none',
              fontSize: '1.3rem',
              cursor: 'pointer',
              color: 'var(--secondary)',
              lineHeight: 1,
            }}
          >
            &times;
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
          <div style={{ padding: '1.25rem 1.5rem', overflowY: 'auto', flex: 1 }}>
            {(localError || errorMessage) && (
              <div
                role="alert"
                style={{
                  background: 'var(--breaking-bg)',
                  border: '1px solid var(--breaking-border)',
                  color: 'var(--breaking)',
                  padding: '0.75rem 1rem',
                  borderRadius: '6px',
                  fontSize: '0.85rem',
                  marginBottom: '1rem',
                }}
              >
                {localError || errorMessage}
              </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 280px), 1fr))', gap: '1.25rem' }}>
              {/* Baseline Column */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                  <label htmlFor="baseline-input" style={{ fontWeight: 600, fontSize: '0.85rem' }}>
                    Baseline (current contract)
                  </label>
                  <label
                    style={{
                      fontSize: '0.75rem',
                      color: 'var(--highlight)',
                      cursor: 'pointer',
                      textDecoration: 'underline',
                    }}
                  >
                    Upload file
                    <input
                      type="file"
                      accept=".json,.yaml,.yml"
                      aria-label="Upload baseline file"
                      onChange={(e) => handleFileUpload(e, setBaselineText, 'Baseline')}
                    />
                  </label>
                </div>
                <textarea
                  id="baseline-input"
                  value={baselineText}
                  onChange={(e) => { setBaselineText(e.target.value); onInputChange(); }}
                  placeholder="Paste OpenAPI 3.0 baseline specification..."
                  rows={14}
                  style={{
                    width: '100%',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.8rem',
                    padding: '0.6rem',
                    borderRadius: '6px',
                    border: '1px solid var(--border)',
                    background: 'var(--canvas)',
                    resize: 'vertical',
                  }}
                />
              </div>

              {/* Candidate Column */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                  <label htmlFor="candidate-input" style={{ fontWeight: 600, fontSize: '0.85rem' }}>
                    Candidate (proposed contract)
                  </label>
                  <label
                    style={{
                      fontSize: '0.75rem',
                      color: 'var(--highlight)',
                      cursor: 'pointer',
                      textDecoration: 'underline',
                    }}
                  >
                    Upload file
                    <input
                      type="file"
                      accept=".json,.yaml,.yml"
                      aria-label="Upload candidate file"
                      onChange={(e) => handleFileUpload(e, setCandidateText, 'Candidate')}
                    />
                  </label>
                </div>
                <textarea
                  id="candidate-input"
                  value={candidateText}
                  onChange={(e) => { setCandidateText(e.target.value); onInputChange(); }}
                  placeholder="Paste OpenAPI 3.0 candidate specification..."
                  rows={14}
                  style={{
                    width: '100%',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.8rem',
                    padding: '0.6rem',
                    borderRadius: '6px',
                    border: '1px solid var(--border)',
                    background: 'var(--canvas)',
                    resize: 'vertical',
                  }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'center', marginTop: '0.75rem' }}>
              <button
                type="button"
                onClick={handleSwap}
                style={{
                  background: 'none',
                  border: '1px solid var(--border)',
                  borderRadius: '4px',
                  padding: '0.3rem 0.75rem',
                  fontSize: '0.78rem',
                  cursor: 'pointer',
                  color: 'var(--secondary)',
                }}
              >
                &rlarr; Swap Baseline and Candidate
              </button>
            </div>

            <div
              style={{
                marginTop: '1.25rem',
                padding: '0.85rem 1rem',
                background: 'var(--canvas)',
                borderRadius: '6px',
                border: '1px solid var(--border)',
                fontSize: '0.78rem',
                color: 'var(--secondary)',
                lineHeight: 1.4,
              }}
            >
              <strong>Privacy Notice:</strong> Both specifications are transmitted to the server for in-memory comparison
              under Policy v1. The application does not intentionally retain inputs. Providers may keep access logs;
              do not submit secrets. The free API may take about a minute to wake. Internal references only;
              external URLs are prohibited. Limit: 1 MiB per document.
            </div>
          </div>

          <div
            style={{
              padding: '1rem 1.5rem',
              borderTop: '1px solid var(--border)',
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '0.75rem',
              background: 'var(--surface)',
            }}
          >
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              style={{
                background: 'none',
                border: '1px solid var(--border)',
                borderRadius: '6px',
                padding: '0.5rem 1rem',
                fontSize: '0.85rem',
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              style={{
                background: 'var(--ink)',
                color: 'var(--surface)',
                border: 'none',
                borderRadius: '6px',
                padding: '0.5rem 1.25rem',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: isLoading ? 'not-allowed' : 'pointer',
                opacity: isLoading ? 0.7 : 1,
              }}
            >
              {isLoading ? 'Running comparison...' : 'Run comparison'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
