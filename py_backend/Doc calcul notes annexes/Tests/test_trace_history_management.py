"""
Property-Based Tests for Trace History Management

Feature: calcul-notes-annexes-syscohada
Property 23: Trace History Management

For any note annexe generated multiple times, the system must maintain 
the 10 most recent trace files, automatically deleting older traces.

Validates: Requirements 15.7
"""

import pytest
from hypothesis import given, settings, strategies as st, assume
import os
import time
from pathlib import Path
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from Modules.trace_manager import TraceManager


# ============================================================================
# Hypothesis Strategies
# ============================================================================

@st.composite
def st_numero_note(draw):
    """Generate valid note numbers (01-33)"""
    numero = draw(st.integers(min_value=1, max_value=33))
    return f"{numero:02d}"


@st.composite
def st_num_traces(draw):
    """Generate number of traces to create (more than max_historique to test deletion)"""
    return draw(st.integers(min_value=5, max_value=25))


@st.composite
def st_max_historique(draw):
    """Generate max_historique value (1-15)"""
    return draw(st.integers(min_value=1, max_value=15))


# ============================================================================
# Property 23: Trace History Management
# ============================================================================

@given(
    numero_note=st_numero_note(),
    num_traces=st_num_traces(),
    max_historique=st_max_historique()
)
@settings(max_examples=100, deadline=None)
def test_property_23_trace_history_management(numero_note, num_traces, max_historique):
    """
    Property 23: Trace History Management
    
    For any note annexe generated multiple times, the system must maintain 
    the max_historique most recent trace files, automatically deleting older traces.
    
    Validates: Requirements 15.7
    """
    # Arrange
    trace_manager = TraceManager(numero_note)
    traces_dir = trace_manager.traces_dir
    
    # Ensure traces directory exists
    traces_dir.mkdir(parents=True, exist_ok=True)
    
    # Create multiple trace files with different timestamps
    created_files = []
    
    try:
        for i in range(num_traces):
            # Create trace with unique timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{i:03d}"
            trace_file = f"trace_note_{numero_note}_{timestamp}.json"
            
            # Record some metadata
            trace_manager.enregistrer_metadata(
                fichier_balance=f"balance_test_{i}.xlsx",
                hash_md5=f"hash_{i}",
                titre_note=f"Test Note {numero_note}"
            )
            
            # Save trace
            saved_path = trace_manager.sauvegarder_trace(trace_file)
            created_files.append(Path(saved_path))
            
            # Small delay to ensure different modification times
            time.sleep(0.01)
        
        # Verify all files were created
        assert len(created_files) == num_traces, "All trace files must be created"
        for file_path in created_files:
            assert file_path.exists(), f"Trace file {file_path} must exist"
        
        # Act - Manage history
        trace_manager.gerer_historique(max_historique=max_historique)
        
        # Assert - Property 1: Only max_historique files should remain
        pattern = f"trace_note_{numero_note}_*.json"
        remaining_files = list(traces_dir.glob(pattern))
        
        expected_count = min(num_traces, max_historique)
        assert len(remaining_files) == expected_count, \
            f"Must keep exactly {expected_count} most recent traces (found {len(remaining_files)})"
        
        # Assert - Property 2: The most recent files should be kept
        if num_traces > max_historique:
            # Get the most recent files by modification time
            all_files_sorted = sorted(
                created_files,
                key=lambda p: p.stat().st_mtime if p.exists() else 0,
                reverse=True
            )
            
            expected_kept_files = set(all_files_sorted[:max_historique])
            actual_kept_files = set(remaining_files)
            
            # Verify the kept files are the most recent ones
            for kept_file in actual_kept_files:
                assert kept_file in expected_kept_files, \
                    f"File {kept_file.name} should be among the {max_historique} most recent"
        
        # Assert - Property 3: Older files should be deleted
        if num_traces > max_historique:
            num_deleted = num_traces - max_historique
            deleted_count = sum(1 for f in created_files if not f.exists())
            assert deleted_count == num_deleted, \
                f"Must delete exactly {num_deleted} oldest traces (deleted {deleted_count})"
        
        # Assert - Property 4: Remaining files must be valid JSON traces
        for remaining_file in remaining_files:
            assert remaining_file.exists(), "Remaining file must exist"
            assert remaining_file.suffix == '.json', "Remaining file must be JSON"
            assert remaining_file.name.startswith(f"trace_note_{numero_note}_"), \
                "Remaining file must follow naming convention"
        
    finally:
        # Cleanup - Remove all test trace files
        pattern = f"trace_note_{numero_note}_*.json"
        for trace_file in traces_dir.glob(pattern):
            try:
                trace_file.unlink()
            except Exception:
                pass


