# Property Test Summary: Mapping Lookup Consistency

**Feature**: calcul-notes-annexes-syscohada  
**Property**: 12 - Mapping Lookup Consistency  
**Task**: 9.2  
**Date**: 2026-04-22

## Property Statement

For any valid poste name in the correspondances_syscohada.json file, the Mapping_Manager must return the associated list of account roots, and adding new correspondences to the JSON must not require code changes.

## Requirements Validated

- **Requirement 7.2**: When a poste is searched, the Mapping_Manager shall return the list of associated account roots
- **Requirement 7.5**: The Mapping_Manager shall allow adding new correspondences without modifying Python code
- **Requirement 7.7**: The Mapping_Manager shall validate that each account root is a valid numeric string

## Test Implementation

### Test File
`py_backend/Doc calcul notes annexes/Tests/test_mapping_manager_property.py`

### Property Tests Implemented

1. **test_property_12_mapping_lookup_consistency**
   - Validates that for any generated correspondances dictionary, all postes can be looked up correctly
   - Handles duplicate libelles by combining all racines
   - Validates that all racines are numeric strings
   - Runs 100 examples with Hypothesis

2. **test_property_12_adding_new_correspondences_without_code_changes**
   - Validates that new correspondences can be added dynamically via API
   - Validates that added correspondences persist after save/reload
   - Skips cases with pre-existing duplicate libelles to avoid ambiguity
   - Runs 100 examples with Hypothesis

3. **test_property_12_all_account_roots_are_valid_numeric_strings**
   - Validates that all account roots in any correspondances dictionary are valid numeric strings
   - Validates root length is between 1 and 5 digits
   - Runs 100 examples with Hypothesis

4. **test_property_12_missing_poste_returns_empty_list**
   - Validates that looking up a non-existent poste returns an empty list without exceptions
   - Runs 50 examples with Hypothesis

5. **test_property_12_lookup_is_idempotent**
   - Validates that looking up the same poste multiple times returns identical results
   - Runs 50 examples with Hypothesis

6. **test_property_12_real_correspondances_file**
   - Validates the actual correspondances_syscohada.json file
   - Checks all 4 sections (bilan_actif, bilan_passif, charges, produits)
   - Handles duplicate libelles correctly (e.g., "Reprises de provisions", "Transferts de charges")
   - Validates all racines are numeric strings

7. **test_property_12_real_file_specific_lookups**
   - Tests specific known lookups from the real file
   - Validates "Frais de recherche et de développement" → includes "211"
   - Validates "Capital" → includes "101"
   - Validates "Achats de marchandises" → includes "601"
   - Validates "Ventes de marchandises" → includes "701"

## Key Implementation Details

### Handling Duplicate Libelles

The real correspondances_syscohada.json file contains duplicate libelles:
- "Reprises de provisions" appears twice (TJ with ["791"], TP with ["796", "797", "798"])
- "Transferts de charges" appears three times (TK, TQ, TW with different racines)

The MappingManager handles this by:
1. Returning ALL racines from all entries with the same libelle
2. Deduplicating the combined list while preserving order
3. When adding a new correspondence with an existing libelle, it updates the first matching entry

### Hypothesis Strategies

Custom strategies were created to generate realistic test data:
- `st_correspondances_dict()`: Generates valid correspondances dictionaries with 1-4 sections, each with 1-10 postes
- `st_poste_name()`: Generates valid poste names with French characters
- `st_account_root()`: Generates valid numeric account roots (1-5 digits)
- `st_section_name()`: Generates valid section names (bilan_actif, bilan_passif, charges, produits)

## Test Results

All 7 property tests pass successfully:
- ✓ test_property_12_mapping_lookup_consistency (100 examples)
- ✓ test_property_12_adding_new_correspondences_without_code_changes (100 examples)
- ✓ test_property_12_all_account_roots_are_valid_numeric_strings (100 examples)
- ✓ test_property_12_missing_poste_returns_empty_list (50 examples)
- ✓ test_property_12_lookup_is_idempotent (50 examples)
- ✓ test_property_12_real_correspondances_file
- ✓ test_property_12_real_file_specific_lookups

**Total execution time**: ~36 seconds

## Code Coverage

The property tests exercise:
- `MappingManager.__init__()`
- `MappingManager.charger_correspondances()`
- `MappingManager.obtenir_racines_compte()` - including duplicate handling
- `MappingManager.valider_racines()`
- `MappingManager.ajouter_correspondance()`
- `MappingManager.sauvegarder()`

## Bugs Found

The property tests revealed:
1. The real correspondances_syscohada.json file contains duplicate libelles, which is a data quality issue
2. The MappingManager needed to be updated to handle both list-based and dict-based JSON formats
3. The lookup function needed to combine racines from duplicate libelles

## Recommendations

1. **Data Quality**: Consider consolidating duplicate libelles in the real file, or document that duplicates are intentional
2. **API Enhancement**: Consider adding a method to remove correspondences
3. **Validation**: Consider adding validation to prevent duplicate libelles when adding new correspondences
4. **Documentation**: Document the duplicate handling behavior in the MappingManager docstrings

## Running the Tests

```bash
# Run all property tests
pytest py_backend/Doc\ calcul\ notes\ annexes/Tests/test_mapping_manager_property.py -v

# Run with Hypothesis statistics
pytest py_backend/Doc\ calcul\ notes\ annexes/Tests/test_mapping_manager_property.py -v --hypothesis-show-statistics

# Run a specific test
pytest py_backend/Doc\ calcul\ notes\ annexes/Tests/test_mapping_manager_property.py::test_property_12_real_correspondances_file -v
```

## Conclusion

Property 12 (Mapping Lookup Consistency) is fully validated. The MappingManager correctly:
- Returns associated account roots for any valid poste
- Allows adding new correspondences without code changes
- Validates that all account roots are numeric strings
- Handles duplicate libelles by combining racines
- Persists changes correctly

The implementation satisfies Requirements 7.2, 7.5, and 7.7.
