# Quick Start: Trace History Management Property Tests

## What This Tests

Property 23: **Trace History Management** - The system must maintain the 10 most recent trace files, automatically deleting older traces.

## Run the Tests

### Run all trace history tests:
```bash
cd py_backend/Doc\ calcul\ notes\ annexes/Tests
pytest test_trace_history_management.py -v --hypothesis-show-statistics
```

### Run a specific test:
```bash
pytest test_trace_history_management.py::test_property_23_trace_history_management -v
```

### Run with more examples (thorough testing):
```bash
pytest test_trace_history_management.py -v --hypothesis-profile=ci
```

## What Gets Tested

✅ **Core Functionality**:
- Only `max_historique` most recent traces are kept
- Older traces are automatically deleted
- Files are ordered by modification time (mtime)

✅ **Edge Cases**:
- Fewer traces than the limit (no deletion)
- No existing traces (graceful handling)
- Default limit of 10 traces

✅ **Advanced Behavior**:
- Idempotent operations (multiple calls safe)
- Dynamic limit adjustment (decreasing limit)
- Correct file ordering by mtime, not filename

## Expected Output

```
test_trace_history_management.py::test_property_23_trace_history_management PASSED
test_trace_history_management.py::test_property_23_history_with_fewer_traces_than_max PASSED
test_trace_history_management.py::test_property_23_default_max_historique_is_10 PASSED
test_trace_history_management.py::test_property_23_history_preserves_most_recent_by_mtime PASSED
test_trace_history_management.py::test_property_23_history_with_no_existing_traces PASSED
test_trace_history_management.py::test_property_23_multiple_history_calls_are_idempotent PASSED
test_trace_history_management.py::test_property_23_decreasing_max_historique_deletes_more_files PASSED

====== 7 passed in X.XXs ======
```

## Quick Validation

To quickly verify the trace history management works:

```python
from Modules.trace_manager import TraceManager

# Create trace manager
trace_mgr = TraceManager("3A")

# Create 15 traces
for i in range(15):
    trace_mgr.enregistrer_metadata(f"balance_{i}.xlsx")
    trace_mgr.sauvegarder_trace(f"trace_note_3A_test_{i:02d}.json")

# Manage history (keep only 10)
trace_mgr.gerer_historique(max_historique=10)

# Check: should have exactly 10 traces
import os
traces = [f for f in os.listdir(trace_mgr.traces_dir) if f.startswith("trace_note_3A_")]
print(f"Traces remaining: {len(traces)}")  # Should print: 10
```

## What This Validates

**Requirement 15.7**: "THE System SHALL conserver l'historique des 10 dernières générations de chaque note"

- ✅ Default limit of 10 traces
- ✅ Configurable limit via parameter
- ✅ Automatic deletion of old traces
- ✅ Preservation of recent traces
- ✅ Disk space management

## Common Issues

### Issue: Tests fail with "Permission denied"
**Solution**: Ensure the `Traces/` directory is writable and not locked by another process.

### Issue: Tests are slow
**Solution**: Use the dev profile for faster feedback:
```bash
pytest test_trace_history_management.py -v --hypothesis-profile=dev
```

### Issue: Timing-related failures
**Solution**: The tests use small delays (`time.sleep(0.01)`) to ensure different modification times. On very fast systems, increase this delay in the test code.

## Next Steps

After running these tests:
1. ✅ Verify all tests pass
2. ✅ Check the test summary for statistics
3. ✅ Review any failures and fix the implementation
4. ✅ Run integration tests to verify end-to-end behavior

## Related Documentation

- `PROPERTY_TEST_TRACE_HISTORY_SUMMARY.md` - Detailed test documentation
- `TASK_11_1_TRACE_MANAGER_SUMMARY.md` - TraceManager implementation guide
- `test_trace_manager_property.py` - Property 22 (Calculation Traceability)
