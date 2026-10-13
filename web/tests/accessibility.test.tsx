import React from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axe from 'axe-core';
import { App } from '../src/App';
import sample from '../public/sample/result.json';

// React Flow needs a layout engine. These tests deliberately cover the text
// alternative, not graph keyboard/zoom behavior or rendered visual contrast.
vi.mock('../src/components/ImpactMap', () => ({ ImpactMap: ({onSelectOperation}: {onSelectOperation: (label: string) => void}) =>
  <button onClick={() => onSelectOperation('DELETE /orders/{orderId}')}>Select removed operation</button> }));
afterEach(() => { cleanup(); vi.unstubAllGlobals(); window.location.hash = ''; });
const spec = JSON.stringify({openapi: '3.0.3', info: {title: 'Synthetic', version: '1'}, paths: {}});

async function studio(compareResponse?: () => Promise<unknown>) {
  vi.stubGlobal('fetch', vi.fn((url: string) => url === '/sample/result.json'
    ? Promise.resolve({ok: true, json: async () => sample})
    : compareResponse?.()));
  const user = userEvent.setup();
  render(<App />);
  await screen.findByRole('button', {name: /All \(11\)/});
  return user;
}
async function openInputs(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole('button', {name: /Compare contracts/i}));
  return screen.getByRole('dialog', {name: 'Compare OpenAPI Contracts'});
}
async function fillInputs(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByLabelText('Baseline (current contract)'));
  await user.paste(spec);
  await user.click(screen.getByLabelText('Candidate (proposed contract)'));
  await user.paste(spec);
}