@given(
    numero_note=st_numero_note(),
    max_historique=st_max_historique()
)
@settings(max_examples=50, deadline=None)
def test_property_23_history_with_fewer_traces_than_max(numero_note, max_historique):
    """
    Property 23 Edge Case: History Management with Fewer Traces than Max
    
    When the number of existing traces is less than max_historique,
    no files should be deleted.
    
    Validates: Requirements 15.7
    """
    # Arrange
    trace_manager = TraceManager(numero_note)
    traces_dir = trace_manager.traces_dir
    traces_dir.mkdir(parents=True, exist_ok=True)
    
    # Create fewer traces than max_historique
    num_traces = max(1, max_historique - 2)
    created_files = []
    
    try:
        for i in range(num_traces):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{i:03d}"
            trace_file = f"trace_note_{numero_note}_{timestamp}.json"
            
            trace_manager.enregistrer_metadata(
                fichier_balance=f"balance_{i}.xlsx",
                hash_md5=f"hash_{i}"
            )
            
            saved_path = trace_manager.sauvegarder_trace(trace_file)
            created_files.append(Path(saved_path))
            time.sleep(0.01)
        
        # Act
        trace_manager.gerer_historique(max_historique=max_historique)
        
        # Assert - All files should still exist (no deletion)
        pattern = f"trace_note_{numero_note}_*.json"
        remaining_files = list(traces_dir.glob(pattern))
        
        assert len(remaining_files) == num_traces, \
            f"All {num_traces} traces should be kept when less than max_historique ({max_historique})"
        
        for file_path in created_files:
            assert file_path.exists(), f"File {file_path.name} should not be deleted"
    
    finally:
        # Cleanup
        pattern = f"trace_note_{numero_note}_*.json"
        for trace_file in traces_dir.glob(pattern):
            try:
                trace_file.unlink()
            except Exception:
                pass


@given(
    numero_note=st_numero_note(),
    num_traces=st.integers(min_value=15, max_value=30)
)
@settings(max_examples=50, deadline=None)
def test_property_23_default_max_historique_is_10(numero_note, num_traces):
    """
    Property 23 Default Behavior: Default max_historique is 10
    
    When gerer_historique() is called without arguments, it should
    default to keeping 10 most recent traces.
    
    Validates: Requirements 15.7
    """
    # Arrange
    trace_manager = TraceManager(numero_note)
    traces_dir = trace_manager.traces_dir
    traces_dir.mkdir(parents=True, exist_ok=True)
    
    created_files = []
    
    try:
        # Create more than 10 traces
        for i in range(num_traces):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{i:03d}"
            trace_file = f"trace_note_{numero_note}_{timestamp}.json"
            
            trace_manager.enregistrer_metadata(
                fichier_balance=f"balance_{i}.xlsx",
                hash_md5=f"hash_{i}"
            )
            
            saved_path = trace_manager.sauvegarder_trace(trace_file)
            created_files.append(Path(saved_path))
            time.sleep(0.01)
        
        # Act - Call without max_historique argument (should default to 10)
        trace_manager.gerer_historique()
        
        # Assert - Should keep exactly 10 most recent traces
        pattern = f"trace_note_{numero_note}_*.json"
        remaining_files = list(traces_dir.glob(pattern))
        
        expected_count = min(num_traces, 10)
        assert len(remaining_files) == expected_count, \
            f"Default max_historique should be 10 (found {len(remaining_files)} traces)"
    
    finally:
        # Cleanup
        pattern = f"trace_note_{numero_note}_*.json"
        for trace_file in traces_dir.glob(pattern):
            try:
                trace_file.unlink()
            except Exception:
                pass


