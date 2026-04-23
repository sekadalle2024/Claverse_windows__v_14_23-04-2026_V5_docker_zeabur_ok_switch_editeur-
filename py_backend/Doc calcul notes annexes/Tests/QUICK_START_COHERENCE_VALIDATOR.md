# Quick Start Guide: CoherenceValidator Module

## Overview
The `CoherenceValidator` module validates consistency between calculated SYSCOHADA financial statement annexes.

## Quick Test

### Run Standalone Test
```powershell
python "py_backend/Doc calcul notes annexes/Modules/coherence_validator.py"
```

**Expected Output:**
```
=== Test du CoherenceValidator ===

1. Validation du total des immobilisations...
   Résultat: ✓ Cohérent (écart: 0.00)

2. Validation des dotations aux amortissements...
   Résultat: ✓ Cohérent (écart: 0.00)

3. Validation de la continuité temporelle...

4. Calcul du taux de cohérence global...
   Taux: 100.0%

5. Génération du rapport HTML...
   Rapport sauvegardé: rapport_coherence_test.html

=== Test terminé ===
```

### View Generated Report
Open `rapport_coherence_test.html` in your browser to see the coherence report.

## Basic Usage

```python
from coherence_validator import CoherenceValidator
import pandas as pd

# Prepare notes (example with Note 3A)
df_3a = pd.DataFrame({
    'libelle': ['Frais R&D', 'Brevets', 'TOTAL'],
    'brut_ouverture': [1000000, 500000, 1500000],
    'vnc_cloture': [860000, 450000, 1310000],
    'dotations': [100000, 50000, 150000]
})

notes = {'note_3a': df_3a}

# Create validator
validator = CoherenceValidator(notes)

# Run validations
validator.valider_total_immobilisations()
validator.valider_dotations_amortissements()
validator.valider_continuite_temporelle()

# Get coherence rate
taux = validator.calculer_taux_coherence()
print(f"Taux de cohérence: {taux:.1f}%")

# Generate HTML report
html = validator.generer_rapport_coherence()
with open('rapport.html', 'w', encoding='utf-8') as f:
    f.write(html)
```

## Key Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `valider_total_immobilisations()` | Validate total fixed assets | `(bool, float)` |
| `valider_dotations_amortissements()` | Validate depreciation charges | `(bool, float)` |
| `valider_continuite_temporelle()` | Validate temporal continuity | `Dict[str, Tuple[bool, float]]` |
| `calculer_taux_coherence()` | Calculate global rate | `float` (0-100) |
| `generer_rapport_coherence()` | Generate HTML report | `str` (HTML) |

## Coherence Thresholds

- ✅ **Coherent:** Deviation < 1%
- ⚠️ **Warning:** Deviation 1-5%
- 🔴 **Critical:** Coherence rate < 95%

## Expected Notes Structure

Each note DataFrame should have these columns (as applicable):

### Fixed Asset Notes (3A-3E)
- `libelle`: Line description
- `brut_ouverture`: Gross opening balance
- `brut_cloture`: Gross closing balance
- `amort_ouverture`: Opening depreciation
- `amort_cloture`: Closing depreciation
- `vnc_ouverture`: Opening net book value
- `vnc_cloture`: Closing net book value
- `dotations`: Depreciation charges
- `reprises`: Depreciation reversals

### Temporal Continuity Columns
- `brut_cloture_n1`: Gross closing N-1
- `solde_cloture_n1`: Balance closing N-1

## Troubleshooting

### Issue: "Note not found"
**Solution:** Ensure note names match expected format: `note_3a`, `note_3b`, etc.

### Issue: "Columns not available"
**Solution:** Verify DataFrame has required columns for the validation type.

### Issue: "Division by zero"
**Solution:** Module handles this gracefully - check if notes have zero totals.

## Next Steps

1. ✅ Module tested and working
2. ⏭️ Integrate with main orchestrator
3. ⏭️ Add property-based tests (optional)
4. ⏭️ Test with real balance data

## Files

- **Module:** `Modules/coherence_validator.py`
- **Summary:** `Tests/TASK_10_1_COHERENCE_VALIDATOR_SUMMARY.md`
- **This Guide:** `Tests/QUICK_START_COHERENCE_VALIDATOR.md`

---

**Status:** ✅ Ready for use  
**Last Updated:** April 23, 2026
