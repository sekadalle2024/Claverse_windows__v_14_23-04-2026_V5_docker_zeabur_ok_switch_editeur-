# Quick Start: Property Test 22 - Calculation Traceability

## 🚀 Run the Test Now

```bash
cd py_backend/Doc\ calcul\ notes\ annexes
pytest Tests/test_trace_manager_property.py -v --hypothesis-show-statistics
```

## ✅ What This Test Does

Tests that the Trace_Manager creates complete audit trails for all calculations:

1. ✅ Creates trace_note_XX.json files
2. ✅ Records all calculated amounts with source accounts
3. ✅ Records generation timestamp
4. ✅ Records source balance file name and MD5 hash
5. ✅ Enables complete audit reconstruction

## 📊 Expected Output

```
test_trace_manager_property.py::test_property_22_calculation_traceability PASSED [100 examples]
test_trace_manager_property.py::test_property_22_trace_completeness_for_audit PASSED [50 examples]
test_trace_manager_property.py::test_property_22_trace_with_empty_calculations PASSED [50 examples]
test_trace_manager_property.py::test_trace_file_naming_convention PASSED [50 examples]

======================== 4 passed in 15.23s ========================

Hypothesis Statistics:
  - 250 total examples tested
  - 0 failures
  - Typical runtime: 50-200ms per example
```

## 🎯 What Gets Validated

### Property 22: Calculation Traceability

For ANY note annexe generated, the trace must contain:

| Component | Requirement | Verified |
|-----------|-------------|----------|
| Note number | 15.1 | ✅ |
| Generation timestamp | 15.3 | ✅ |
| Source file name | 15.4 | ✅ |
| MD5 hash | 15.4 | ✅ |
| All calculations | 15.1 | ✅ |
| Source accounts | 15.2 | ✅ |
| 8 balance columns | 15.2 | ✅ |
| Audit reconstruction | 15.1, 15.2 | ✅ |

## 🔍 Example Trace Structure

```json
{
  "note": "03",
  "titre": "Immobilisations incorporelles",
  "date_generation": "2026-04-23T14:30:00",
  "fichier_balance": "P000 - BALANCE DEMO N_N-1_N-2.xlsx",
  "hash_md5_balance": "a1b2c3d4e5f6...",
  "lignes": [
    {
      "libelle": "Frais de recherche et de développement",
      "montant": 1500000.0,
      "comptes_sources": [
        {
          "numero": "211",
          "intitule": "Frais de recherche",
          "ant_debit": 1000000.0,
          "ant_credit": 0.0,
          "mvt_debit": 500000.0,
          "mvt_credit": 0.0,
          "solde_debit": 1500000.0,
          "solde_credit": 0.0
        }
      ]
    }
  ]
}
```

## 🧪 Test Scenarios

### Scenario 1: Complete Trace (100 examples)
- Random note numbers (01-33)
- Random calculations (1-10 per note)
- Random source accounts (1-5 per calculation)
- Verifies all trace components

### Scenario 2: Audit Capabilities (50 examples)
- Verifies source data identification
- Verifies calculation reproduction
- Verifies independent verification

### Scenario 3: Edge Cases (50 examples)
- Empty calculations
- File naming conventions

## 🐛 Troubleshooting

### Test Fails: "Trace file must be created"
**Problem:** Trace_Manager.sauvegarder_trace() not working

**Solution:**
```python
# Check that Trace_Manager has this method:
def sauvegarder_trace(self, fichier_sortie: str):
    with open(fichier_sortie, 'w', encoding='utf-8') as f:
        json.dump(self.trace_data, f, indent=2, ensure_ascii=False)
```

### Test Fails: "Trace must contain generation timestamp"
**Problem:** date_generation field missing

**Solution:**
```python
# In enregistrer_metadata():
self.trace_data['date_generation'] = datetime.now().isoformat()
```

### Test Fails: "All source accounts must be traced"
**Problem:** comptes_sources not recorded

**Solution:**
```python
# In enregistrer_calcul():
ligne = {
    'libelle': libelle,
    'montant': montant,
    'comptes_sources': comptes_sources  # Must include this!
}
self.trace_data['lignes'].append(ligne)
```

## 📝 Task Completion

After this test passes, mark task as complete:

```markdown
- [x] 11.2 Write property test for calculation traceability
  - **Property 22: Calculation Traceability**
  - **Validates: Requirements 15.1, 15.2, 15.3, 15.4**
```

## 🎓 Understanding the Test

### Why Property-Based Testing?

Traditional unit tests check specific examples:
```python
def test_trace_specific_example():
    trace = TraceManager("03")
    trace.enregistrer_calcul("Test", 1000.0, [...])
    # Only tests ONE scenario
```

Property-based tests check universal properties:
```python
@given(numero_note=st_numero_note(), calculs=st.lists(...))
def test_property_22_calculation_traceability(numero_note, calculs):
    # Tests 100+ random scenarios automatically!
```

### What Hypothesis Does

1. **Generates** 100+ random test cases
2. **Runs** your test on each case
3. **Shrinks** failures to minimal examples
4. **Reports** statistics on test coverage

## 🔗 Related Files

- **Test File:** `Tests/test_trace_manager_property.py`
- **Module:** `Modules/trace_manager.py`
- **Summary:** `Tests/PROPERTY_TEST_CALCULATION_TRACEABILITY_SUMMARY.md`
- **Design:** `.kiro/specs/calcul-notes-annexes-syscohada/design.md`
- **Tasks:** `.kiro/specs/calcul-notes-annexes-syscohada/tasks.md`

## ⏭️ Next Steps

1. ✅ Run this test
2. ✅ Verify all 250+ examples pass
3. ✅ Mark Task 11.2 as complete
4. ⏭️ Continue to Task 12: Checkpoint
5. ⏭️ Or optionally: Task 11.3 (Trace history management)

## 💡 Pro Tips

- Run with `-v` for verbose output
- Run with `--hypothesis-show-statistics` to see test coverage
- Run with `-s` to see print statements
- Run with `--hypothesis-seed=12345` to reproduce specific test runs

## 🎉 Success Criteria

✅ All 4 test functions pass  
✅ 250+ examples tested  
✅ 0 failures  
✅ Trace files created correctly  
✅ All metadata preserved  
✅ Audit reconstruction possible  

**When all criteria met → Task 11.2 COMPLETE! 🎊**