describe('bounded accessibility regressions', () => {
  it('has named landmarks, one h1 and a working first skip link', async () => {
    const user = await studio();
    expect(screen.getAllByRole('heading', {level: 1})).toHaveLength(1);
    expect(screen.getAllByRole('main')).toHaveLength(1);
    await user.tab();
    expect(document.activeElement).toBe(screen.getByRole('link', {name: 'Skip to findings'}));
    await user.keyboard('{Enter}');
    expect(document.activeElement).toBe(screen.getByRole('main'));
  });

  it('contains modal focus in both directions, isolates background and restores trigger on Escape', async () => {
    const user = await studio();
    const trigger = screen.getByRole('button', {name: /Compare contracts/i});
    const dialog = await openInputs(user);
    const first = screen.getByRole('button', {name: 'Close dialog'});
    const last = screen.getByRole('button', {name: 'Run comparison'});
    expect(document.activeElement).toBe(first);
    expect(document.getElementById('studio-content')?.hasAttribute('inert')).toBe(true);
    await user.tab({shift: true});
    expect(document.activeElement).toBe(last);
    await user.tab();
    expect(document.activeElement).toBe(first);
    await user.keyboard('{Escape}');
    expect(dialog.isConnected).toBe(false);
    expect(document.getElementById('studio-content')?.hasAttribute('inert')).toBe(false);
    expect(document.activeElement).toBe(trigger);
  });

  it('focuses and describes each empty field, clears stale invalid state on correction', async () => {
    const user = await studio();
    await openInputs(user);
    const baseline = screen.getByLabelText('Baseline (current contract)');
    const candidate = screen.getByLabelText('Candidate (proposed contract)');
    await user.click(screen.getByRole('button', {name: 'Run comparison'}));
    expect(document.activeElement).toBe(baseline);
    expect(baseline.getAttribute('aria-invalid')).toBe('true');
    expect(document.getElementById(baseline.getAttribute('aria-describedby')!)?.textContent).toBe('Please provide a baseline specification.');
    await user.paste(spec);
    expect(baseline.hasAttribute('aria-invalid')).toBe(false);
    await user.click(screen.getByRole('button', {name: 'Run comparison'}));
    expect(document.activeElement).toBe(candidate);
    expect(candidate.getAttribute('aria-invalid')).toBe('true');
    expect(document.getElementById(candidate.getAttribute('aria-describedby')!)?.textContent).toBe('Please provide a candidate specification.');
  });

  it('exposes filter and native finding selection states to keyboard users', async () => {
    const user = await studio();
    const filter = screen.getByRole('button', {name: 'Breaking (5)'});
    filter.focus();
    await user.keyboard(' ');
    expect(filter.getAttribute('aria-pressed')).toBe('true');
    expect(screen.getByRole('button', {name: 'All (11)'}).getAttribute('aria-pressed')).toBe('false');
    const findings = document.querySelectorAll<HTMLButtonElement>('.finding-button');
    expect(findings).toHaveLength(5);
    findings[0].focus();
    await user.keyboard('{Enter}');
    expect(findings[0].getAttribute('aria-pressed')).toBe('true');
    findings[1].focus();
    await user.keyboard(' ');
    expect(findings[1].getAttribute('aria-pressed')).toBe('true');
    expect(findings[0].getAttribute('aria-pressed')).toBe('false');
  });

  it('names both upload controls and associates oversize upload errors with the correct field', async () => {
    const user = await studio();
    await openInputs(user);
    expect(screen.getByLabelText('Upload baseline file')).toHaveProperty('type', 'file');
    const upload = screen.getByLabelText('Upload candidate file');
    await user.upload(upload, new File(['x'.repeat(1024 * 1024 + 1)], 'synthetic.yaml', {type: 'application/yaml'}));
    expect(document.activeElement).toBe(upload);
    expect(upload.getAttribute('aria-invalid')).toBe('true');
    expect(document.getElementById(upload.getAttribute('aria-describedby')!)?.textContent).toContain('Candidate exceeds the 1 MiB');
    await user.click(screen.getByRole('button', {name: 'Swap Baseline and Candidate'}));
    expect(upload.hasAttribute('aria-invalid')).toBe(false);
  });

  it('selects operation evidence ahead of global metadata from keyboard map activation', async () => {
    const user = await studio();
    const node = screen.getByRole('button', {name: 'Select removed operation'});
    node.focus();
    await user.keyboard('{Enter}');
    expect(screen.getByRole('button', {name: /OP-01 Operation/}).getAttribute('aria-pressed')).toBe('true');
  });

  it('announces loading/completion in a stable region and exposes busy state', async () => {
    let resolve!: (value: unknown) => void;
    const user = await studio(() => new Promise(r => { resolve = r; }));
    const status = screen.getByRole('status');
    await openInputs(user);
    await fillInputs(user);
    await user.click(screen.getByRole('button', {name: 'Run comparison'}));
    expect(screen.getByRole('button', {name: 'Running comparison...'}).hasAttribute('disabled')).toBe(true);
    expect(document.querySelector('main')?.getAttribute('aria-busy')).toBe('true');
    expect(status.textContent).toMatch(/Comparing/);
    resolve({ok: true, json: async () => sample});
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    expect(screen.getByRole('status')).toBe(status);
    expect(status.textContent).toContain('Comparison complete.');
    expect(status.textContent).toContain('11 findings; 1 coverage gaps.');
    expect(screen.getByRole('main').getAttribute('aria-busy')).toBe('false');
  });

  it('announces server failure, retains input and identifies the previous result as stale', async () => {
    const user = await studio(async () => ({ok: false, json: async () => ({message: 'Candidate document is invalid.'})}));
    await openInputs(user);
    await fillInputs(user);
    await user.click(screen.getByRole('button', {name: 'Run comparison'}));
    expect(await screen.findByRole('alert')).toHaveProperty('textContent', 'Candidate document is invalid.');
    expect(screen.getByLabelText('Candidate (proposed contract)')).toHaveProperty('value', spec);
    await user.keyboard('{Escape}');
    expect(screen.getByRole('status').textContent).toContain('Showing the previous comparison');
  });

  it.each(['studio', 'input', 'explanation'])('passes axe structural rules for %s (graph and contrast excluded)', async (surface) => {
    const user = await studio();
    if (surface === 'input') await openInputs(user);
    if (surface === 'explanation') await user.click(screen.getByRole('button', {name: /Recorded example/}));
    const audit = await axe.run(document.body, {rules: {'color-contrast': {enabled: false}}});
    expect(audit.violations.map(v => ({id: v.id, targets: v.nodes.map(n => n.target)}))).toEqual([]);
  });
});
