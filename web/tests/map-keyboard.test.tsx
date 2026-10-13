import React from 'react';
import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ImpactMap } from '../src/components/ImpactMap';
import sample from '../public/sample/result.json';

// Exercise SpecShift's node content; React Flow's pan/zoom is a browser gate.
vi.mock('@xyflow/react', () => ({
  ReactFlow: ({nodes, children}: {nodes: {id: string; data: {label: React.ReactNode}}[]; children: React.ReactNode}) =>
    <div>{nodes.map(n => <div key={n.id}>{n.data.label}</div>)}{children}</div>,
  Background: () => null, Controls: () => null, MarkerType: {ArrowClosed: 'arrowclosed'},
}));
afterEach(cleanup);
it('activates an operation node by Enter and Space with a method/path name', async () => {
  const user = userEvent.setup();
  const select = vi.fn();
  render(<ImpactMap graphData={sample.graph} selectedFinding={null} onSelectOperation={select} />);
  const node = screen.getByRole('button', {name: 'GET /orders', exact: true});
  node.focus();
  await user.keyboard('{Enter}');
  await user.keyboard(' ');
  expect(select.mock.calls).toEqual([['GET /orders'], ['GET /orders']]);
});
