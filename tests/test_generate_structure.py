#!/usr/bin/env python3
"""
Unit tests for the dynamic structure generator script.
"""

import json
import pytest
import tempfile
from pathlib import Path
import sys
import os

# Add the scripts directory to the Python path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from generate_structure import (
    StructureGenerator,
    GeneratorConfig,
    SecurityValidator,
    DirectoryScanner,
    TreeGenerator,
    MermaidGenerator,
    FileDescriptor,
    APIDiscovery
)


class TestSecurityValidator:
    """Test security validation functionality."""
    
    def test_validate_path_within_base(self):
        """Test that valid paths within base directory are accepted."""
        validator = SecurityValidator()
        base_path = Path("/tmp/test")
        valid_path = Path("/tmp/test/subdir/file.py")
        
        # Mock the path resolution for testing
        assert validator.validate_path(Path("test"), Path("."))
    
    def test_sanitize_markdown(self):
        """Test markdown sanitization."""
        validator = SecurityValidator()
        
        # Test basic markdown characters
        text = "This has *bold* and _italic_ and `code`"
        sanitized = validator.sanitize_markdown(text)
        assert "\\*" in sanitized
        assert "\\_" in sanitized
        assert "\\`" in sanitized
        
        # Test that normal text is preserved
        normal_text = "This is normal text with spaces and numbers 123"
        assert validator.sanitize_markdown(normal_text) == normal_text


class TestGeneratorConfig:
    """Test configuration handling."""
    
    def test_default_config_creation(self):
        """Test that default configuration is created properly."""
        generator = StructureGenerator(Path("."))
        config = generator.config
        
        assert isinstance(config, GeneratorConfig)
        assert config.enable_api_discovery is True
        assert config.enable_mermaid is True
        assert config.enable_tree is True
        assert config.enable_descriptions is True
        assert len(config.exclude_patterns) > 0
        assert config.max_file_size > 0


class TestDirectoryScanner:
    """Test directory scanning functionality."""
    
    def test_should_exclude_patterns(self):
        """Test exclusion pattern matching."""
        config = GeneratorConfig(
            exclude_patterns=[r'\.git.*', r'__pycache__.*'],
            include_extensions=['.py'],
            max_file_size=1024*1024,
            enable_api_discovery=True,
            enable_mermaid=True,
            enable_tree=True,
            enable_descriptions=True
        )
        
        scanner = DirectoryScanner(Path("."), config)
        
        # Test that git files are excluded
        assert scanner.should_exclude(Path(".git/config"))
        assert scanner.should_exclude(Path("subdir/.git/HEAD"))
        
        # Test that pycache files are excluded
        assert scanner.should_exclude(Path("__pycache__/module.pyc"))
        
        # Test that normal files are not excluded
        assert not scanner.should_exclude(Path("normal_file.py"))


class TestTreeGenerator:
    """Test ASCII tree generation."""
    
    def test_tree_generation(self):
        """Test basic tree generation."""
        base_path = Path("/tmp/test")
        generator = TreeGenerator(base_path)
        
        # Create sample paths
        paths = [
            Path("/tmp/test/file1.py"),
            Path("/tmp/test/dir1"),
            Path("/tmp/test/dir1/file2.py"),
            Path("/tmp/test/dir2"),
            Path("/tmp/test/dir2/subdir"),
            Path("/tmp/test/dir2/subdir/file3.py")
        ]
        
        tree = generator.generate_tree(paths)
        
        # Check that the tree contains expected elements
        assert "test/" in tree
        assert "file1.py" in tree
        assert "dir1" in tree
        assert "dir2" in tree
        assert "├──" in tree or "└──" in tree


class TestFileDescriptor:
    """Test file description generation."""
    
    def test_get_file_description(self):
        """Test file description based on patterns."""
        descriptor = FileDescriptor(Path("."))
        
        # Test Python files
        assert "Python" in descriptor.get_file_description(Path("test.py"))
        assert "initialization" in descriptor.get_file_description(Path("__init__.py"))
        assert "entry point" in descriptor.get_file_description(Path("main.py"))
        
        # Test configuration files
        assert "Configuration" in descriptor.get_file_description(Path("config.py"))
        assert "YAML" in descriptor.get_file_description(Path("config.yml"))
        assert "JSON" in descriptor.get_file_description(Path("data.json"))
        
        # Test documentation files
        assert "Markdown" in descriptor.get_file_description(Path("README.md"))
        assert "documentation" in descriptor.get_file_description(Path("README.md"))


class TestAPIDiscovery:
    """Test API route discovery."""
    
    def test_flask_route_parsing(self):
        """Test Flask route detection."""
        discovery = APIDiscovery(Path("."))
        
        # Create a temporary Python file with Flask routes
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
from flask import Blueprint

bp = Blueprint("test", __name__)

@bp.route("/users", methods=["GET", "POST"])
def users():
    pass

@bp.route("/profile/<user_id>", methods=["GET"])
def profile(user_id):
    pass
''')
            temp_file = Path(f.name)
        
        try:
            routes = discovery._extract_routes_from_file(temp_file)
            
            # Should find both routes
            assert len(routes) >= 2
            
            # Check that both methods are found for the first route
            methods = [route['method'] for route in routes if route['path'] == '/users']
            assert 'GET' in methods
            assert 'POST' in methods
            
        finally:
            temp_file.unlink()
    
    def test_fastapi_route_parsing(self):
        """Test FastAPI route detection."""
        discovery = APIDiscovery(Path("."))
        
        # Create a temporary Python file with FastAPI routes
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    pass

@router.post("/data")
async def create_data():
    pass
''')
            temp_file = Path(f.name)
        
        try:
            routes = discovery._extract_routes_from_file(temp_file)
            
            # Should find both routes
            assert len(routes) >= 2
            
            # Check specific routes
            paths = [route['path'] for route in routes]
            methods = [route['method'] for route in routes]
            
            assert '/health' in paths
            assert '/data' in paths
            assert 'GET' in methods
            assert 'POST' in methods
            
        finally:
            temp_file.unlink()


class TestStructureGeneration:
    """Test complete structure generation."""
    
    def test_structure_generation_with_temp_dir(self):
        """Test structure generation with a temporary directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a simple directory structure
            (temp_path / "src").mkdir()
            (temp_path / "src" / "main.py").write_text("# Main file")
            (temp_path / "tests").mkdir()
            (temp_path / "tests" / "test_main.py").write_text("# Test file")
            (temp_path / "README.md").write_text("# Test Project")
            
            # Generate structure
            generator = StructureGenerator(temp_path)
            structure_data = generator.generate_structure()
            
            # Check that all sections are present
            assert 'tree' in structure_data
            assert 'mermaid' in structure_data
            assert 'descriptions' in structure_data
            assert 'api_routes' in structure_data
            
            # Check tree content
            tree = structure_data['tree']
            assert 'src' in tree
            assert 'tests' in tree
            assert 'README.md' in tree
            
            # Check descriptions
            descriptions = structure_data['descriptions']
            assert 'src' in descriptions
            assert 'Directory' in descriptions
            
            # Check mermaid
            mermaid = structure_data['mermaid']
            assert 'flowchart TD' in mermaid
            assert 'main.py' in mermaid


if __name__ == '__main__':
    pytest.main([__file__])