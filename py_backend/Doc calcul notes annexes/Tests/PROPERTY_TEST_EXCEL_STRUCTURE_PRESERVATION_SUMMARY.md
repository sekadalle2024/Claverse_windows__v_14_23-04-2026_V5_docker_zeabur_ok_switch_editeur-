# Property Test 15: Excel Export Structure Preservation - Summary

## Overview

This property test validates that the Excel_Exporter module correctly preserves the structure of note annexe data when exporting to Excel format, with proper formatting conforming to SYSCOHADA standards.

**Test File**: `test_excel_exporter_structure_preservation.py`

**Property Statement**: For any note annexe exported to Excel, the Excel_Exporter must create a worksheet with the same structure as the HTML table (headers, data rows, total row), with numeric formatting for amounts and styling (borders, header colors).

**Validates**: Requirements 9.1, 9.2, 9.3, 9.4, 9.5

## Property Tests Implemented

### 1. `test_property_excel_structure_preservation`

**Property**: For any generated note annexe with valid data, the Excel export must preserve:
- Number of rows (data + headers)
- Number of columns
- Cell values
- Header formatting
- Amount formatting
- Borders
- Total row styling

**Strategy**: Uses `st_note_annexe_complete()` to generate complete notes with 3-10 data rows plus a total row.

**Verifications**:
1. ✓ File creation
2. ✓ Worksheet existence with correct name
3. ✓ Title formatting (bold, blue background)
4. ✓ Number of data rows matches DataFrame
5. ✓ Number of columns (1 label + data columns)
6. ✓ Group headers (row 3) with correct titles and formatting
7. ✓ Sub-headers (row 4) with correct labels and formatting
8. ✓ Data values match DataFrame values
9. ✓ Numeric format with thousand separators (#,##0)
10. ✓ Zero/null values displayed as '-'
11. ✓ Total row formatting (bold, gray background)
12. ✓ Borders on all data cells (thin style)
13. ✓ Column widths (40 for label, 15 for data columns)

**Requirements Validated**:
- 9.1: Export of single note to Excel
- 9.2: Structure preservation (headers, rows, totals)
- 9.3: Formatting with borders and colors
- 9.4: Numeric formatting with thousand separators
- 9.5: File creation and saving

### 2. `test_property_excel_multiple_notes_export`

**Property**: For any number of notes (1-10), the batch export must create one worksheet per note with correct structure.

**Strategy**: Generates 1-10 notes and exports them all using `exporter_toutes_notes()`.

**Verifications**:
1. ✓ File creation
2. ✓ Number of worksheets equals number of notes
3. ✓ Worksheet names match note numbers
4. ✓ Each worksheet has minimum required rows and columns
5. ✓ Each worksheet title contains correct note number

**Requirements Validated**:
- 9.2: Batch export of all notes
- 9.6: Multiple worksheets in single file

### 3. `test_property_excel_timestamp_filename`

**Property**: The filename generation must correctly add or omit timestamp based on the parameter.

**Strategy**: Tests both `avec_timestamp=True` and `avec_timestamp=False`.

**Verifications**:
1. ✓ File creation
2. ✓ With timestamp: filename contains timestamp in format YYYYMMDD_HHMMSS
3. ✓ With timestamp: filename starts with base name
4. ✓ With timestamp: timestamp has exactly 15 characters
5. ✓ Without timestamp: filename is exactly the base name

**Requirements Validated**:
- 9.5: Timestamped filename generation

## Unit Tests Implemented

### 1. `test_excel_exporter_empty_dataframe`

Tests handling of empty DataFrames without raising exceptions.

### 2. `test_excel_exporter_large_numbers`

Tests correct handling and formatting of very large monetary amounts (up to 999,999,999,999.99).

## Hypothesis Strategies

### `st_note_annexe_complete()`

Generates complete note annexe data including:
- Note number (3A, 3B, 3C, 3D, 3E, 4, 5)
- Note title
- DataFrame with 3-10 data rows + total row
- Column configuration with groups and labels

**Ensures**:
- Valid note structure
- Coherent total row (sum of all data rows)
- Complete column configuration

## Test Configuration

- **Max Examples**: 50 for main property test, 20 for multiple notes, 10 for timestamp
- **Deadline**: 30 seconds per test
- **Hypothesis Profile**: default (from conftest.py)

## Running the Tests

```bash
# Run all property tests
pytest test_excel_exporter_structure_preservation.py -v

# Run with detailed output
pytest test_excel_exporter_structure_preservation.py -v -s

# Run specific test
pytest test_excel_exporter_structure_preservation.py::test_property_excel_structure_preservation -v

# Run with Hypothesis statistics
pytest test_excel_exporter_structure_preservation.py -v --hypothesis-show-statistics
```

## Expected Output

```
test_excel_exporter_structure_preservation.py::test_property_excel_structure_preservation PASSED
test_excel_exporter_structure_preservation.py::test_property_excel_multiple_notes_export PASSED
test_excel_exporter_structure_preservation.py::test_property_excel_timestamp_filename PASSED
test_excel_exporter_structure_preservation.py::test_excel_exporter_empty_dataframe PASSED
test_excel_exporter_structure_preservation.py::test_excel_exporter_large_numbers PASSED
```

## Key Assertions

### Structure Preservation
- Number of rows and columns match input DataFrame
- All data values are correctly transferred
- Cell types are preserved (numbers vs strings)

### Formatting Verification
- Title: Bold, white text, dark blue background (2C3E50)
- Group headers: Bold, white text, gray-blue background (34495E)
- Sub-headers: White text, gray background (7F8C8D)
- Total row: Bold, gray background (ECF0F1)
- Numeric format: #,##0 (thousand separators, 0 decimals)
- Borders: Thin style on all data cells

### File Management
- Files created in temporary directories
- Cleanup after each test
- Timestamp format: YYYYMMDD_HHMMSS
- Directory creation if needed

## Coverage

This property test provides comprehensive coverage of:

1. **Single note export** (Requirement 9.1)
2. **Batch export** (Requirement 9.2)
3. **Formatting application** (Requirement 9.3)
4. **Numeric formatting** (Requirement 9.4)
5. **Timestamped filenames** (Requirement 9.5)

## Integration with Task 8.1

This property test complements the simple test from Task 8.1 by:
- Testing with randomly generated data (property-based)
- Verifying structure preservation across many examples
- Testing edge cases (empty DataFrames, large numbers)
- Validating batch export functionality
- Checking timestamp generation

## Notes

- Uses temporary directories for all file operations
- Cleans up all test files after execution
- Tests are independent and can run in any order
- Comprehensive assertions for both structure and formatting
- Validates SYSCOHADA-specific formatting requirements

## Task Completion

✓ Task 8.2 completed successfully

**Deliverables**:
1. Property test file: `test_excel_exporter_structure_preservation.py`
2. Summary document: `PROPERTY_TEST_EXCEL_STRUCTURE_PRESERVATION_SUMMARY.md`

**Requirements Validated**: 9.1, 9.2, 9.3, 9.4, 9.5
