import React, { useEffect, useState, useCallback } from 'react';
import { ComparisonResult, Finding } from './types';
import { Header } from './components/Header';
import { ImpactMap } from './components/ImpactMap';
import { Inspector } from './components/Inspector';
import { OperationsList } from './components/OperationsList';
import { InputModal } from './components/InputModal';
import { HowMadeModal } from './components/HowMadeModal';

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
const escapeHtml = (text: string) => text.replace(/[&<>"']/g, (char) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
}[char]!));

export const App: React.FC = () => {
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [selectedFindingId, setSelectedFindingId] = useState<string | null>(null);
  const [isSample, setIsSample] = useState<boolean>(true);
  const [isStale, setIsStale] = useState<boolean>(false);
  const [isInputModalOpen, setIsInputModalOpen] = useState<boolean>(false);
  const [isHowMadeOpen, setIsHowMadeOpen] = useState<boolean>(false);
  const [isComparing, setIsComparing] = useState<boolean>(false);
  const [compareError, setCompareError] = useState<string | null>(null);
  const [lastInputs, setLastInputs] = useState<{baseline: string; candidate: string} | null>(null);
  const [reportError, setReportError] = useState<string | null>(null);

  // Load bundled recorded sample on mount
  useEffect(() => {
    fetch('/sample/result.json')
      .then((res) => {
        if (!res.ok) throw new Error('Could not load recorded sample');
        return res.json();
      })
      .then((data: ComparisonResult) => {
        setResult(data);
        setIsSample(true);
        // Default select the shared schema breaking finding (SC-03)
        const linkedFinding = data.findings.find((f) => f.id === window.location.hash.slice(1));
        const defaultFinding = linkedFinding || data.findings.find((f) => f.rule_id === 'SC-03') || data.findings[0];
        if (defaultFinding) {
          setSelectedFindingId(defaultFinding.id);
        }
      })
      .catch((err) => {
        console.error('Failed to load sample:', err);
      });
  }, []);

  // Synchronize selection with URL hash
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '');
      if (!hash) setSelectedFindingId(null);
      else {
        const finding = result?.findings.find((f) => f.id === hash);
        // A new comparison can update the hash before the previous result's
        // listener has been replaced. Do not discard its newly selected ID.
        if (finding) setSelectedFindingId(finding.id);
      }
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, [result]);

  const handleSelectFinding = useCallback((finding: Finding) => {
    setSelectedFindingId(finding.id);
    window.location.hash = finding.id;
  }, []);

  const handleClearSelection = useCallback(() => {
    setSelectedFindingId(null);
    history.replaceState(null, '', window.location.pathname + window.location.search);
  }, []);

  const handleSelectOperation = useCallback(
    (opLabel: string) => {
      if (!result) return;
      const matchingFinding = result.findings.find((f) => f.affected_operations.includes(opLabel));
      if (matchingFinding) {
        handleSelectFinding(matchingFinding);
      }
    },
    [result, handleSelectFinding]
  );

  const handleCompare = async (baseline: string, candidate: string) => {
    setIsComparing(true);
    setCompareError(null);
    try {
      const response = await fetch(`${API_BASE}/api/compare/`, {
        signal: AbortSignal.timeout(90000),
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ baseline, candidate }),
      });

      if (!response.ok) {
        let errData;
        try {
          errData = await response.json();
        } catch {
          errData = { message: `Comparison request failed with status ${response.status}` };
        }
        throw new Error(errData.message || 'Comparison failed');
      }

      const data: ComparisonResult = await response.json();
      setResult(data);
      setLastInputs({baseline, candidate});
      setIsSample(false);
      setIsStale(false);
      if (data.findings.length > 0) {
        handleSelectFinding(data.findings[0]);
      } else {
        handleClearSelection();
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Comparison failed';
      setCompareError(message);
      throw err;
    } finally {
      setIsComparing(false);
    }
  };

  const handleDownloadJson = () => {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `specshift-report-${result.policy_version}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadHtml = async () => {
    if (!result) return;
    // Attempt download from API if possible or create client-side self-contained HTML
    try {
      let htmlContent = `<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>SpecShift Report</title></head>
<body><h1>SpecShift Report</h1><p>Baseline to candidate. Full comparison, independent of UI filters.</p><pre>${escapeHtml(JSON.stringify(result, null, 2))}</pre></body></html>`;
      if (!isSample && lastInputs) {
        const response = await fetch(`${API_BASE}/api/report/`, {
          method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(lastInputs), signal: AbortSignal.timeout(90000),
        });
        if (!response.ok) throw new Error(`Report request failed (${response.status}). Retry shortly.`);
        htmlContent = await response.text();
      }
      const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'specshift-report.html';
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setReportError(err instanceof Error ? err.message : 'Report download failed.');
    }
  };

  const selectedFinding = result?.findings.find((f) => f.id === selectedFindingId) || null;

  return (
    <div className="app-container">
      <Header
        summary={result?.summary || null}
        policyVersion={result?.policy_version || 'v1'}
        isSample={isSample}
        isStale={isStale}
        onOpenCompare={() => setIsInputModalOpen(true)}
        onDownloadJson={handleDownloadJson}
        onDownloadHtml={handleDownloadHtml}
        onShowHowMade={() => setIsHowMadeOpen(true)}
      />

      {/* Main Studio Viewport */}
      <p role="status" style={{padding: '0.4rem 1.5rem'}}>{isComparing ? 'Comparing. The free API may take about a minute to wake.' : reportError || (isStale ? 'Showing the previous comparison. Run comparison to review edited inputs.' : '')}</p>
      <main className="app-main">
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
          {/* Top: Impact Map Canvas */}
          <div style={{ flex: 1, minHeight: '380px' }}>
            {result && (
              <ImpactMap
                graphData={result.graph}
                selectedFinding={selectedFinding}
                onSelectOperation={handleSelectOperation}
              />
            )}
          </div>

          {/* Bottom: Synchronized Findings & Operations List */}
          {result && (
            <OperationsList
              findings={result.findings}
              coverageGaps={result.coverage_gaps}
              selectedFindingId={selectedFindingId}
              onSelectFinding={handleSelectFinding}
            />
          )}
        </div>

        {/* Right Rail: Evidence Inspector */}
        <Inspector
          selectedFinding={selectedFinding}
          summary={result?.summary || null}
          onClearSelection={handleClearSelection}
        />
      </main>

      <InputModal
        isOpen={isInputModalOpen}
        onClose={() => setIsInputModalOpen(false)}
        onCompare={handleCompare}
        isLoading={isComparing}
        errorMessage={compareError}
        onInputChange={() => setIsStale(true)}
      />

      <HowMadeModal isOpen={isHowMadeOpen} onClose={() => setIsHowMadeOpen(false)} />
    </div>
  );
};
