# Property Test Summary: HTML Generation Conformity

## Test Information

- **Property Number**: 11
- **Property Name**: HTML Generation Conformity
- **Test File**: `test_html_generator_conformity.py`
- **Date Created**: 2026-04-22
- **Status**: ✅ Implemented

## Property Statement

**Property 11: HTML Generation Conformity**

*For any* note annexe generated, the HTML_Generator must produce valid HTML containing a table with headers conforming to the official SYSCOHADA format, CSS styling with borders and alternating row colors, monetary amounts formatted with thousand separators and 0 decimals, and a total row with distinct styling.

## Requirements Validated

This property test validates the following requirements:

- **Requirement 6.2**: HTML must include a table with headers conforming to the official SYSCOHADA format
- **Requirement 6.3**: HTML must apply CSS styling with borders and alternating row colors
- **Requirement 6.4**: Monetary amounts must be formatted with thousand separators and 0 decimals
- **Requirement 6.5**: HTML must include a total row with distinct styling
- **Requirement 6.6**: HTML must use Courier New font for amounts to align digits

## Test Strategy

### Property-Based Testing Approach

The test uses **Hypothesis** to generate random test data:

- **Input Generation**:
  - Random number of lines (1-20) for the note annexe
  - Random monetary amounts using `st_montant()` strategy
  - Random note titles and numbers
  - Coherent financial data (respecting accounting equations)

- **Test Configuration**:
  - **Max Examples**: 100 iterations per test
  - **Deadline**: 60 seconds per test
  - **Shrinking**: Automatic minimal failing case identification

### Validation Checks

The property test performs comprehensive validation through helper functions:

#### 1. `assert_valid_html_structure(html)`
Validates basic HTML structure:
- Presence of `<html>`, `<head>`, `<body>` tags
- Presence of `<table>`, `<thead>`, `<tbody>` tags
- UTF-8 charset meta tag
- Title tag containing "NOTE"

**Validates**: Requirement 6.2 (partial)

#### 2. `assert_syscohada_headers_present(html, colonnes_config)`
Validates SYSCOHADA-compliant table headers:
- Two header rows (group headers and sub-headers)
- LIBELLÉ header with `rowspan=2`
- All configured group headers present with correct `colspan`
- All sub-headers present (Ouverture, Augmentations, etc.)
- Correct number of columns

**Validates**: Requirement 6.2 (complete)

#### 3. `assert_css_styling_present(html)`
Validates CSS styling presence:
- `<style>` tag exists with content
- Border styling defined (`border`, `border-collapse`)
- Table and cell styling present

**Validates**: Requirement 6.3 (partial - borders)

#### 4. `assert_alternating_row_colors(html)`
Validates alternating row colors:
- CSS defines `even-row` and `odd-row` classes or `nth-child` selectors
- Table rows have appropriate classes applied
- Different background colors for alternating rows

**Validates**: Requirement 6.3 (complete)

#### 5. `assert_monetary_formatting(html, df)`
Validates monetary amount formatting:
- All amounts are integers (0 decimals)
- Amounts ≥ 1000 have space separators
- Correct spacing pattern (every 3 digits from right)
- Zero amounts displayed as dash (-)
- No decimal points in formatted amounts

**Validates**: Requirement 6.4 (complete)

#### 6. `assert_total_row_present(html, titre_note)`
Validates total row presence and styling:
- At least one row contains "TOTAL"
- Total row has distinct CSS class (`total-row`)
- CSS defines special styling for total row
- Total row styling includes bold font and borders

**Validates**: Requirement 6.5 (complete)

#### 7. `assert_courier_font_for_amounts(html)`
Validates Courier New font usage:
- CSS includes "Courier New" or "Courier" font
- Font applied to monetary cells (`.montant-cell` or `td`)
- Monospace font family specified
- Font-family property set for amount cells

**Validates**: Requirement 6.6 (complete)

## Test Coverage

### Property-Based Test

**Function**: `test_property_11_html_generation_conformity`

- **Input Space**: 
  - 1-20 lines per note
  - Monetary amounts: 0 to 100 million
  - Random note titles and numbers
  - All SYSCOHADA column configurations

- **Assertions**: 7 comprehensive validation functions
- **Iterations**: 100 random test cases

### Unit Tests

Additional unit tests cover specific scenarios:

1. **`test_html_generation_with_zero_amounts`**
   - Validates zero amounts display as dash (-)
   - Edge case: all amounts are zero

2. **`test_html_generation_with_large_amounts`**
   - Validates formatting of amounts in millions
   - Example: 123,456,789 → "123 456 789"

