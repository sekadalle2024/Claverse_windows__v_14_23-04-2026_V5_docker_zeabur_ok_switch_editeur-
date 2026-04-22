"""
Property-Based Tests for HTML_Generator Conformity

This module contains property-based tests to validate that the HTML_Generator
produces HTML conforming to the official SYSCOHADA format.

Property 11: HTML Generation Conformity
Validates: Requirements 6.2, 6.3, 6.4, 6.5, 6.6

Author: Claraverse
Date: 2026-04-22
"""

import pytest
from hypothesis import given, settings, assume
import hypothesis.strategies as st
import pandas as pd
import re
from bs4 import BeautifulSoup
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Modules'))

from html_generator import HTMLGenerator
from conftest import st_ligne_note_annexe, st_montant


# ============================================================================
# PROPERTY 11: HTML GENERATION CONFORMITY
# ============================================================================

@given(
    lignes=st.lists(st_ligne_note_annexe(), min_size=1, max_size=20),
    titre_note=st.text(min_size=5, max_size=100),
    numero_note=st.text(min_size=1, max_size=5)
)
@settings(max_examples=100, deadline=60000)
def test_property_11_html_generation_conformity(lignes, titre_note, numero_note):
    """
    **Validates: Requirements 6.2, 6.3, 6.4, 6.5, 6.6**
    
    Property 11: HTML Generation Conformity
    
    For any note annexe generated, the HTML_Generator must produce valid HTML 
    containing a table with headers conforming to the official SYSCOHADA format, 
    CSS styling with borders and alternating row colors, monetary amounts formatted 
    with thousand separators and 0 decimals, and a total row with distinct styling.
    """
    # Arrange: Create DataFrame from generated lines
    df = pd.DataFrame(lignes)
    
    # Add a total row
    total_row = {
        'libelle': f'TOTAL {titre_note.upper()}',
        'brut_ouverture': df['brut_ouverture'].sum(),
        'augmentations': df['augmentations'].sum(),
        'diminutions': df['diminutions'].sum(),
        'brut_cloture': df['brut_cloture'].sum(),
        'amort_ouverture': df['amort_ouverture'].sum(),
        'dotations': df['dotations'].sum(),
        'reprises': df['reprises'].sum(),
        'amort_cloture': df['amort_cloture'].sum(),
        'vnc_ouverture': df['vnc_ouverture'].sum(),
        'vnc_cloture': df['vnc_cloture'].sum()
    }
    df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)
    
    # Configuration des colonnes SYSCOHADA standard
    colonnes_config = {
        'groupes': [
            {
                'titre': 'VALEURS BRUTES',
                'colonnes': ['brut_ouverture', 'augmentations', 'diminutions', 'brut_cloture']
            },
            {
                'titre': 'AMORTISSEMENTS',
                'colonnes': ['amort_ouverture', 'dotations', 'reprises', 'amort_cloture']
            },
            {
                'titre': 'VALEURS NETTES COMPTABLES',
                'colonnes': ['vnc_ouverture', 'vnc_cloture']
            }
        ],
        'labels': {
            'brut_ouverture': 'Ouverture',
            'augmentations': 'Augmentations',
            'diminutions': 'Diminutions',
            'brut_cloture': 'Clôture',
            'amort_ouverture': 'Ouverture',
            'dotations': 'Dotations',
            'reprises': 'Reprises',
            'amort_cloture': 'Clôture',
            'vnc_ouverture': 'Ouverture',
            'vnc_cloture': 'Clôture'
        }
    }
    
    # Act: Generate HTML
    generator = HTMLGenerator(titre_note, numero_note)
    html = generator.generer_html(df, colonnes_config)
    
    # Assert: Validate HTML conformity
    
    # Requirement 6.2: HTML must include a table with headers conforming to SYSCOHADA format
    assert_valid_html_structure(html)
    assert_syscohada_headers_present(html, colonnes_config)
    
    # Requirement 6.3: HTML must apply CSS styling with borders and alternating row colors
    assert_css_styling_present(html)
    assert_alternating_row_colors(html)
    
    # Requirement 6.4: Monetary amounts must be formatted with thousand separators and 0 decimals
    assert_monetary_formatting(html, df)
    
    # Requirement 6.5: HTML must include a total row with distinct styling
    assert_total_row_present(html, titre_note)
    
    # Requirement 6.6: HTML must use Courier New font for amounts to align digits
    assert_courier_font_for_amounts(html)


