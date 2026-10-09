export type Classification = 'breaking' | 'review_required' | 'non_breaking';

export interface Finding {
  id: string;
  rule_id: string;
  classification: Classification;
  context: 'operation' | 'request' | 'response' | 'metadata';
  origin_pointer: string | null;
  candidate_pointer: string | null;
  before: unknown;
  before_presence: 'present' | 'absent' | 'null';
  after: unknown;
  after_presence: 'present' | 'absent' | 'null';
  explanation: string;
  policy_rule: string;
  affected_operations: string[];
}

export interface CoverageGap {
  id: string;
  pointer: string;
  construct: string;
  reason: string;
  affected_operations: string[];
}

export interface OperationItem {
  method: string;
  path: string;
  status: 'retained' | 'removed' | 'added';
}

export interface GraphNode {
  id: string;
  type: 'operation' | 'schema';
  label: string;
  pointer?: string;
  method?: string;
  path?: string;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label: string;
  context: 'request' | 'response' | 'reference';
}

export interface Summary {
  breaking_count: number;
  review_count: number;
  non_breaking_count: number;
  total_findings: number;
  coverage_gap_count: number;
  total_operations: number;
  covered_operations: number;
  conclusion: string;
}

export interface ComparisonResult {
  schema_version: string;
  engine_version: string;
  policy_version: string;
  input_digests: {
    baseline: string;
    candidate: string;
  };
  summary: Summary;
  operations: OperationItem[];
  findings: Finding[];
  coverage_gaps: CoverageGap[];
  graph: {
    nodes: GraphNode[];
    edges: GraphEdge[];
  };
  warnings: string[];
}
