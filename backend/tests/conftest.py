"""
Pytest configuration and fixtures
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.services.preprocessor import PreprocessorService
from src.services.textrank_service import TextRankService


@pytest.fixture
def client():
    """Test client for API"""
    return TestClient(app)


@pytest.fixture
def sample_text():
    """Sample customer support text"""
    return """
    Subject: Login issues after password reset
    
    Customer reported inability to access account after completing password reset process. 
    User followed the reset link from email but receives "Invalid session" error on login page.
    
    Steps to reproduce:
    1. Click forgot password
    2. Receive reset email
    3. Click reset link
    4. Set new password
    5. Attempt to login
    
    Expected result: Successful login with new credentials
    Actual result: Invalid session error displayed
    
    Resolution: Cleared browser cache and cookies. Session tokens were stale. 
    User successfully logged in after cache clear. 
    Recommended enabling "Remember me" option to prevent future issues.
    """

@pytest.fixture
def preprocessor():
    """Preprocessor service instance"""
    return PreprocessorService()


@pytest.fixture
def textrank():
    """TextRank service instance"""
    return TextRankService()


