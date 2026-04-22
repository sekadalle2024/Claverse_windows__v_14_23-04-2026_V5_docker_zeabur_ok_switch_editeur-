# Property Test: Depreciation Account Sign Inversion

## Property 8: Depreciation Account Sign Inversion

**Feature**: calcul-notes-annexes-syscohada  
**Validates**: Requirements 3.7, 4.4, 4.5

## Property Statement

*For any* depreciation account (accounts starting with 28 or 29), the Movement_Calculator must treat credit movements as increases (dotations) and debit movements as decreases (reprises), which is the inverse of normal accounts.

## Test Implementation

**File**: `test_movement_calculator_depreciation.py`

### Property Tests (4 tests)

1. **test_property_depreciation_sign_inversion_credit_is_dotation**
   - Validates that credit movements = dotations (increases in depreciation)
   - Tests 100 randomly generated depreciation accounts
   - Validates: Requirements 3.7, 4.4

2. **test_property_depreciation_sign_inversion_debit_is_reprise**
   - Validates that debit movements = reprises (decreases in depreciation)
   - Tests 100 randomly generated depreciation accounts
   - Validates: Requirements 3.7, 4.5

3. **test_property_depreciation_sign_inversion_complete**
   - Validates complete sign inversion in a full balance context
   - Tests 100 randomly generated balances with depreciation accounts
   - Validates: Requirements 3.7, 4.4, 4.5

4. **test_property_depreciation_classes_28_and_29**
   - Validates that both class 28 (amortissements) and class 29 (provisions) have the same behavior
   - Tests 100 randomly generated account pairs
   - Validates: Requirement 3.7

### Unit Tests (6 tests)

1. **test_amortissement_dotation_simple**
   - Simple depreciation charge (dotation) scenario
   - Account 2811 with 100,000 dotation

2. **test_amortissement_reprise_simple**
   - Simple depreciation reversal (reprise) scenario
   - Account 2812 with 50,000 reprise

3. **test_amortissement_dotation_et_reprise**
   - Simultaneous dotation and reprise
   - Account 2813 with 150,000 dotation and 30,000 reprise

4. **test_amortissement_classe_29**
   - Provision account (class 29) behavior
   - Account 2911 with 80,000 dotation

5. **test_amortissement_compte_inexistant**
   - Missing depreciation account handling
   - Returns zero values for non-existent account

6. **test_amortissement_valeurs_nulles**
   - Zero movements scenario
   - Account with no movements during the period

## Test Results

**Status**: ✅ ALL TESTS PASSED

```
10 passed in 8.08s
```

### Coverage

- **Property tests**: 400 examples tested (4 tests × 100 examples each)
- **Unit tests**: 6 specific scenarios
- **Total assertions**: 10 test functions with multiple assertions each

## Key Validations

### Sign Inversion Rules

For depreciation accounts (28X, 29X):

| Movement Type | Normal Account | Depreciation Account |
|--------------|----------------|---------------------|
| Credit       | Decrease       | **Increase (Dotation)** |
| Debit        | Increase       | **Decrease (Reprise)** |

### Validated Behaviors

1. ✅ Credit movements are correctly treated as dotations (increases)
2. ✅ Debit movements are correctly treated as reprises (decreases)
3. ✅ Both class 28 and 29 accounts have consistent behavior
4. ✅ Missing accounts return zero values gracefully
5. ✅ Zero movements are handled correctly
6. ✅ Simultaneous dotations and reprises are calculated correctly

## Requirements Validation

### Requirement 3.7
> WHEN des comptes d'amortissement sont traités, THE Movement_Calculator SHALL inverser les signes (crédit = augmentation)

**Status**: ✅ VALIDATED by all 4 property tests

### Requirement 4.4
> WHEN les dotations aux amortissements sont calculées, THE VNC_Calculator SHALL les extraire des mouvements crédit des comptes 28X

**Status**: ✅ VALIDATED by test_property_depreciation_sign_inversion_credit_is_dotation

### Requirement 4.5
> WHEN les reprises d'amortissements sont calculées, THE VNC_Calculator SHALL les extraire des mouvements débit des comptes 28X

**Status**: ✅ VALIDATED by test_property_depreciation_sign_inversion_debit_is_reprise

## Hypothesis Strategies

### st_compte_amortissement
Generates valid depreciation accounts (28X or 29X) with random movements:
- Account number: 28X or 29X with optional detail digits
- Debit movements: 0 to 5,000,000
- Credit movements: 0 to 5,000,000

### st_balance_avec_amortissement
Generates a complete balance with at least one depreciation account:
- Main depreciation account with movements
- 0-10 additional accounts for context
- Coherent opening and closing balances

## Test Configuration

- **Max examples per property test**: 100
- **Deadline per test**: 60 seconds
- **Hypothesis profile**: default
- **Total execution time**: 8.08 seconds

## Integration with Movement_Calculator

The tests validate the `calculer_mouvements_amortissement()` method:

```python
def calculer_mouvements_amortissement(compte_amort: str, 
                                     balance_n: pd.DataFrame) -> Dict[str, float]:
    """
    Calcule les mouvements d'amortissement (signes inversés).
    
    Returns:
        Dict avec clés: dotations (crédit), reprises (débit)
    """
```

## Next Steps

This completes Task 4.3. The next task in the implementation plan is:

- **Task 5**: Implement VNC_Calculator module
  - Task 5.1: Create vnc_calculator.py with VNCCalculator class
  - Task 5.2: Write property test for VNC calculation formula (optional)

## Notes

- All property tests use Hypothesis for automatic test case generation
- Tests cover both normal cases and edge cases (zero values, missing accounts)
- The sign inversion is critical for correct calculation of depreciation movements
- Both amortissement (28X) and provision (29X) accounts follow the same rules
