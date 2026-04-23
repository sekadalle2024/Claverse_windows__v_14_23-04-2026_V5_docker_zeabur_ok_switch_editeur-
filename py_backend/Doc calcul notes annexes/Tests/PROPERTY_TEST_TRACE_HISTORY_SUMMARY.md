# Property Test Summary: Trace History Management

## Property 23: Trace History Management

**Feature**: calcul-notes-annexes-syscohada  
**Validates**: Requirements 15.7

### Property Statement

*For any* note annexe generated multiple times, the system must maintain the 10 most recent trace files, automatically deleting older traces.

### Test Coverage

This property test suite validates that the `TraceManager.gerer_historique()` method correctly manages trace file history by:

1. **Keeping the correct number of traces**: Only `max_historique` most recent files are retained
2. **Deleting older traces**: Files beyond the limit are automatically removed
3. **Using modification time**: Most recent files are determined by `mtime`, not filename
4. **Handling edge cases**: Works correctly with fewer traces than the limit, no traces, etc.
5. **Being idempotent**: Multiple calls with the same limit don't delete additional files
6. **Supporting dynamic limits**: Decreasing the limit deletes more files as expected

### Test Functions

#### 1. `test_property_23_trace_history_management`
**Purpose**: Core property test validating history management  
**Strategy**: Creates multiple trace files and verifies correct retention/deletion  
**Properties Verified**:
- Only `max_historique` files remain after cleanup
- The most recent files are kept
- Older files are deleted
- Remaining files are valid JSON traces

**Hypothesis Configuration**:
- `max_examples=100`
- `deadline=None`
- Generates 5-25 traces with max_historique of 1-15

#### 2. `test_property_23_history_with_fewer_traces_than_max`
**Purpose**: Edge case when traces < max_historique  
**Strategy**: Creates fewer traces than the limit  
**Properties Verified**:
- No files are deleted when count is below limit
- All created files remain after cleanup

**Hypothesis Configuration**:
- `max_examples=50`
- Tests with `num_traces = max(1, max_historique - 2)`

#### 3. `test_property_23_default_max_historique_is_10`
**Purpose**: Validates default behavior  
**Strategy**: Calls `gerer_historique()` without arguments  
**Properties Verified**:
- Default limit is 10 traces
- Exactly 10 most recent files are kept when more exist

**Hypothesis Configuration**:
- `max_examples=50`
- Creates 15-30 traces to test default limit

#### 4. `test_property_23_history_preserves_most_recent_by_mtime`
**Purpose**: Validates ordering by modification time  
**Strategy**: Creates files with deliberate timestamp ordering  
**Properties Verified**:
- Files are ordered by `mtime`, not filename
- Most recent by `mtime` are kept, regardless of name

**Hypothesis Configuration**:
- `max_examples=50`
- Uses reverse filename ordering to test mtime priority

#### 5. `test_property_23_history_with_no_existing_traces`
**Purpose**: Edge case with no traces  
**Strategy**: Calls history management with empty directory  
**Properties Verified**:
- No exceptions are raised
- Function completes successfully
- No files exist after cleanup

**Hypothesis Configuration**:
- `max_examples=30`
- Tests graceful handling of empty state

#### 6. `test_property_23_multiple_history_calls_are_idempotent`
**Purpose**: Validates idempotency  
**Strategy**: Calls `gerer_historique()` twice with same limit  
**Properties Verified**:
- Second call doesn't delete additional files
- Same files remain after both calls
- File count is stable

**Hypothesis Configuration**:
- `max_examples=50`
- Creates 12-25 traces with limit of 10

#### 7. `test_property_23_decreasing_max_historique_deletes_more_files`
**Purpose**: Validates dynamic limit adjustment  
**Strategy**: Calls with decreasing limits  
**Properties Verified**:
- Lower limit deletes more files
- File count decreases appropriately
- Most recent files are still kept

**Hypothesis Configuration**:
- `max_examples=50`
- Uses two different limits with `max_historique_2 < max_historique_1`

### Hypothesis Strategies

#### `st_numero_note()`
Generates valid note numbers (01-33) as zero-padded strings.

#### `st_num_traces()`
Generates number of traces to create (5-25) to test various scenarios.

#### `st_max_historique()`
Generates max_historique values (1-15) for testing different limits.

### Requirements Validation

This test suite validates **Requirement 15.7**:

> THE System SHALL conserver l'historique des 10 dernières générations de chaque note

**How it's validated**:
1. ✅ Default limit of 10 is enforced
2. ✅ Configurable limit via `max_historique` parameter
3. ✅ Automatic deletion of older traces
4. ✅ Preservation of most recent traces by modification time
5. ✅ Graceful handling of edge cases (no traces, fewer than limit)
6. ✅ Idempotent behavior on repeated calls
7. ✅ Dynamic limit adjustment support

### Test Execution

Run all trace history tests:
```bash
pytest py_backend/Doc\ calcul\ notes\ annexes/Tests/test_trace_history_management.py -v --hypothesis-show-statistics
```

Run specific test:
```bash
pytest py_backend/Doc\ calcul\ notes\ annexes/Tests/test_trace_history_management.py::test_property_23_trace_history_management -v
```

Run with increased examples:
```bash
pytest py_backend/Doc\ calcul\ notes\ annexes/Tests/test_trace_history_management.py -v --hypothesis-profile=ci
```

### Expected Results

All tests should pass, demonstrating that:
- ✅ History management correctly limits trace files
- ✅ Most recent traces are preserved
- ✅ Older traces are automatically deleted
- ✅ Edge cases are handled gracefully
- ✅ Behavior is idempotent and predictable
- ✅ Dynamic limit adjustment works correctly

### Integration with Requirement 15.7

This property test ensures that the trace history management feature meets the specification:

**Requirement 15.7**: "THE System SHALL conserver l'historique des 10 dernières générations de chaque note"

**Test Coverage**:
- ✅ Default 10-trace limit is enforced
- ✅ Configurable limit for flexibility
- ✅ Automatic cleanup of old traces
- ✅ Preservation of audit trail for recent generations
- ✅ Disk space management through automatic deletion

### Notes

1. **File System Dependency**: These tests interact with the file system and create/delete actual files in the `Traces/` directory. Cleanup is performed in `finally` blocks to ensure test isolation.

2. **Timing Sensitivity**: Tests use `time.sleep(0.01)` to ensure different modification times. This may need adjustment on very fast or very slow systems.

3. **Idempotency**: The idempotency test is crucial for ensuring that automated cleanup scripts can safely run multiple times without unintended side effects.

4. **Dynamic Limits**: The ability to decrease `max_historique` is important for disk space management in production environments.

5. **Modification Time**: Using `mtime` (modification time) rather than filename ensures correct ordering even if files are renamed or created out of order.

### Related Tests

- `test_trace_manager_property.py`: Property 22 - Calculation Traceability
- `test_trace_manager_simple.py`: Unit tests for TraceManager basic functionality

### Maintenance

When updating the `TraceManager.gerer_historique()` implementation:
1. Ensure all property tests still pass
2. Update test strategies if new parameters are added
3. Add new test cases for new edge cases
4. Update this documentation with any changes

### Performance Considerations

- Each test creates and deletes multiple files (5-30 traces)
- Total test suite execution time: ~10-30 seconds depending on system
- File I/O is the main performance bottleneck
- Consider running with `--hypothesis-profile=dev` for faster feedback during development
