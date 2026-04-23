# Property Test Summary: Trace Export Format Conversion

## Property 24: Trace Export Format Conversion

**Feature:** calcul-notes-annexes-syscohada  
**Validates:** Requirements 15.6

## Property Statement

*For any* trace file in JSON format, the system must be able to export it to CSV format preserving all calculation details for analysis in Excel.

## Test Coverage

### Main Property Test: `test_property_24_trace_export_format_conversion`

Verifies that JSON traces can be converted to CSV format with complete data preservation:

1. **CSV File Creation**: Trace can be exported to CSV format
2. **Header Structure**: CSV contains correct column headers
3. **Row Count**: One CSV row per source account (denormalized structure)
4. **Data Preservation**: All calculation details preserved (libellé, montant, source accounts)
5. **Excel Compatibility**: UTF-8-BOM encoding and semicolon delimiter
6. **Column Consistency**: All rows have same number of columns
7. **Round-Trip Capability**: CSV can be parsed back to verify data integrity
8. **Metadata Replication**: Metadata replicated across all rows for Excel filtering
9. **Parseable Format**: CSV is valid and parseable

### Edge Case Tests

#### `test_property_24_csv_export_with_empty_calculations`
- Verifies CSV export works even with no calculations
- Must still produce valid CSV with headers

#### `test_property_24_csv_preserves_special_characters`
- Verifies French accents and special characters are preserved
- UTF-8-BOM encoding prevents character corruption

#### `test_property_24_csv_enables_excel_analysis`
- Verifies CSV structure enables common Excel operations:
  - Filtering by note, libellé, or account
  - Pivot tables on metadata columns
  - Summing amounts by libellé
  - Grouping by source accounts

#### `test_property_24_json_to_csv_round_trip_integrity`
- Verifies complete information preservation from JSON to CSV
- Ensures auditor can reconstruct calculations from CSV alone
- Validates metadata, calculation count, and source account integrity

## CSV Format Specification

### Column Structure
```
Note | Titre | Date Génération | Fichier Balance | Hash MD5 | 
Libellé Ligne | Montant | Compte Source | Intitulé Compte | 
Valeur Compte | Type Valeur
```

### Format Details
- **Encoding**: UTF-8 with BOM (for Excel compatibility)
- **Delimiter**: Semicolon (`;`) - European Excel standard
- **Structure**: Denormalized - one row per source account
- **Metadata**: Replicated across all rows for filtering

### Example CSV Output
```csv
Note;Titre;Date Génération;Fichier Balance;Hash MD5;Libellé Ligne;Montant;Compte Source;Intitulé Compte;Valeur Compte;Type Valeur
3A;Immobilisations incorporelles;2026-04-23T10:30:00;P000 - BALANCE DEMO.xlsx;a1b2c3d4;Frais R&D;1500000.0;211;Frais de recherche;1500000.0;brut
3A;Immobilisations incorporelles;2026-04-23T10:30:00;P000 - BALANCE DEMO.xlsx;a1b2c3d4;Frais R&D;1500000.0;2811;Amort. Frais R&D;300000.0;amortissement
```

## Excel Analysis Capabilities

The CSV format enables:

1. **Filtering**: By note number, libellé, account number, or value type
2. **Pivot Tables**: Using metadata columns (note, date, balance file)
3. **Summing**: Aggregate amounts by libellé or account
4. **Sorting**: By any column for analysis
5. **Grouping**: By calculation line or source account
6. **Audit Trail**: Complete traceability from CSV alone

## Property Validation Strategy

### Hypothesis Strategy
- Generates random note numbers (01-33)
- Creates varied calculation data with multiple source accounts
- Tests with different balance file names
- Validates with 100 examples per test

### Assertions
1. CSV file exists and is readable
2. Headers match expected format
3. Row count equals sum of source accounts across all calculations
4. All data fields preserved with correct values
5. Encoding is UTF-8-BOM
6. Delimiter is semicolon
7. All rows have consistent column count
8. Metadata is consistent across all rows
9. Round-trip integrity maintained

## Requirements Validation

### Requirement 15.6
> THE System SHALL permettre l'export du fichier de trace en format CSV pour analyse dans Excel

**Validated by:**
- Main property test verifies CSV export functionality
- Edge cases verify robustness with empty data
- Special character test verifies French text handling
- Excel analysis test verifies practical usability
- Round-trip test verifies complete data preservation

## Running the Tests

```bash
# Run all trace export format conversion tests
pytest py_backend/Doc\ calcul\ notes\ annexes/Tests/test_trace_export_format_conversion.py -v

# Run with Hypothesis statistics
pytest py_backend/Doc\ calcul\ notes\ annexes/Tests/test_trace_export_format_conversion.py -v --hypothesis-show-statistics

# Run specific test
pytest py_backend/Doc\ calcul\ notes\ annexes/Tests/test_trace_export_format_conversion.py::test_property_24_trace_export_format_conversion -v

# Run with increased examples
pytest py_backend/Doc\ calcul\ notes\ annexes/Tests/test_trace_export_format_conversion.py -v --hypothesis-max-examples=200
```

## Test Results Interpretation

### Success Criteria
- All property tests pass with 100 examples
- CSV files are created successfully
- All data is preserved in conversion
- Excel compatibility is maintained
- Round-trip integrity is verified

### Common Failure Modes
1. **Encoding Issues**: Character corruption with special characters
2. **Delimiter Problems**: Wrong delimiter breaks Excel import
3. **Data Loss**: Missing fields in CSV conversion
4. **Format Inconsistency**: Rows with different column counts
5. **Metadata Corruption**: Inconsistent metadata across rows

## Integration with Trace Manager

The CSV export functionality is provided by the `TraceManager.exporter_csv()` method:

```python
trace_manager = TraceManager("3A")
trace_manager.enregistrer_metadata("balance.xlsx", "hash123")
trace_manager.enregistrer_calcul("Frais R&D", 1500000.0, comptes_sources)

# Export to CSV
csv_path = trace_manager.exporter_csv("trace_note_3A.csv")
```

## Benefits of CSV Export

1. **Excel Compatibility**: Direct import into Excel without conversion
2. **Audit Trail**: Complete calculation details in tabular format
3. **Analysis Flexibility**: Use Excel pivot tables, filters, and formulas
4. **Data Portability**: CSV is universal format for data exchange
5. **Human Readable**: Easy to review and verify calculations
6. **Archival**: Simple format for long-term storage

## Conclusion

Property 24 ensures that the trace export functionality provides complete, accurate, and Excel-compatible CSV output for audit and analysis purposes. The property-based tests validate this across a wide range of input scenarios, ensuring robustness and reliability.