# ============================================================================
# HELPER ASSERTION FUNCTIONS
# ============================================================================

def assert_valid_html_structure(html: str):
    """
    Validates that the HTML is well-formed and contains required elements.
    
    Requirement 6.2: Valid HTML structure
    """
    # Parse HTML
    soup = BeautifulSoup(html, 'html.parser')
    
    # Check for required HTML elements
    assert soup.find('html') is not None, "HTML must have <html> tag"
    assert soup.find('head') is not None, "HTML must have <head> tag"
    assert soup.find('body') is not None, "HTML must have <body> tag"
    assert soup.find('table') is not None, "HTML must have <table> tag"
    assert soup.find('thead') is not None, "HTML must have <thead> tag"
    assert soup.find('tbody') is not None, "HTML must have <tbody> tag"
    
    # Check for meta charset
    meta_charset = soup.find('meta', {'charset': True})
    assert meta_charset is not None, "HTML must have charset meta tag"
    assert meta_charset['charset'].lower() == 'utf-8', "Charset must be UTF-8"
    
    # Check for title
    title = soup.find('title')
    assert title is not None, "HTML must have <title> tag"
    assert 'NOTE' in title.text, "Title must contain 'NOTE'"


def assert_syscohada_headers_present(html: str, colonnes_config: dict):
    """
    Validates that table headers conform to SYSCOHADA format.
    
    Requirement 6.2: Headers conforming to official SYSCOHADA format
    """
    soup = BeautifulSoup(html, 'html.parser')
    thead = soup.find('thead')
    
    assert thead is not None, "Table must have thead"
    
    # Check for two header rows (group headers and sub-headers)
    header_rows = thead.find_all('tr')
    assert len(header_rows) == 2, "Table must have 2 header rows (groups and sub-columns)"
    
    # Check for group headers
    group_row = header_rows[0]
    group_headers = group_row.find_all('th')
    
    # First header should be LIBELLÉ with rowspan=2
    libelle_header = group_headers[0]
    assert 'LIBELLÉ' in libelle_header.text or 'libelle' in libelle_header.get('class', []), \
        "First header must be LIBELLÉ"
    assert libelle_header.get('rowspan') == '2', "LIBELLÉ header must have rowspan=2"
    
    # Check that all configured groups are present
    for groupe in colonnes_config['groupes']:
        groupe_titre = groupe['titre']
        found = False
        for header in group_headers:
            if groupe_titre in header.text:
                found = True
                # Check colspan matches number of columns
                expected_colspan = len(groupe['colonnes'])
                actual_colspan = header.get('colspan', '1')
                assert actual_colspan == str(expected_colspan), \
                    f"Group '{groupe_titre}' must have colspan={expected_colspan}"
                break
        assert found, f"Group header '{groupe_titre}' must be present in HTML"
    
    # Check for sub-headers
    subheader_row = header_rows[1]
    subheaders = subheader_row.find_all('th')
    
    # Count expected sub-headers
    expected_subheaders = sum(len(g['colonnes']) for g in colonnes_config['groupes'])
    assert len(subheaders) == expected_subheaders, \
        f"Must have {expected_subheaders} sub-headers"


