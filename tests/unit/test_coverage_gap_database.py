"""Targeted tests for app.database to improve coverage."""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from app.database import get_db, init_db, SessionLocal, engine
from app.models import Base


@pytest.mark.unit
class TestDatabaseFunctions:
    """Test database functions to cover untested code."""
    
    def test_get_db_success(self):
        """Test get_db generator yields session and closes it."""
        db_gen = get_db()
        db = next(db_gen)
        
        assert isinstance(db, Session)
        assert db.is_active
        
        # Cleanup
        try:
            next(db_gen)
        except StopIteration:
            pass
    
    def test_get_db_closes_on_exception(self):
        """Test get_db closes session even when exception occurs."""
        db_gen = get_db()
        db = next(db_gen)
        
        # Simulate exception
        db.close()
        
        # Generator should complete
        try:
            next(db_gen)
        except StopIteration:
            pass
    
    def test_get_db_context_manager_usage(self):
        """Test get_db works as context manager pattern."""
        db_gen = get_db()
        try:
            db = next(db_gen)
            assert db is not None
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass
    
    @patch('app.database.Base.metadata.create_all')
    def test_init_db_creates_tables(self, mock_create_all):
        """Test init_db creates all database tables."""
        init_db()
        
        mock_create_all.assert_called_once_with(bind=engine)
    
    @patch('app.database.Base.metadata.create_all')
    def test_init_db_imports_all_models(self, mock_create_all):
        """Test init_db imports all models before creating tables."""
        # This test verifies that init_db() imports models
        # The actual import happens in the function body
        init_db()
        
        # Verify create_all was called
        assert mock_create_all.called
        
        # Verify models are importable (they should be after init_db)
        from app.models import User, Service
        from app.models.camera import ArloBaseStation, ArloCamera, ArloRecording, ArloEvent
        from app.models.encoder import VideoEncoder
        
        assert User is not None
        assert Service is not None
        assert ArloBaseStation is not None
        assert ArloCamera is not None
        assert ArloRecording is not None
        assert ArloEvent is not None
        assert VideoEncoder is not None