3. **`test_html_responsive_design`**
   - Validates viewport meta tag presence
   - Validates media queries for responsive design
   - Ensures mobile compatibility

## Expected Behavior

### Valid HTML Output

The HTML_Generator must produce output with:

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NOTE 3A - Immobilisations Incorporelles</title>
    <style>
        /* CSS with borders, alternating colors, Courier font */
        .montant-cell {
            font-family: 'Courier New', monospace;
        }
        .even-row { background-color: #ffffff; }
        .odd-row { background-color: #f9f9f9; }
        .total-row { font-weight: bold; border-top: 2px solid; }
    </style>
</head>
<body>
    <table>
        <thead>
            <tr>
                <th rowspan="2">LIBELLÉ</th>
                <th colspan="4">VALEURS BRUTES</th>
                ...
            </tr>
            <tr>
                <th>Ouverture</th>
                <th>Augmentations</th>
                ...
            </tr>
        </thead>
        <tbody>
            <tr class="even-row">
                <td>Frais de recherche</td>
                <td class="montant-cell">1 500 000</td>
                ...
            </tr>
            <tr class="total-row">
                <td>TOTAL IMMOBILISATIONS</td>
                <td class="montant-cell">10 500 000</td>
                ...
            </tr>
        </tbody>
    </table>
</body>
</html>
```

### Monetary Formatting Examples

| Amount | Formatted Output |
|--------|------------------|
| 0 | - |
| 500 | 500 |
| 1000 | 1 000 |
| 1500000 | 1 500 000 |
| 123456789 | 123 456 789 |

## Running the Tests

### Run Property Test Only

```bash
pytest py_backend/Doc\ calcul\ notes\ annexes/Tests/test_html_generator_conformity.py::test_property_11_html_generation_conformity -v --hypothesis-show-statistics
```

### Run All HTML Generator Tests

```bash
pytest py_backend/Doc\ calcul\ notes\ annexes/Tests/test_html_generator_conformity.py -v
```

### Run with Coverage

```bash
pytest py_backend/Doc\ calcul\ notes\ annexes/Tests/test_html_generator_conformity.py -v --cov=py_backend/Doc\ calcul\ notes\ annexes/Modules/html_generator --cov-report=html
```

## Dependencies

- **pytest**: Test framework
- **hypothesis**: Property-based testing library
- **beautifulsoup4**: HTML parsing and validation
- **pandas**: DataFrame handling
- **lxml**: HTML parser backend for BeautifulSoup

Install dependencies:

```bash
pip install pytest hypothesis beautifulsoup4 pandas lxml
```

## Success Criteria

The property test passes when:

1. ✅ All 100 random test cases pass
2. ✅ HTML structure is valid for all generated notes
3. ✅ SYSCOHADA headers are correctly formatted
4. ✅ CSS styling includes borders and alternating colors
5. ✅ All monetary amounts formatted with thousand separators
6. ✅ Total row present with distinct styling
7. ✅ Courier New font applied to amount cells

## Failure Scenarios

The test will fail if:

- ❌ HTML is malformed or missing required tags
- ❌ Table headers don't match SYSCOHADA format
- ❌ CSS styling is missing or incomplete
- ❌ Monetary amounts have decimals or wrong separators
- ❌ Total row is missing or not styled distinctly
- ❌ Courier New font not applied to amounts

## Integration with CI/CD

This test is part of the automated test suite and runs on:

- Every commit to the repository
- Pull request validation
- Nightly builds

**Performance Target**: Test suite should complete in < 60 seconds

## Related Tests

- `test_balance_reader_property.py` - Property tests for balance loading
- `test_account_extractor_completeness.py` - Property tests for account extraction
- `test_movement_calculator_coherence.py` - Property tests for calculation coherence

## Notes

- The test uses BeautifulSoup for robust HTML parsing and validation
- Hypothesis automatically shrinks failing cases to minimal examples
- The test validates both structure and styling conformity
- Responsive design is validated through media query presence
- The test ensures cross-browser compatibility through standard HTML/CSS

## Maintenance

**Last Updated**: 2026-04-22  
**Maintainer**: Claraverse Development Team  
**Review Frequency**: After any changes to HTML_Generator module

## References

- Design Document: `.kiro/specs/calcul-notes-annexes-syscohada/design.md`
- Requirements Document: `.kiro/specs/calcul-notes-annexes-syscohada/requirements.md`
- HTML_Generator Module: `py_backend/Doc calcul notes annexes/Modules/html_generator.py`
