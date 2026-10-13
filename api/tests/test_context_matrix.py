"""Bounded conformance matrix: explicit schema edits, not JSON Schema equivalence."""
from copy import deepcopy
import pytest
from api.tests.test_release_regressions import SCHEMA_CASES, compare
from api.comparison.parse import resolve_pointer
from api.comparison.engine import _make_stable_id

REVERSE = {
    'SC-01': ('SC-01', 'review_required', 'review_required'),
    'SC-02': ('SC-03', 'non_breaking', 'breaking'),
    'SC-03': ('SC-02', 'breaking', 'non_breaking'),
    'SC-04': ('SC-05', 'non_breaking', 'breaking'),
    'SC-05': ('SC-04', 'breaking', 'non_breaking'),
    'SC-06': ('SC-04', 'breaking', 'non_breaking'),
    'SC-07': ('SC-06', 'review_required', 'review_required'),
    'SC-08': ('SC-09', 'breaking', 'non_breaking'),
    'SC-09': ('SC-08', 'non_breaking', 'breaking'),
    'SC-10': ('SC-11', 'non_breaking', 'breaking'),
    'SC-11': ('SC-10', 'breaking', 'non_breaking'),
    'SC-12': ('SC-13', 'non_breaking', 'breaking'),
    'SC-13': ('SC-12', 'breaking', 'non_breaking'),
}


def shared_document(schema, nested):
    ref = {'$ref': '#/components/schemas/Shared'}
    if nested:
        ref = {'$ref': '#/components/schemas/Envelope'}
    spec = {'openapi': '3.0.3', 'info': {'title': 'Synthetic matrix', 'version': '1'},
            'paths': {}, 'components': {'schemas': {'Shared': deepcopy(schema)}}}
    if nested:
        spec['components']['schemas']['Envelope'] = {
            'type': 'object', 'properties': {'batch/~': {'type': 'array', 'items': {
                '$ref': '#/components/schemas/Shared'}}}}
    for path in ['/a', '/b']:
        spec['paths'][path] = {
            'post': {'requestBody': {'content': {'application/json': {'schema': deepcopy(ref)}}},
                     'responses': {'204': {'description': 'ok'}}},
            'get': {'responses': {'200': {'description': 'ok', 'content': {
                'application/json': {'schema': deepcopy(ref)}}}}}}
    # This control must never acquire a contextual finding or gap.
    spec['paths']['/control'] = {'get': {'responses': {'204': {'description': 'ok'}}}}
    return spec


def assert_evidence(finding, baseline, candidate):
    for side, spec, pointer in [('before', baseline, 'origin_pointer'),
                                ('after', candidate, 'candidate_pointer')]:
        if finding[side + '_presence'] == 'absent':
            assert finding[side] is None
        else:
            assert resolve_pointer(spec, finding[pointer]) == finding[side]


@pytest.mark.parametrize('before,after,rule,request_class,response_class', SCHEMA_CASES)
@pytest.mark.parametrize('reverse', [False, True], ids=['forward', 'reverse'])
@pytest.mark.parametrize('nested', [False, True], ids=['shared', 'nested-shared'])
def test_schema_context_matrix(before, after, rule, request_class, response_class, reverse, nested):
    if reverse:
        before, after = after, before
        rule, request_class, response_class = REVERSE[rule]
    baseline, candidate = shared_document(before, nested), shared_document(after, nested)
    result = compare(baseline, candidate)
    matches = [f for f in result['findings'] if f['rule_id'] == rule]
    assert len(matches) == 2  # one per context, not one per operation
    for context, classification, method in [('request', request_class, 'POST'),
                                             ('response', response_class, 'GET')]:
        finding = next(f for f in matches if f['context'] == context)
        assert finding['classification'] == classification
        assert finding['affected_operations'] == [method + ' /a', method + ' /b']
        pointer = finding['origin_pointer'] or finding['candidate_pointer']
        assert pointer.startswith('#/components/schemas/Shared')
        identity_suffix = {'SC-01': ['type'], 'SC-02': ['enum-rem'], 'SC-03': ['enum-add'],
                           'SC-04': ['name'], 'SC-05': ['name'], 'SC-06': ['name'],
                           'SC-07': ['name'], 'SC-08': ['nullable'], 'SC-09': ['nullable'],
                           'SC-10': ['minimum'], 'SC-11': ['minimum'], 'SC-12': [], 'SC-13': []}
        assert finding['id'] == _make_stable_id('finding', rule.lower(), context,
                                               '#/components/schemas/Shared', *identity_suffix[rule])
        assert_evidence(finding, baseline, candidate)
    assert result == compare(baseline, candidate)
    assert len({f['id'] for f in result['findings']}) == len(result['findings'])
    assert compare(baseline, baseline)['findings'] == []
    assert compare(candidate, candidate)['findings'] == []
    assert result['coverage_gaps'] == []


