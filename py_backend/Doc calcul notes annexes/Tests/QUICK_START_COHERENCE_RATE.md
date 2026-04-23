# Quick Start: Coherence Rate Calculation Property Test

## Overview

This guide shows how to run the property-based tests for coherence rate calculation (Property 17).

## Prerequisites

```bash
# Ensure you have the required packages
pip install pytest hypothesis pandas
```

## Running the Tests

### Run All Tests

```bash
# From the project root
pytest "py_backend/Doc calcul notes annexes/Tests/test_coherence_validator_rate.py" -v
```

### Run with Hypothesis Statistics

```bash
pytest "py_backend/Doc calcul notes annexes/Tests/test_coherence_validator_rate.py" -v --hypothesis-show-statistics
```

### Run Specific Property Test

```bash
# Test high coherence rate
pytest "py_backend/Doc calcul notes annexes/Tests/test_coherence_validator_rate.py::test_property_coherence_rate_high_coherence" -v

# Test critical alert emission
pytest "py_backend/Doc calcul notes annexes/Tests/test_coherence_validator_rate.py::test_property_coherence_rate_low_coherence_alert" -v

# Test rate calculation formula
pytest "py_backend/Doc calcul notes annexes/Tests/test_coherence_validator_rate.py::test_property_coherence_rate_calculation_formula" -v
```

### Run with Verbose Output

```bash
pytest "py_backend/Doc calcul notes annexes/Tests/test_coherence_validator_rate.py" -vv --tb=short
```

## Expected Output

```
===================== test session starts =====================
collected 10 items

test_coherence_validator_rate.py::test_property_coherence_rate_high_coherence PASSED [ 10%]
test_coherence_validator_rate.py::test_property_coherence_rate_low_coherence_alert PASSED [ 20%]
test_coherence_validator_rate.py::test_property_coherence_rate_calculation_formula PASSED [ 30%]
test_coherence_validator_rate.py::test_property_coherence_rate_percentage_range PASSED [ 40%]
test_coherence_validator_rate.py::test_property_coherence_rate_monotonicity PASSED [ 50%]
test_coherence_validator_rate.py::test_property_coherence_rate_alert_details PASSED [ 60%]
test_coherence_validator_rate.py::test_coherence_rate_100_percent PASSED [ 70%]
test_coherence_validator_rate.py::test_coherence_rate_below_95_percent PASSED [ 80%]
test_coherence_validator_rate.py::test_coherence_rate_empty_validations PASSED [ 90%]
test_coherence_validator_rate.py::test_coherence_rate_partial_validations PASSED [100%]

===================== 10 passed in 12.08s =====================
```

## What's Being Tested

### Property 17: Coherence Rate Calculation

The tests validate that the `Coherence_Validator` correctly:

1. **Calculates the global coherence rate** as:
   ```
   rate = (coherent validations / total validations) × 100
   ```

2. **Emits a critical alert** when the rate is below 95%

3. **Maintains rate properties:**
   - Always between 0 and 100
   - Monotonic (improving coherence doesn't decrease rate)
   - Accurate (matches manual calculation)

## Test Categories

### Property-Based Tests (6 tests)
- Generate random note sets with controlled deviations
- Test 30-50 examples per property
- Validate universal properties across all inputs

### Unit Tests (4 tests)
- Test specific scenarios (100% rate, < 95% rate, empty validations)
- Verify edge cases and boundary conditions

## Customizing Test Runs

### Change Number of Examples

Edit the test file and modify the `@settings` decorator:

```python
@given(notes=st_ensemble_notes_taux_eleve())
@settings(max_examples=100, deadline=60000)  # Run 100 examples instead of 50
def test_property_coherence_rate_high_coherence(notes):
    ...
```

### Run with Different Hypothesis Profiles

```bash
# Quick run (fewer examples)
pytest "py_backend/Doc calcul notes annexes/Tests/test_coherence_validator_rate.py" --hypothesis-profile=dev

# CI run (more examples)
pytest "py_backend/Doc calcul notes annexes/Tests/test_coherence_validator_rate.py" --hypothesis-profile=ci
```

## Troubleshooting

### Tests Take Too Long

Reduce the number of examples:
```python
@settings(max_examples=20, deadline=30000)
```

### Tests Fail with Timeout

Increase the deadline:
```python
@settings(max_examples=50, deadline=120000)  # 2 minutes
```

### Import Errors

Ensure you're in the correct directory and the module path is correct:
```bash
cd "py_backend/Doc calcul notes annexes"
pytest Tests/test_coherence_validator_rate.py -v
```

## Understanding Test Output

### Hypothesis Statistics

```
- during generate phase (2.11 seconds):
  - Typical runtimes: ~ 22-84 ms, of which ~ 17-71 ms in data generation
  - 50 passing examples, 0 failing examples, 0 invalid examples
- Stopped because settings.max_examples=50
```

This shows:
- **Total time:** 2.11 seconds for 50 examples
- **Runtime per example:** 22-84 ms
- **Data generation time:** 17-71 ms (time to create test data)
- **Results:** All 50 examples passed
- **Stop reason:** Reached the configured maximum examples

### Test Failure Example

If a test fails, Hypothesis will show:
```
Falsifying example: test_property_coherence_rate_high_coherence(
    notes={'note_3a': DataFrame(...)}
)
```

This is the minimal example that caused the failure, making debugging easier.

## Integration with CI/CD

Add to your CI pipeline:

```yaml
- name: Run Coherence Rate Property Tests
  run: |
    pytest "py_backend/Doc calcul notes annexes/Tests/test_coherence_validator_rate.py" \
      -v \
      --hypothesis-show-statistics \
      --junitxml=test-results/coherence-rate.xml
```

## Related Tests

- **test_coherence_validator_inter_note.py:** Tests inter-note coherence validation (Property 16)
- **test_coherence_validator_simple.py:** Unit tests for Coherence_Validator module

## Next Steps

After running these tests successfully:

1. Review the summary document: `PROPERTY_TEST_COHERENCE_RATE_SUMMARY.md`
2. Check the Coherence_Validator implementation: `Modules/coherence_validator.py`
3. Proceed to Task 11.1: Implement Trace_Manager module

## Support

For issues or questions:
- Check the test file comments for detailed property descriptions
- Review the Coherence_Validator module docstrings
- Consult the design document: `.kiro/specs/calcul-notes-annexes-syscohada/design.md`