@given(
    numero_note=st_numero_note(),
    num_traces=st.integers(min_value=5, max_value=20),
    max_historique=st_max_historique()
)
@settings(max_examples=50, deadline=None)
def test_property_23_history_preserves_most_recent_by_mtime(numero_note, num_traces, max_historique):
    """
    Property 23 Ordering: History Management Uses Modification Time
    
    The system must use file modification time (mtime) to determine
    which traces are most recent, not file name or creation time.
    
    Validates: Requirements 15.7
    """
    # Arrange
    trace_manager = TraceManager(numero_note)
    traces_dir = trace_manager.traces_dir
    traces_dir.mkdir(parents=True, exist_ok=True)
    
    created_files = []
    
    try:
        # Create traces with deliberate timestamp ordering
        for i in range(num_traces):
            # Use reverse order in filename to test that mtime is used, not filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{num_traces - i:03d}"
            trace_file = f"trace_note_{numero_note}_{timestamp}.json"
            
            trace_manager.enregistrer_metadata(
                fichier_balance=f"balance_{i}.xlsx",
                hash_md5=f"hash_{i}"
            )
            
            saved_path = trace_manager.sauvegarder_trace(trace_file)
            created_files.append(Path(saved_path))
            
            # Ensure different modification times
            time.sleep(0.02)
        
        # Record the modification times before cleanup
        files_with_mtime = [
            (f, f.stat().st_mtime) for f in created_files if f.exists()
        ]
        files_with_mtime.sort(key=lambda x: x[1], reverse=True)
        
        # Act
        trace_manager.gerer_historique(max_historique=max_historique)
        
        # Assert - The files with the most recent mtime should be kept
        pattern = f"trace_note_{numero_note}_*.json"
        remaining_files = set(traces_dir.glob(pattern))
        
        expected_count = min(num_traces, max_historique)
        expected_kept = set(f[0] for f in files_with_mtime[:expected_count])
        
        assert len(remaining_files) == expected_count
        
        # Verify the kept files are the ones with most recent mtime
        for kept_file in remaining_files:
            assert kept_file in expected_kept, \
                f"File {kept_file.name} should be among the {expected_count} most recent by mtime"
    
    finally:
        # Cleanup
        pattern = f"trace_note_{numero_note}_*.json"
        for trace_file in traces_dir.glob(pattern):
            try:
                trace_file.unlink()
            except Exception:
                pass


@given(numero_note=st_numero_note())
@settings(max_examples=30, deadline=None)
def test_property_23_history_with_no_existing_traces(numero_note):
    """
    Property 23 Edge Case: History Management with No Existing Traces
    
    When gerer_historique() is called with no existing trace files,
    it should complete successfully without errors.
    
    Validates: Requirements 15.7
    """
    # Arrange
    trace_manager = TraceManager(numero_note)
    traces_dir = trace_manager.traces_dir
    traces_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure no trace files exist for this note
    pattern = f"trace_note_{numero_note}_*.json"
    for trace_file in traces_dir.glob(pattern):
        trace_file.unlink()
    
    # Act - Should not raise any exception
    try:
        trace_manager.gerer_historique(max_historique=10)
        
        # Assert - No files should exist
        remaining_files = list(traces_dir.glob(pattern))
        assert len(remaining_files) == 0, "No traces should exist"
        
    except Exception as e:
        pytest.fail(f"gerer_historique() should not raise exception with no traces: {e}")