@pytest.mark.parametrize('nested', [False, True])
def test_unchanged_shared_gap_reaches_every_consumer(nested):
    schema = {'type': 'string', 'pattern': '^a'}
    spec = shared_document(schema, nested)
    result = compare(spec, spec)
    assert result['findings'] == []
    assert len(result['coverage_gaps']) == 1
    gap = result['coverage_gaps'][0]
    assert gap['pointer'] == '#/components/schemas/Shared'
    assert gap['construct'] == 'pattern'
    assert gap['affected_operations'] == ['GET /a', 'GET /b', 'POST /a', 'POST /b']
    assert result['summary']['covered_operations'] == 1
    assert result['summary']['conclusion'] == 'Review required; compatibility not established'


@pytest.mark.parametrize('context,expected', [('request', 'breaking'), ('response', 'non_breaking')])
def test_nested_inline_escaped_evidence(context, expected):
    from api.tests.test_release_regressions import schema_document
    before = {'type': 'object', 'properties': {'batch/~': {'type': 'array', 'items': {
        'type': 'string', 'maxLength': 10}}}}
    after = deepcopy(before)
    after['properties']['batch/~']['items']['maxLength'] = 5
    baseline, candidate = schema_document(before, context), schema_document(after, context)
    finding = next(f for f in compare(baseline, candidate)['findings'] if f['rule_id'] == 'SC-10')
    assert finding['origin_pointer'].endswith('/properties/batch~1~0/items/maxLength')
    assert finding['candidate_pointer'] == finding['origin_pointer']
    assert finding['classification'] == expected
    assert_evidence(finding, baseline, candidate)


@pytest.mark.parametrize('kind,key,old,new', [
    ('number', 'minimum', 1, 2), ('number', 'maximum', 10, 5),
    ('string', 'minLength', 1, 2), ('string', 'maxLength', 10, 5),
    ('array', 'minItems', 1, 2), ('array', 'maxItems', 10, 5),
])
@pytest.mark.parametrize('reverse', [False, True])
def test_all_bound_families_nested_shared(kind, key, old, new, reverse):
    before = {'type': kind, key: old}
    after = {'type': kind, key: new}
    if kind == 'array':
        before['items'] = after['items'] = {'type': 'string'}
    if reverse:
        before, after = after, before
    baseline, candidate = shared_document(before, True), shared_document(after, True)
    result = compare(baseline, candidate)
    matches = [f for f in result['findings'] if f['rule_id'] == ('SC-11' if reverse else 'SC-10')]
    assert len(matches) == 2
    for f in matches:
        assert f['origin_pointer'] == f['candidate_pointer'] == '#/components/schemas/Shared/' + key
        assert f['classification'] == ('non_breaking' if (f['context'] == 'request') == reverse else 'breaking')
        assert f['affected_operations'] == [('POST' if f['context'] == 'request' else 'GET') + ' /' + p for p in ['a', 'b']]
        assert_evidence(f, baseline, candidate)


@pytest.mark.parametrize('before,after', [
    ({'type': 'integer', 'minimum': 1}, {'type': 'number', 'minimum': 2}),
    ({'minimum': 1}, {'minimum': 2}),
    ({'type': 'string', 'minimum': 1}, {'type': 'string', 'minimum': 2}),
    ({'type': 'number', 'minimum': 1, 'exclusiveMinimum': True},
     {'type': 'number', 'minimum': 2, 'exclusiveMinimum': True}),
])
def test_ambiguous_bounds_never_receive_set_direction_verdict(before, after):
    result = compare(shared_document(before, True), shared_document(after, True))
    assert not any(f['rule_id'] in {'SC-10', 'SC-11'} for f in result['findings'])
    assert result['summary']['review_count'] > 0
    assert 'compatibility not established' in result['summary']['conclusion']


def test_recursive_shared_consumers_preserve_findings_and_gaps():
    before = {'type': 'object', 'properties': {
        'value': {'type': 'string', 'enum': ['a']},
        'next': {'$ref': '#/components/schemas/Shared'}}, 'futureConstraint': True}
    after = deepcopy(before)
    after['properties']['value']['enum'].append('b')
    result = compare(shared_document(before, True), shared_document(after, True))
    matches = [f for f in result['findings'] if f['rule_id'] == 'SC-03']
    assert len(matches) == 2
    for f in matches:
        assert f['affected_operations'] == [('POST' if f['context'] == 'request' else 'GET') + ' /' + p for p in ['a', 'b']]
    assert result['coverage_gaps'][0]['affected_operations'] == ['GET /a', 'GET /b', 'POST /a', 'POST /b']
    assert result['summary']['covered_operations'] == 1


