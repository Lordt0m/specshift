import React, { useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { GraphNode, GraphEdge, Finding } from '../types';

interface ImpactMapProps {
  graphData: {
    nodes: GraphNode[];
    edges: GraphEdge[];
  };
  selectedFinding: Finding | null;
  onSelectOperation?: (opLabel: string) => void;
}

export const ImpactMap: React.FC<ImpactMapProps> = ({
  graphData,
  selectedFinding,
  onSelectOperation,
}) => {
  // Determine highlighted nodes & edges based on selected finding
  const { highlightedNodeIds, affectedOpLabels, originNodeId } = useMemo(() => {
    const affected = new Set(selectedFinding?.affected_operations || []);
    let originId: string | null = null;

    if (selectedFinding?.origin_pointer) {
      if (selectedFinding.origin_pointer.includes('/components/schemas/')) {
        const schemaName = selectedFinding.origin_pointer.split('/components/schemas/')[1].split('/')[0];
        originId = `schema:${schemaName}`;
      } else if (selectedFinding.origin_pointer.includes('/paths/')) {
        // e.g. #/paths/~1orders~1{orderId}/delete
        const op = selectedFinding.affected_operations[0];
        if (op) {
          const [m, ...p] = op.split(' ');
          originId = `op:${m}_${p.join(' ')}`;
        }
      }
    } else if (selectedFinding?.affected_operations.length === 1) {
      const [m, ...p] = selectedFinding.affected_operations[0].split(' ');
      originId = `op:${m}_${p.join(' ')}`;
    }

    const highlighted = new Set<string>();
    if (originId) highlighted.add(originId);

    // Add affected operation nodes
    for (const node of graphData.nodes) {
      if (node.type === 'operation' && affected.has(node.label)) {
        highlighted.add(node.id);
      }
    }

    return {
      highlightedNodeIds: highlighted,
      affectedOpLabels: affected,
      originNodeId: originId,
    };
  }, [selectedFinding, graphData.nodes]);

  // Lay nodes out deterministically
  const initialNodes: Node[] = useMemo(() => {
    const opNodes = graphData.nodes.filter((n) => n.type === 'operation');
    const schemaNodes = graphData.nodes.filter((n) => n.type === 'schema');

    const result: Node[] = [];

    // Layer 1: Operations
    opNodes.forEach((n, idx) => {
      const isAffected = affectedOpLabels.has(n.label);
      const isHighlighted = highlightedNodeIds.has(n.id);
      const isDimmed = selectedFinding !== null && !isHighlighted;

      result.push({
        id: n.id,
        position: { x: 50 + idx * 260, y: 50 },
        data: {
          label: (
            <div
              style={{
                padding: '0.6rem 0.8rem',
                borderRadius: '6px',
                border: isAffected
                  ? '2px solid var(--breaking)'
                  : isHighlighted
                  ? '2px solid var(--highlight)'
                  : '1px solid var(--border)',
                background: isAffected ? 'var(--breaking-bg)' : 'var(--surface)',
                color: isAffected ? 'var(--breaking)' : 'var(--ink)',
                fontSize: '0.8rem',
                fontWeight: 600,
                opacity: isDimmed ? 0.4 : 1,
                boxShadow: isAffected ? '0 2px 8px rgba(182, 63, 55, 0.2)' : 'none',
                cursor: 'pointer',
              }}
              onClick={() => onSelectOperation && onSelectOperation(n.label)}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <span style={{ fontSize: '0.7rem', padding: '0.1rem 0.3rem', background: 'var(--canvas)', borderRadius: '3px' }}>
                  {n.method || 'OP'}
                </span>
                <span className="mono" style={{ fontSize: '0.78rem' }}>{n.path || n.label}</span>
              </div>
              {isAffected && (
                <div style={{ fontSize: '0.68rem', marginTop: '0.3rem', fontWeight: 700 }}>
                  &bull; Affected by finding
                </div>
              )}
            </div>
          ),
        },
        type: 'default',
      });
    });

    // Layer 2: Schemas
    schemaNodes.forEach((n, idx) => {
      const isOrigin = originNodeId === n.id;
      const isHighlighted = highlightedNodeIds.has(n.id);
      const isDimmed = selectedFinding !== null && !isHighlighted;

      result.push({
        id: n.id,
        position: { x: 80 + idx * 240, y: 220 },
        data: {
          label: (
            <div
              style={{
                padding: '0.6rem 0.8rem',
                borderRadius: '6px',
                border: isOrigin
                  ? '2px solid var(--highlight)'
                  : '1px solid var(--border)',
                background: isOrigin ? 'var(--highlight-bg)' : 'var(--surface)',
                color: 'var(--ink)',
                fontSize: '0.8rem',
                fontWeight: 600,
                opacity: isDimmed ? 0.4 : 1,
                boxShadow: isOrigin ? '0 2px 8px rgba(42, 96, 158, 0.2)' : 'none',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--secondary)' }}>schema:</span>
                <span className="mono" style={{ color: 'var(--highlight)' }}>{n.label}</span>
              </div>
              {isOrigin && (
                <div style={{ fontSize: '0.68rem', marginTop: '0.3rem', color: 'var(--highlight)', fontWeight: 700 }}>
                  [Origin of finding]
                </div>
              )}
            </div>
          ),
        },
        type: 'default',
      });
    });

    return result;
  }, [graphData.nodes, highlightedNodeIds, affectedOpLabels, originNodeId, selectedFinding, onSelectOperation]);

  const initialEdges: Edge[] = useMemo(() => {
    return graphData.edges.map((e) => {
      const isEdgeActive =
        highlightedNodeIds.has(e.source) && highlightedNodeIds.has(e.target);
      const isDimmed = selectedFinding !== null && !isEdgeActive;

      return {
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.label,
        animated: isEdgeActive,
        style: {
          stroke: isEdgeActive ? 'var(--highlight)' : 'var(--border)',
          strokeWidth: isEdgeActive ? 2.5 : 1.2,
          opacity: isDimmed ? 0.25 : 1,
        },
        labelStyle: {
          fontSize: '0.68rem',
          fill: isEdgeActive ? 'var(--highlight)' : 'var(--secondary)',
          fontWeight: isEdgeActive ? 600 : 400,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: isEdgeActive ? 'var(--highlight)' : 'var(--border)',
        },
      };
    });
  }, [graphData.edges, highlightedNodeIds, selectedFinding]);

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        height: '100%',
        background: 'var(--canvas)',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div
        style={{
          padding: '0.5rem 1rem',
          background: 'var(--surface)',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '0.78rem',
          color: 'var(--secondary)',
        }}
      >
        <div>
          <strong>Impact Map:</strong> Reachability indicates contract dependency, not proof of runtime failure.
        </div>
        {selectedFinding && (
          <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.75rem' }}>
            <span>Highlight: <strong>{selectedFinding.rule_id}</strong></span>
            <span>&bull;</span>
            <span>{selectedFinding.affected_operations.length} operations reachable</span>
          </div>
        )}
      </div>

      <div style={{ flex: 1, position: 'relative' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          fitView
          minZoom={0.3}
          maxZoom={1.8}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={true}
        >
          <Background color="#DCE3E3" gap={20} size={1} />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>
    </div>
  );
};
