# Property Test: Inter-Note Coherence Validation

## Overview

This property test validates **Property 16: Inter-Note Coherence Validation** which ensures that the CoherenceValidator correctly verifies consistency across multiple financial statement annexes.

## Requirements Validated

- **Requirement 10.1**: Validation du total des immobilisations (Notes 3A-3E vs Bilan Actif)
- **Requirement 10.2**: Validation des dotations aux amortissements (Notes 3A-3E vs Compte de Résultat)
- **Requirement 10.3**: Validation de la continuité temporelle (Solde Clôture N-1 = Solde Ouverture N)

## Property Statement

**For any** complete set of calculated notes, when the CoherenceValidator validates them, it must verify that:

1. **Total Immobilizations**: The sum of Notes 3A-3E (Incorporeal, Tangible, Financial, Deferred Charges, Foreign Exchange Differences) equals the balance sheet assets
2. **Depreciation Charges**: The sum of depreciation charges from Notes 3A-3E equals the income statement
3. **Temporal Continuity**: Closing balances from year N-1 equal opening balances for year N across all notes

## Test Structure

### Hypothesis Strategies

#### `st_note_immobilisation(note_name)`
Generates a coherent immobilization note with:
- 2-5 detail lines
- 1 total line
- Coherent formulas: VNC = Gross - Depreciation
- Realistic amounts (100K to 10M)

#### `st_ensemble_notes_coherent()`
Generates a coherent set of 5 immobilization notes (3A-3E) with:
- Internal coherence for each note
- Consistent totals across notes

#### `st_ensemble_notes_incoherent()`
Generates a set of notes with intentional inconsistencies:
- Modifies totals in random notes
- Introduces 10-50% discrepancies

### Property Tests

#### 1. `test_property_inter_note_coherence_total_immobilisations`
**Property**: For any coherent set of notes, total immobilizations validation must succeed.

**Validates**:
- Coherence flag is True
- Deviation is negligible (< 1.0)
- Validations are recorded
- Total is positive
- Details contain all 5 notes

**Requirements**: 10.1, 10.2

#### 2. `test_property_inter_note_coherence_dotations_amortissements`
**Property**: For any coherent set of notes, depreciation charges validation must succeed.

**Validates**:
- Coherence flag is True
- Deviation is negligible (< 1.0)
- Validations are recorded
- Total depreciation is non-negative
- Details contain depreciation by note

**Requirements**: 10.1, 10.2

#### 3. `test_property_inter_note_coherence_continuite_temporelle`
**Property**: For any set of notes, temporal continuity must be validated.

**Validates**:
- Returns a dictionary of results
- Each note has a result tuple (bool, float)
- Deviations are non-negative
- Validations are recorded

**Requirements**: 10.3, 10.4

#### 4. `test_property_inter_note_coherence_detection_incoherence`
**Property**: For any set of notes with intentional inconsistencies, at least one inconsistency must be detected.

**Validates**:
- Coherence rate < 100%
- Alert system functions correctly

**Requirements**: 10.1, 10.2, 10.4

#### 5. `test_property_taux_coherence_global`
**Property**: For any coherent set of notes, global coherence rate must be >= 95%.

**Validates**:
- Rate is between 0 and 100
- Rate >= 95% for coherent notes
- No critical alerts are emitted

**Requirements**: 10.5, 10.6

#### 6. `test_property_rapport_coherence_generation`
**Property**: For any set of notes, HTML coherence report must be generated with all required sections.

**Validates**:
- Report is non-empty string
- Valid HTML structure
- Contains essential sections (title, global rate, validations)
- Contains metadata (date, note count)

**Requirements**: 10.7

## Unit Tests

### `test_coherence_ensemble_notes_simple`
Tests with a simple set of 2 notes (3A, 3B) with coherent values.

### `test_detection_incoherence_total`
Tests detection of inconsistency in totals.

### `test_rapport_html_structure`
Tests HTML report structure and content.

## Running the Tests

```bash
# Run all property tests
pytest py_backend/Doc\ calcul\ notes\ annexes/Tests/test_coherence_validator_inter_note.py -v

# Run with coverage
pytest py_backend/Doc\ calcul\ notes\ annexes/Tests/test_coherence_validator_inter_note.py --cov=Modules.coherence_validator

# Run specific test
pytest py_backend/Doc\ calcul\ notes\ annexes/Tests/test_coherence_validator_inter_note.py::test_property_inter_note_coherence_total_immobilisations -v
```

## Expected Results

All property tests should pass, demonstrating that:

1. ✅ Total immobilizations validation works correctly for coherent notes
2. ✅ Depreciation charges validation works correctly for coherent notes
3. ✅ Temporal continuity validation works correctly
4. ✅ Inconsistencies are detected in incoherent notes
5. ✅ Global coherence rate is calculated correctly (>= 95% for coherent notes)
6. ✅ HTML coherence report is generated with all required sections

## Configuration

- **Max examples**: 50 for main tests, 30 for complex tests, 20 for report generation
- **Deadline**: 60 seconds per test
- **Hypothesis profile**: default (100 examples, 60s deadline)

## Notes

- The tests use realistic financial amounts (100K to 10M)
- VNC (Net Book Value) is always validated to be >= 0
- Temporal continuity tests may not apply to all notes (depends on available columns)
- The coherence validator compares notes against themselves when no external reference (balance sheet, income statement) is available
- Intentional inconsistencies are introduced by modifying totals by 10-50%

## Integration with Task 10.1

This property test complements the CoherenceValidator implementation (Task 10.1) by:
- Validating all public methods of the CoherenceValidator class
- Testing with randomly generated but realistic data
- Ensuring edge cases are handled correctly
- Verifying that the 95% coherence threshold is enforced

## Success Criteria

✅ All property tests pass  
✅ Code coverage > 90% for coherence_validator.py  
✅ No false positives (coherent notes flagged as incoherent)  
✅ No false negatives (incoherent notes flagged as coherent)  
✅ HTML report generation works for all input combinations