@given(
    numero_note=st_numero_note(),
    num_traces=st.integers(min_value=12, max_value=25)
)
@settings(max_examples=50, deadline=None)
def test_property_23_multiple_history_calls_are_idempotent(numero_note, num_traces):
    """
    Property 23 Idempotency: Multiple History Management Calls
    
    Calling gerer_historique() multiple times with the same max_historique
    should be idempotent - the second call should not delete any additional files.
    
    Validates: Requirements 15.7
    """
    # Arrange
    trace_manager = TraceManager(numero_note)
    traces_dir = trace_manager.traces_dir
    traces_dir.mkdir(parents=True, exist_ok=True)
    
    max_historique = 10
    created_files = []
    
    try:
        # Create traces
        for i in range(num_traces):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{i:03d}"
            trace_file = f"trace_note_{numero_note}_{timestamp}.json"
            
            trace_manager.enregistrer_metadata(
                fichier_balance=f"balance_{i}.xlsx",
                hash_md5=f"hash_{i}"
            )
            
            saved_path = trace_manager.sauvegarder_trace(trace_file)
            created_files.append(Path(saved_path))
            time.sleep(0.01)
        
        # Act - First call
        trace_manager.gerer_historique(max_historique=max_historique)
        
        pattern = f"trace_note_{numero_note}_*.json"
        files_after_first_call = set(traces_dir.glob(pattern))
        count_after_first = len(files_after_first_call)
        
        # Act - Second call (should be idempotent)
        trace_manager.gerer_historique(max_historique=max_historique)
        
        files_after_second_call = set(traces_dir.glob(pattern))
        count_after_second = len(files_after_second_call)
        
        # Assert - Same number of files after both calls
        assert count_after_first == count_after_second, \
            "Second gerer_historique() call should not delete additional files"
        
        # Assert - Same files after both calls
        assert files_after_first_call == files_after_second_call, \
            "Second gerer_historique() call should keep the same files"
        
        # Assert - Correct number of files kept
        expected_count = min(num_traces, max_historique)
        assert count_after_second == expected_count, \
            f"Should keep exactly {expected_count} traces"
    
    finally:
        # Cleanup
        pattern = f"trace_note_{numero_note}_*.json"
        for trace_file in traces_dir.glob(pattern):
            try:
                trace_file.unlink()
            except Exception:
                pass


@given(
    numero_note=st_numero_note(),
    num_traces=st.integers(min_value=15, max_value=25),
    max_historique_1=st.integers(min_value=5, max_value=10),
    max_historique_2=st.integers(min_value=3, max_value=7)
)
@settings(max_examples=50, deadline=None)
def test_property_23_decreasing_max_historique_deletes_more_files(
    numero_note, num_traces, max_historique_1, max_historique_2
):
    """
    Property 23 Dynamic Limit: Decreasing max_historique
    
    When max_historique is decreased in subsequent calls, more files
    should be deleted to meet the new limit.
    
    Validates: Requirements 15.7
    """
    # Ensure max_historique_2 < max_historique_1
    assume(max_historique_2 < max_historique_1)
    
    # Arrange
    trace_manager = TraceManager(numero_note)
    traces_dir = trace_manager.traces_dir
    traces_dir.mkdir(parents=True, exist_ok=True)
    
    created_files = []
    
    try:
        # Create traces
        for i in range(num_traces):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{i:03d}"
            trace_file = f"trace_note_{numero_note}_{timestamp}.json"
            
            trace_manager.enregistrer_metadata(
                fichier_balance=f"balance_{i}.xlsx",
                hash_md5=f"hash_{i}"
            )
            
            saved_path = trace_manager.sauvegarder_trace(trace_file)
            created_files.append(Path(saved_path))
            time.sleep(0.01)
        
        # Act - First call with higher limit
        trace_manager.gerer_historique(max_historique=max_historique_1)
        
        pattern = f"trace_note_{numero_note}_*.json"
        count_after_first = len(list(traces_dir.glob(pattern)))
        expected_after_first = min(num_traces, max_historique_1)
        
        assert count_after_first == expected_after_first
        
        # Act - Second call with lower limit
        trace_manager.gerer_historique(max_historique=max_historique_2)
        
        count_after_second = len(list(traces_dir.glob(pattern)))
        expected_after_second = min(count_after_first, max_historique_2)
        
        # Assert - Fewer files should remain
        assert count_after_second == expected_after_second, \
            f"Should keep only {expected_after_second} traces after decreasing limit"
        
        assert count_after_second <= count_after_first, \
            "Decreasing max_historique should not increase file count"
    
    finally:
        # Cleanup
        pattern = f"trace_note_{numero_note}_*.json"
        for trace_file in traces_dir.glob(pattern):
            try:
                trace_file.unlink()
            except Exception:
                pass


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