def test_mutual_cycle_with_different_entry_schema_preserves_later_evidence():
    before = {'type': 'object', 'properties': {
        'aaa-next': {'$ref': '#/components/schemas/Inner'},
        'zzz-value': {'type': 'string', 'enum': ['a'], 'pattern': '^a'}}}
    baseline = shared_document(before, True)
    baseline['components']['schemas']['Inner'] = {'type': 'object', 'properties': {
        'parent': {'$ref': '#/components/schemas/Shared'}}}
    baseline['paths']['/c'] = deepcopy(baseline['paths']['/a'])
    op = baseline['paths']['/c']
    op['post']['requestBody']['content']['application/json']['schema']['$ref'] = '#/components/schemas/Inner'
    op['get']['responses']['200']['content']['application/json']['schema']['$ref'] = '#/components/schemas/Inner'
    candidate = deepcopy(baseline)
    candidate['components']['schemas']['Shared']['properties']['zzz-value']['enum'].append('b')
    result = compare(baseline, candidate)
    for f in result['findings']:
        assert f['affected_operations'] == [('POST' if f['context'] == 'request' else 'GET') + ' /' + p for p in ['a', 'b', 'c']]
    assert result['coverage_gaps'][0]['affected_operations'] == ['GET /a', 'GET /b', 'GET /c', 'POST /a', 'POST /b', 'POST /c']
    assert result['summary']['covered_operations'] == 1


@pytest.mark.parametrize('kind,forward_rule,reverse_rule', [
    ('operation', 'OP-02', 'OP-01'), ('required_parameter', 'PA-01', 'PA-03'),
    ('optional_parameter', 'PA-02', 'PA-03'), ('parameter_required', 'PA-01', 'PA-02'),
    ('body_required', 'RB-01', 'RB-02'), ('request_media', 'MD-02', 'MD-01'),
    ('response_status', 'RS-02', 'RS-01'), ('response_media', 'RS-02', 'RS-01'),
    ('operation_id', 'MT-02', 'MT-02'),
])
@pytest.mark.parametrize('reverse', [False, True])
def test_operation_contract_reverse_cases(kind, forward_rule, reverse_rule, reverse):
    from api.tests.test_release_regressions import document
    baseline = document()
    op = baseline['paths']['/test']['get']
    if kind == 'parameter_required':
        op['parameters'] = [{'name': 'q', 'in': 'query', 'required': False, 'schema': {'type': 'string'}}]
    if kind in {'body_required', 'request_media'}:
        op['requestBody'] = {'required': False, 'content': {'application/json': {'schema': {'type': 'string'}}}}
    if kind == 'operation_id':
        op['operationId'] = 'oldName'
    candidate = deepcopy(baseline)
    change = candidate['paths']['/test']['get']
    if kind == 'operation':
        candidate['paths']['/new'] = {'get': {'responses': {'204': {'description': 'ok'}}}}
    elif kind in {'required_parameter', 'optional_parameter'}:
        change['parameters'] = [{'name': 'q', 'in': 'query', 'required': kind == 'required_parameter', 'schema': {'type': 'string'}}]
    elif kind == 'parameter_required':
        change['parameters'][0]['required'] = True
    elif kind == 'body_required':
        change['requestBody']['required'] = True
    elif kind == 'request_media':
        change['requestBody']['content']['application/problem+json'] = {'schema': {'type': 'string'}}
    elif kind == 'response_status':
        change['responses']['404'] = {'description': 'missing'}
    elif kind == 'response_media':
        change['responses']['200']['content']['application/problem+json'] = {'schema': {'type': 'string'}}
    elif kind == 'operation_id':
        change['operationId'] = 'newName'
    if reverse:
        baseline, candidate = candidate, baseline
    result = compare(baseline, candidate)
    expected_rule = reverse_rule if reverse else forward_rule
    matches = [f for f in result['findings'] if f['rule_id'] == expected_rule]
    assert len(matches) == 1
    finding = matches[0]
    expected_class = {'OP-01': 'breaking', 'OP-02': 'non_breaking', 'PA-01': 'breaking',
                      'PA-02': 'non_breaking', 'PA-03': 'review_required', 'RB-01': 'breaking',
                      'RB-02': 'non_breaking', 'MD-01': 'breaking', 'MD-02': 'non_breaking',
                      'RS-01': 'review_required', 'RS-02': 'review_required', 'MT-02': 'review_required'}
    assert finding['classification'] == expected_class[expected_rule]
    assert finding['affected_operations'] == ['GET /new' if kind == 'operation' else 'GET /test']
    assert_evidence(finding, baseline, candidate)
    assert result == compare(baseline, candidate)
    assert compare(baseline, baseline)['findings'] == []
    assert compare(candidate, candidate)['findings'] == []