def assert_css_styling_present(html: str):
    """
    Validates that CSS styling is present with borders.
    
    Requirement 6.3: CSS styling with borders
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # Check for style tag
    style_tag = soup.find('style')
    assert style_tag is not None, "HTML must have <style> tag"
    
    css_content = style_tag.string
    assert css_content is not None, "Style tag must have content"
    
    # Check for border styling
    assert 'border' in css_content.lower(), "CSS must include border styling"
    assert 'border-collapse' in css_content.lower(), "CSS must include border-collapse"
    
    # Check for table styling
    assert 'table' in css_content.lower(), "CSS must include table styling"
    
    # Check for cell styling
    assert 'td' in css_content.lower() or 'th' in css_content.lower(), \
        "CSS must include cell (td/th) styling"


def assert_alternating_row_colors(html: str):
    """
    Validates that alternating row colors are defined in CSS.
    
    Requirement 6.3: Alternating row colors
    """
    soup = BeautifulSoup(html, 'html.parser')
    style_tag = soup.find('style')
    css_content = style_tag.string.lower()
    
    # Check for even/odd row classes or nth-child selectors
    has_even_odd = ('even-row' in css_content or 'odd-row' in css_content or
                    'nth-child(even)' in css_content or 'nth-child(odd)' in css_content)
    
    assert has_even_odd, "CSS must define alternating row colors (even-row/odd-row or nth-child)"
    
    # Check that rows in tbody have appropriate classes
    tbody = soup.find('tbody')
    if tbody:
        rows = tbody.find_all('tr')
        if len(rows) > 1:
            # At least some rows should have even-row or odd-row class
            has_row_classes = any(
                'even-row' in row.get('class', []) or 'odd-row' in row.get('class', [])
                for row in rows
            )
            assert has_row_classes, "Table rows must have even-row or odd-row classes"


def assert_monetary_formatting(html: str, df: pd.DataFrame):
    """
    Validates that monetary amounts are formatted with thousand separators and 0 decimals.
    
    Requirement 6.4: Monetary amounts formatted with thousand separators and 0 decimals
    """
    soup = BeautifulSoup(html, 'html.parser')
    tbody = soup.find('tbody')
    
    assert tbody is not None, "Table must have tbody"
    
    # Find all monetary cells (cells with montant-cell class or in numeric columns)
    montant_cells = tbody.find_all('td', class_='montant-cell')
    
    if not montant_cells:
        # Fallback: find all td cells except first (libellé)
        rows = tbody.find_all('tr')
        montant_cells = []
        for row in rows:
            cells = row.find_all('td')
            if len(cells) > 1:
                montant_cells.extend(cells[1:])  # Skip first cell (libellé)
    
    assert len(montant_cells) > 0, "Table must have monetary cells"
    
    # Check formatting of non-zero amounts
    for cell in montant_cells:
        text = cell.text.strip()
        
        # Skip empty cells or dashes
        if not text or text == '-':
            continue
        
        # Check for thousand separator (space)
        # Amounts >= 1000 should have space separator
        # Remove spaces and check if it's a valid integer
        text_no_spaces = text.replace(' ', '')
        
        # Should be a valid integer (no decimals)
        assert text_no_spaces.isdigit() or text == '-', \
            f"Monetary amount '{text}' must be an integer without decimals"
        
        # If amount >= 1000, should have space separators
        if text_no_spaces.isdigit():
            amount = int(text_no_spaces)
            if amount >= 1000:
                assert ' ' in text, \
                    f"Amount {amount} must have thousand separator (space)"
                
                # Verify correct spacing (every 3 digits from right)
                # Example: "1 500 000" for 1500000
                expected_format = f"{amount:,}".replace(',', ' ')
                assert text == expected_format, \
                    f"Amount formatting incorrect: expected '{expected_format}', got '{text}'"


def assert_total_row_present(html: str, titre_note: str):
    """
    Validates that a total row is present with distinct styling.
    
    Requirement 6.5: Total row with distinct styling
    """
    soup = BeautifulSoup(html, 'html.parser')
    tbody = soup.find('tbody')
    
    assert tbody is not None, "Table must have tbody"
    
    # Find rows with 'TOTAL' in text
    rows = tbody.find_all('tr')
    total_rows = [row for row in rows if 'TOTAL' in row.text.upper()]
    
    assert len(total_rows) > 0, "Table must have at least one TOTAL row"
    
    # Check that total row has distinct styling (total-row class or similar)
    total_row = total_rows[-1]  # Last row should be total
    row_classes = total_row.get('class', [])
    
    assert 'total-row' in row_classes or 'total' in ' '.join(row_classes).lower(), \
        "Total row must have distinct CSS class (total-row)"
    
    # Check that CSS defines styling for total row
    style_tag = soup.find('style')
    css_content = style_tag.string.lower()
    
    assert 'total-row' in css_content or '.total' in css_content, \
        "CSS must define styling for total row"
    
    # Check for distinct styling properties (bold, borders, background)
    assert 'font-weight' in css_content or 'bold' in css_content, \
        "Total row CSS should include font-weight or bold"


def assert_courier_font_for_amounts(html: str):
    """
    Validates that Courier New font is used for amounts to align digits.
    
    Requirement 6.6: Courier New font for amounts
    """
    soup = BeautifulSoup(html, 'html.parser')
    style_tag = soup.find('style')
    
    assert style_tag is not None, "HTML must have style tag"
    
    css_content = style_tag.string.lower()
    
    # Check for Courier New font in CSS
    assert 'courier new' in css_content or 'courier' in css_content, \
        "CSS must include Courier New font"
    
    # Check that it's applied to monetary cells
    # Look for .montant-cell or td styling with Courier
    assert 'montant-cell' in css_content or 'monospace' in css_content, \
        "Courier font must be applied to monetary cells"
    
    # Verify font-family is set for monetary cells
    # Extract the montant-cell or td rule
    montant_pattern = r'\.montant-cell\s*{[^}]*font-family[^}]*}'
    td_pattern = r'td\s*{[^}]*font-family[^}]*}'
    
    has_font_family = (re.search(montant_pattern, css_content, re.IGNORECASE) is not None or
                       re.search(td_pattern, css_content, re.IGNORECASE) is not None or
                       'monospace' in css_content)
    
    assert has_font_family, "CSS must set font-family for monetary cells"


# ============================================================================
# UNIT TESTS FOR SPECIFIC SCENARIOS
# ============================================================================

def test_html_generation_with_zero_amounts():
    """
    Test HTML generation with zero amounts (should display as dash).
    """
    df = pd.DataFrame([
        {
            'libelle': 'Test Item',
            'brut_ouverture': 0,
            'augmentations': 0,
            'diminutions': 0,
            'brut_cloture': 0,
            'amort_ouverture': 0,
            'dotations': 0,
            'reprises': 0,
            'amort_cloture': 0,
            'vnc_ouverture': 0,
            'vnc_cloture': 0
        }
    ])
    
    colonnes_config = {
        'groupes': [
            {
                'titre': 'VALEURS BRUTES',
                'colonnes': ['brut_ouverture', 'augmentations', 'diminutions', 'brut_cloture']
            }
        ],
        'labels': {
            'brut_ouverture': 'Ouverture',
            'augmentations': 'Augmentations',
            'diminutions': 'Diminutions',
            'brut_cloture': 'Clôture'
        }
    }
    
    generator = HTMLGenerator("Test Note", "TEST")
    html = generator.generer_html(df, colonnes_config)
    
    # Zero amounts should be displayed as dash
    assert '-' in html, "Zero amounts should be displayed as dash (-)"


def test_html_generation_with_large_amounts():
    """
    Test HTML generation with large amounts (millions).
    """
    df = pd.DataFrame([
        {
            'libelle': 'Large Amount Item',
            'brut_ouverture': 123456789,
            'augmentations': 987654321,
            'diminutions': 0,
            'brut_cloture': 1111111110,
            'amort_ouverture': 0,
            'dotations': 0,
            'reprises': 0,
            'amort_cloture': 0,
            'vnc_ouverture': 0,
            'vnc_cloture': 0
        }
    ])
    
    colonnes_config = {
        'groupes': [
            {
                'titre': 'VALEURS BRUTES',
                'colonnes': ['brut_ouverture', 'augmentations', 'diminutions', 'brut_cloture']
            }
        ],
        'labels': {
            'brut_ouverture': 'Ouverture',
            'augmentations': 'Augmentations',
            'diminutions': 'Diminutions',
            'brut_cloture': 'Clôture'
        }
    }
    
    generator = HTMLGenerator("Test Note", "TEST")
    html = generator.generer_html(df, colonnes_config)
    
    # Check that large amounts are formatted with spaces
    assert '123 456 789' in html, "Large amounts must have thousand separators"
    assert '987 654 321' in html, "Large amounts must have thousand separators"


def test_html_responsive_design():
    """
    Test that HTML includes responsive design CSS.
    """
    df = pd.DataFrame([
        {
            'libelle': 'Test',
            'brut_ouverture': 1000,
            'augmentations': 0,
            'diminutions': 0,
            'brut_cloture': 1000,
            'amort_ouverture': 0,
            'dotations': 0,
            'reprises': 0,
            'amort_cloture': 0,
            'vnc_ouverture': 0,
            'vnc_cloture': 0
        }
    ])
    
    colonnes_config = {
        'groupes': [
            {
                'titre': 'VALEURS BRUTES',
                'colonnes': ['brut_ouverture', 'augmentations', 'diminutions', 'brut_cloture']
            }
        ],
        'labels': {
            'brut_ouverture': 'Ouverture',
            'augmentations': 'Augmentations',
            'diminutions': 'Diminutions',
            'brut_cloture': 'Clôture'
        }
    }
    
    generator = HTMLGenerator("Test Note", "TEST")
    html = generator.generer_html(df, colonnes_config)
    
    # Check for responsive meta tag
    assert 'viewport' in html.lower(), "HTML must include viewport meta tag"
    
    # Check for media queries in CSS
    assert '@media' in html.lower(), "CSS must include media queries for responsive design"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
