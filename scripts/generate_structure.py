#!/usr/bin/env python3
"""
Dynamic Project Structure Generator
This script scans the project directory structure and generates multiple representations:
- ASCII tree view
- Mermaid diagram flowchart
- File description table
- Auto-discovered FastAPI routes
Security features:
- Path validation to prevent directory traversal
- Configurable exclusion patterns
- Input sanitization for markdown output
- Secure file operations using pathlib
Usage:
    python scripts/generate_structure.py [--output-file README.md] [--config-file config.json]
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union
import ast
import inspect
from dataclasses import dataclass, asdict


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class FileDescription:
    """Data class for file descriptions."""
    path: str
    type: str
    description: str
    size: Optional[int] = None


@dataclass
class GeneratorConfig:
    """Configuration for the structure generator."""
    exclude_patterns: List[str]
    include_extensions: List[str]
    max_file_size: int
    enable_api_discovery: bool
    enable_mermaid: bool
    enable_tree: bool
    enable_descriptions: bool


class SecurityValidator:
    """Validates paths and inputs for security."""

    @staticmethod
    def validate_path(path: Path, base_path: Path) -> bool:
        """
        Validate that a path is within the base directory and safe to access.
        
        Args:
            path: Path to validate
            base_path: Base directory path
            
        Returns:
            bool: True if path is safe to access
        """
        try:
            # Resolve paths to handle symlinks and relative paths
            resolved_path = path.resolve()
            resolved_base = base_path.resolve()

            # Check if path is within base directory
            return str(resolved_path).startswith(str(resolved_base))
        except (OSError, ValueError) as e:
            logger.warning(f"Path validation error for {path}: {e}")
            return False

    @staticmethod
    def sanitize_markdown(text: str) -> str:
        """
        Sanitize text for safe markdown output.
        
        Args:
            text: Text to sanitize
            
        Returns:
            str: Sanitized text
        """
        # Escape markdown special characters
        markdown_chars = ['*', '_', '`', '[', ']', '(', ')', '#', '+', '-', '.', '!']
        for char in markdown_chars:
            text = text.replace(char, f'\\{char}')
        return text


class DirectoryScanner:
    """Scans directory structure with security validation."""

    def __init__(self, base_path: Path, config: GeneratorConfig):
        self.base_path = base_path.resolve()
        self.config = config
        self.validator = SecurityValidator()

    def should_exclude(self, path: Path) -> bool:
        """
        Check if a path should be excluded based on patterns.
        
        Args:
            path: Path to check
            
        Returns:
            bool: True if path should be excluded
        """
        path_str = str(path.relative_to(self.base_path))

        for pattern in self.config.exclude_patterns:
            if re.match(pattern, path_str) or pattern in path_str:
                return True
        return False

    def scan_directory(self) -> List[Path]:
        """
        Scan directory structure and return valid paths.
        
        Returns:
            List[Path]: List of valid file and directory paths
        """
        valid_paths = []

        try:
            for path in self.base_path.rglob('*'):
                # Security validation
                if not self.validator.validate_path(path, self.base_path):
                    logger.warning(f"Skipping unsafe path: {path}")
                    continue

                # Exclusion check
                if self.should_exclude(path):
                    continue

                # File size check
                if path.is_file():
                    try:
                        if path.stat().st_size > self.config.max_file_size:
                            logger.info(f"Skipping large file: {path}")
                            continue
                    except OSError:
                        continue

                valid_paths.append(path)

        except Exception as e:
            logger.error(f"Error scanning directory: {e}")

        return sorted(valid_paths)


class TreeGenerator:
    """Generates ASCII tree representation."""

    def __init__(self, base_path: Path):
        self.base_path = base_path

    def generate_tree(self, paths: List[Path]) -> str:
        """
        Generate ASCII tree representation.
        
        Args:
            paths: List of paths to include in tree
            
        Returns:
            str: ASCII tree representation
        """
        tree_dict = {}

        # Build tree structure
        for path in paths:
            parts = path.relative_to(self.base_path).parts
            current = tree_dict

            for part in parts:
                if part not in current:
                    current[part] = {}
                current = current[part]

        # Generate tree string
        tree_lines = [self.base_path.name + '/']
        self._build_tree_lines(tree_dict, tree_lines, prefix='')

        return '\n'.join(tree_lines)

    def _build_tree_lines(self, tree_dict: Dict, lines: List[str], prefix: str = ''):
        """Recursively build tree lines."""
        items = list(tree_dict.items())
        for i, (name, subtree) in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = '└── ' if is_last else '├── '
            lines.append(f"{prefix}{current_prefix}{name}")

            if subtree:
                next_prefix = prefix + ('    ' if is_last else '│   ')
                self._build_tree_lines(subtree, lines, next_prefix)


class MermaidGenerator:
    """Generates Mermaid diagram representation."""

    def __init__(self, base_path: Path):
        self.base_path = base_path

    def generate_mermaid(self, paths: List[Path]) -> str:
        """
        Generate Mermaid flowchart diagram.
        
        Args:
            paths: List of paths to include in diagram
            
        Returns:
            str: Mermaid diagram representation
        """
        lines = ['flowchart TD', f'  R[{self.base_path.name}/]', '']
        node_id = 1
        path_to_id = {'': 'R'}

        # Generate nodes and connections
        for path in paths:
            relative_path = path.relative_to(self.base_path)
            parts = relative_path.parts

            current_path = ''
            parent_id = 'R'

            for part in parts:
                current_path = str(Path(current_path) / part) if current_path else part

                if current_path not in path_to_id:
                    node_id += 1
                    current_id = f'n{node_id}'
                    path_to_id[current_path] = current_id

                    # Determine node style
                    if path.is_dir():
                        lines.append(f'  {parent_id} --> {current_id}[{part}/]')
                    else:
                        lines.append(f'  {parent_id} --> {current_id}({part})')

                parent_id = path_to_id[current_path]

        return '\n'.join(lines)


class FileDescriptor:
    """Generates file descriptions based on naming conventions."""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.description_patterns = {
            r'.*\.py$': 'Python source file',
            r'.*__init__\.py$': 'Python package initialization file',
            r'.*main\.py$': 'Python application entry point',
            r'.*config\.py$': 'Configuration module',
            r'.*test_.*\.py$': 'Python test file',
            r'.*\.yml$|.*\.yaml$': 'YAML configuration file',
            r'.*\.json$': 'JSON data file',
            r'.*\.md$': 'Markdown documentation file',
            r'.*README\.md$': 'Main project documentation',
            r'.*\.txt$': 'Text file',
            r'.*requirements.*\.txt$': 'Python dependencies file',
            r'.*pyproject\.toml$': 'Python project configuration file',
            r'.*Dockerfile.*': 'Docker container configuration',
            r'.*\.env.*': 'Environment variables file',
            r'.*LICENSE.*': 'License file',
            r'.*\.gitignore$': 'Git ignore patterns file',
        }

    def get_file_description(self, path: Path) -> str:
        """
        Get description for a file based on naming patterns.
        
        Args:
            path: File path
            
        Returns:
            str: File description
        """
        filename = path.name.lower()
        relative_path = str(path.relative_to(self.base_path)).lower()

        # Check specific patterns
        for pattern, description in self.description_patterns.items():
            if re.match(pattern, relative_path) or re.match(pattern, filename):
                return description

        # Check if it's a directory
        if path.is_dir():
            return self._get_directory_description(path)

        # Default description based on extension
        suffix = path.suffix.lower()
        extension_descriptions = {
            '.py': 'Python source file',
            '.js': 'JavaScript file',
            '.css': 'Cascading Style Sheets file',
            '.html': 'HTML template file',
            '.sql': 'SQL database script',
            '.sh': 'Shell script',
            '.log': 'Log file',
        }

        return extension_descriptions.get(suffix, 'File')

    def _get_directory_description(self, path: Path) -> str:
        """Get description for a directory based on its name and contents."""
        dir_name = path.name.lower()

        directory_descriptions = {
            'tests': 'Test files and test utilities',
            'src': 'Source code directory',
            'docs': 'Documentation files',
            'scripts': 'Utility and automation scripts',
            'api': 'API route definitions',
            'core': 'Core application logic',
            'services': 'Business logic services',
            'models': 'Data models and schemas',
            'utils': 'Utility functions',
            'config': 'Configuration modules',
            'static': 'Static assets (CSS, JS, images)',
            'templates': 'HTML templates',
            'migrations': 'Database migration files',
            '.github': 'GitHub configuration and workflows',
        }

        return directory_descriptions.get(dir_name, 'Directory')

    def generate_description_table(self, paths: List[Path]) -> str:
        """
        Generate markdown table of file descriptions.
        
        Args:
            paths: List of paths to describe
            
        Returns:
            str: Markdown table
        """
        descriptions = []
        validator = SecurityValidator()

        for path in paths:
            try:
                relative_path = path.relative_to(self.base_path)
                description = self.get_file_description(path)
                file_type = 'Directory' if path.is_dir() else 'File'

                # Sanitize for markdown
                path_str = validator.sanitize_markdown(str(relative_path))
                desc_str = validator.sanitize_markdown(description)

                descriptions.append({
                    'path': path_str,
                    'type': file_type,
                    'description': desc_str
                })
            except Exception as e:
                logger.warning(f"Error processing path {path}: {e}")

        # Generate table
        if not descriptions:
            return "No files to describe."

        lines = [
            "| Path | Type | Description |",
            "|------|------|-------------|"
        ]

        for desc in descriptions[:50]:  # Limit to first 50 items
            lines.append(f"| {desc['path']} | {desc['type']} | {desc['description']} |")

        if len(descriptions) > 50:
            lines.append(f"| ... | ... | ... and {len(descriptions) - 50} more items |")

        return '\n'.join(lines)


class APIDiscovery:
    """Discovers FastAPI routes from Python files."""

    def __init__(self, base_path: Path):
        self.base_path = base_path

    def discover_routes(self, paths: List[Path]) -> List[Dict[str, str]]:
        """
        Discover FastAPI routes from Python files.
        
        Args:
            paths: List of paths to scan
            
        Returns:
            List[Dict]: List of discovered routes
        """
        routes = []

        for path in paths:
            if path.suffix == '.py' and path.is_file():
                try:
                    routes.extend(self._extract_routes_from_file(path))
                except Exception as e:
                    logger.debug(f"Error scanning {path} for routes: {e}")

        return routes

    def _extract_routes_from_file(self, file_path: Path) -> List[Dict[str, str]]:
        """Extract routes from a Python file using AST parsing."""
        routes = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Look for FastAPI/Flask decorators
                    for decorator in node.decorator_list:
                        route_info = self._parse_decorator(decorator, file_path)
                        if route_info:
                            if isinstance(route_info, list):
                                # Multiple methods for same path (Flask)
                                for info in route_info:
                                    info['function'] = node.name
                                    routes.append(info)
                            else:
                                # Single method
                                route_info['function'] = node.name
                                routes.append(route_info)

        except Exception as e:
            logger.debug(f"Error parsing {file_path}: {e}")

        return routes

    def _parse_decorator(self, decorator, file_path: Path) -> Optional[Union[Dict[str, str], List[Dict[str, str]]]]:
        """Parse FastAPI/Flask decorator to extract route information."""
        if isinstance(decorator, ast.Call):
            # FastAPI router decorators (e.g., @router.get("/path"))
            if isinstance(decorator.func, ast.Attribute):
                method = decorator.func.attr.lower()
                if method in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']:
                    # Extract path from first argument
                    if decorator.args and isinstance(decorator.args[0], ast.Constant):
                        path = decorator.args[0].value
                        return {
                            'method': method.upper(),
                            'path': path,
                            'file': str(file_path.relative_to(self.base_path))
                        }

                # Flask route decorators: @bp.route("/path", methods=["GET", "POST"])
                elif decorator.func.attr == 'route':
                    path = None
                    methods = ['GET']  # Default method

                    # Extract path from first argument
                    if decorator.args and isinstance(decorator.args[0], ast.Constant):
                        path = decorator.args[0].value

                    # Extract methods from keyword arguments
                    for keyword in decorator.keywords:
                        if keyword.arg == 'methods' and isinstance(keyword.value, ast.List):
                            methods = []
                            for method_node in keyword.value.elts:
                                if isinstance(method_node, ast.Constant):
                                    methods.append(method_node.value)

                    if path:
                        # Return multiple entries for multiple methods
                        results = []
                        for method in methods:
                            results.append({
                                'method': method.upper(),
                                'path': path,
                                'file': str(file_path.relative_to(self.base_path))
                            })
                        return results

        return None

    def generate_api_table(self, routes: List[Dict[str, str]]) -> str:
        """Generate markdown table of API routes."""
        if not routes:
            return "No API routes discovered."

        lines = [
            "| Method | Path | Function | File |",
            "|--------|------|----------|------|"
        ]

        for route in routes:
            lines.append(
                f"| {route['method']} | {route['path']} | "
                f"{route['function']} | {route['file']} |"
            )

        return '\n'.join(lines)


class StructureGenerator:
    """Main structure generator class."""

    def __init__(self, base_path: Path, config: Optional[GeneratorConfig] = None):
        self.base_path = base_path.resolve()
        self.config = config or self._get_default_config()

        # Initialize components
        self.scanner = DirectoryScanner(self.base_path, self.config)
        self.tree_generator = TreeGenerator(self.base_path)
        self.mermaid_generator = MermaidGenerator(self.base_path)
        self.file_descriptor = FileDescriptor(self.base_path)
        self.api_discovery = APIDiscovery(self.base_path)

    def _get_default_config(self) -> GeneratorConfig:
        """Get default configuration."""
        return GeneratorConfig(
            exclude_patterns=[
                r'\.git.*',
                r'__pycache__.*',
                r'\.env.*',
                r'.*\.pyc$',
                r'.*\.log$',
                r'venv.*',
                r'node_modules.*',
                r'\.pytest_cache.*',
                r'.*\.egg-info.*',
                r'dist/.*',
                r'build/.*'
            ],
            include_extensions=['.py', '.md', '.yml', '.yaml', '.json', '.txt', '.toml'],
            max_file_size=1024 * 1024,  # 1MB
            enable_api_discovery=True,
            enable_mermaid=True,
            enable_tree=True,
            enable_descriptions=True
        )

    def generate_structure(self) -> Dict[str, str]:
        """
        Generate all structure representations.
        
        Returns:
            Dict[str, str]: Dictionary with different representations
        """
        logger.info(f"Scanning directory: {self.base_path}")
        paths = self.scanner.scan_directory()
        logger.info(f"Found {len(paths)} valid paths")

        result = {}

        # Generate tree view
        if self.config.enable_tree:
            logger.info("Generating tree view")
            result['tree'] = self.tree_generator.generate_tree(paths)

        # Generate Mermaid diagram
        if self.config.enable_mermaid:
            logger.info("Generating Mermaid diagram")
            result['mermaid'] = self.mermaid_generator.generate_mermaid(paths)

        # Generate file descriptions
        if self.config.enable_descriptions:
            logger.info("Generating file descriptions")
            result['descriptions'] = self.file_descriptor.generate_description_table(paths)

        # Discover API routes
        if self.config.enable_api_discovery:
            logger.info("Discovering API routes")
            routes = self.api_discovery.discover_routes(paths)
            result['api_routes'] = self.api_discovery.generate_api_table(routes)

        return result

    def update_readme(self, readme_path: Path, structure_data: Dict[str, str]) -> bool:
        """
        Update README file with generated structure.
        
        Args:
            readme_path: Path to README file
            structure_data: Generated structure data
            
        Returns:
            bool: True if update was successful
        """
        try:
            # Read current README
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Generate structure section
            structure_section = self._build_structure_section(structure_data)

            # Replace content between markers
            start_marker = '<!-- START STRUCTURE -->'
            end_marker = '<!-- END STRUCTURE -->'

            start_idx = content.find(start_marker)
            end_idx = content.find(end_marker)

            if start_idx == -1 or end_idx == -1:
                logger.error("Structure markers not found in README")
                return False

            # Build new content
            new_content = (
                content[:start_idx + len(start_marker)] +
                '\n' + structure_section + '\n' +
                content[end_idx:]
            )

            # Write updated README
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            logger.info(f"Updated README: {readme_path}")
            return True

        except Exception as e:
            logger.error(f"Error updating README: {e}")
            return False

    def _build_structure_section(self, structure_data: Dict[str, str]) -> str:
        """Build the complete structure section for README."""
        sections = []

        sections.append("## Project Structure\n")

        if 'tree' in structure_data:
            sections.append("### Directory Tree\n")
            sections.append("```")
            sections.append(structure_data['tree'])
            sections.append("```\n")

        if 'descriptions' in structure_data:
            sections.append("### File Descriptions\n")
            sections.append(structure_data['descriptions'])
            sections.append("")

        if 'api_routes' in structure_data:
            sections.append("### API Endpoints\n")
            sections.append(structure_data['api_routes'])
            sections.append("")

        if 'mermaid' in structure_data:
            sections.append("### Structure Diagram\n")
            sections.append("```mermaid")
            sections.append(structure_data['mermaid'])
            sections.append("```\n")

        return '\n'.join(sections)


def load_config(config_path: Optional[Path]) -> Optional[GeneratorConfig]:
    """Load configuration from JSON file."""
    if not config_path or not config_path.exists():
        return None

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        return GeneratorConfig(**config_data)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate dynamic project structure documentation"
    )
    parser.add_argument(
        '--output-file',
        type=Path,
        default=Path('README.md'),
        help='Output README file path (default: README.md)'
    )
    parser.add_argument(
        '--config-file',
        type=Path,
        help='Configuration file path (JSON format)'
    )
    parser.add_argument(
        '--base-path',
        type=Path,
        default=Path('.'),
        help='Base directory to scan (default: current directory)'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load configuration
    config = load_config(args.config_file)

    # Initialize generator
    generator = StructureGenerator(args.base_path, config)

    try:
        # Generate structure data
        structure_data = generator.generate_structure()

        # Update README if requested
        if args.output_file:
            success = generator.update_readme(args.output_file, structure_data)
            if success:
                logger.info("README updated successfully")
            else:
                logger.error("Failed to update README")
                sys.exit(1)
        else:
            # Print to stdout
            print(generator._build_structure_section(structure_data))

    except Exception as e:
        logger.error(f"Error generating structure: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
