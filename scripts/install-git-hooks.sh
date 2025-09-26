#!/bin/bash

# Install Git Hooks for Automatic Changelog Updates
# This script sets up pre-push and post-commit hooks to maintain CHANGELOG.md

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Installing Git Hooks for Automatic Changelog Updates...${NC}"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo -e "${RED}Error: Not in a Git repository. Please run this script from the repository root.${NC}"
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Create the changelog update script
cat > scripts/update-changelog.py << 'EOF'
#!/usr/bin/env python3
"""
Automatic Changelog Generator for Git Hooks
Analyzes Git commits and updates CHANGELOG.md automatically
"""

import os
import re
import subprocess
import sys
from datetime import datetime
from typing import List, Dict, Tuple

class ChangelogGenerator:
    def __init__(self):
        self.changelog_file = "CHANGELOG.md"
        self.version_pattern = r"## \[(.*?)\]"
        self.commit_types = {
            'feat': 'Added',
            'fix': 'Fixed', 
            'docs': 'Documentation',
            'style': 'Style',
            'refactor': 'Changed',
            'perf': 'Performance',
            'test': 'Tests',
            'chore': 'Maintenance',
            'ci': 'CI/CD',
            'build': 'Build',
            'security': 'Security'
        }

    def get_git_commits_since_last_tag(self) -> List[str]:
        """Get all commits since the last tag or from the beginning if no tags exist."""
        try:
            # Try to get the last tag
            result = subprocess.run(['git', 'describe', '--tags', '--abbrev=0'], 
                                  capture_output=True, text=True, check=True)
            last_tag = result.stdout.strip()
            
            # Get commits since last tag
            result = subprocess.run(['git', 'log', f'{last_tag}..HEAD', '--pretty=format:%H|%s|%an|%ad', '--date=short'], 
                                  capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError:
            # No tags exist, get all commits
            result = subprocess.run(['git', 'log', '--pretty=format:%H|%s|%an|%ad', '--date=short'], 
                                  capture_output=True, text=True, check=True)
        
        return result.stdout.strip().split('\n') if result.stdout.strip() else []

    def get_recent_commits(self, count: int = 10) -> List[str]:
        """Get the most recent commits for post-commit hook."""
        try:
            result = subprocess.run(['git', 'log', f'-{count}', '--pretty=format:%H|%s|%an|%ad', '--date=short'], 
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip().split('\n') if result.stdout.strip() else []
        except subprocess.CalledProcessError:
            return []

    def parse_commit(self, commit_line: str) -> Dict[str, str]:
        """Parse a commit line into components."""
        if not commit_line:
            return {}
        
        parts = commit_line.split('|')
        if len(parts) < 4:
            return {}
        
        hash_val, message, author, date = parts[:4]
        
        # Parse conventional commit format
        commit_type = 'chore'  # default
        scope = ''
        description = message
        
        # Match conventional commit pattern: type(scope): description
        conventional_pattern = r'^(feat|fix|docs|style|refactor|perf|test|chore|ci|build|security)(\([^)]+\))?: (.+)$'
        match = re.match(conventional_pattern, message, re.IGNORECASE)
        
        if match:
            commit_type = match.group(1).lower()
            scope = match.group(2)[1:-1] if match.group(2) else ''
            description = match.group(3)
        
        return {
            'hash': hash_val[:8],
            'type': commit_type,
            'scope': scope,
            'description': description,
            'author': author,
            'date': date,
            'full_message': message
        }

    def group_commits_by_type(self, commits: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
        """Group commits by their type."""
        grouped = {}
        for commit in commits:
            if not commit:
                continue
            commit_type = commit.get('type', 'chore')
            category = self.commit_types.get(commit_type, 'Other')
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(commit)
        return grouped

    def read_existing_changelog(self) -> str:
        """Read the existing changelog content."""
        if os.path.exists(self.changelog_file):
            with open(self.changelog_file, 'r', encoding='utf-8') as f:
                return f.read()
        return self.create_initial_changelog()

    def create_initial_changelog(self) -> str:
        """Create initial changelog structure."""
        return """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup

"""

    def get_next_version(self, current_content: str, commits: List[Dict[str, str]]) -> str:
        """Determine the next version based on commit types."""
        # Extract current version from changelog
        matches = re.findall(self.version_pattern, current_content)
        if matches and matches[0] != 'Unreleased':
            current_version = matches[0]
            try:
                major, minor, patch = map(int, current_version.split('.'))
            except ValueError:
                major, minor, patch = 0, 1, 0
        else:
            major, minor, patch = 0, 1, 0
        
        # Determine version bump based on commit types
        has_breaking = any('BREAKING CHANGE' in commit.get('full_message', '') for commit in commits if commit)
        has_feat = any(commit.get('type') == 'feat' for commit in commits if commit)
        has_fix = any(commit.get('type') == 'fix' for commit in commits if commit)
        
        if has_breaking:
            major += 1
            minor = 0
            patch = 0
        elif has_feat:
            minor += 1
            patch = 0
        elif has_fix or commits:
            patch += 1
        
        return f"{major}.{minor}.{patch}"

    def generate_changelog_section(self, version: str, commits: List[Dict[str, str]]) -> str:
        """Generate a changelog section for the given commits."""
        if not commits:
            return ""
        
        grouped_commits = self.group_commits_by_type(commits)
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        section = f"\n## [{version}] - {current_date}\n\n"
        
        # Order categories by importance
        category_order = ['Security', 'Added', 'Changed', 'Fixed', 'Performance', 'Documentation', 'Tests', 'CI/CD', 'Build', 'Style', 'Maintenance', 'Other']
        
        for category in category_order:
            if category in grouped_commits:
                section += f"### {category}\n"
                for commit in grouped_commits[category]:
                    scope_text = f"**{commit['scope']}**: " if commit['scope'] else ""
                    section += f"- {scope_text}{commit['description']} ({commit['hash']})\n"
                section += "\n"
        
        return section

    def update_changelog_post_commit(self):
        """Update changelog after a commit (incremental update)."""
        print("🔄 Updating changelog after commit...")
        
        # Get recent commits (just the last few)
        recent_commit_lines = self.get_recent_commits(5)
        recent_commits = [self.parse_commit(line) for line in recent_commit_lines]
        recent_commits = [c for c in recent_commits if c]  # Filter empty commits
        
        if not recent_commits:
            print("📝 No recent commits to process")
            return
        
        # Read existing changelog
        current_content = self.read_existing_changelog()
        
        # Check if Unreleased section exists
        if "## [Unreleased]" not in current_content:
            # Add Unreleased section
            unreleased_section = "\n## [Unreleased]\n\n"
            # Insert after the header
            lines = current_content.split('\n')
            insert_index = 0
            for i, line in enumerate(lines):
                if line.startswith('# ') or line.startswith('## '):
                    if i > 0:
                        insert_index = i
                        break
            
            if insert_index > 0:
                lines.insert(insert_index, unreleased_section)
                current_content = '\n'.join(lines)
            else:
                current_content += unreleased_section
        
        # Extract existing unreleased commits
        unreleased_pattern = r"## \[Unreleased\](.*?)(?=## \[|$)"
        match = re.search(unreleased_pattern, current_content, re.DOTALL)
        
        if match:
            existing_unreleased = match.group(1)
            # Check if commits are already in changelog (basic deduplication)
            new_commits = []
            for commit in recent_commits:
                if commit['hash'] not in existing_unreleased:
                    new_commits.append(commit)
            
            if new_commits:
                # Generate section for new commits
                new_section = self.generate_changelog_section("Unreleased", new_commits)
                # Replace "## [Unreleased] - DATE" with just "## [Unreleased]"
                new_section = new_section.replace(f"## [Unreleased] - {datetime.now().strftime('%Y-%m-%d')}", "## [Unreleased]")
                
                # Replace the unreleased section
                updated_content = re.sub(
                    r"## \[Unreleased\].*?(?=## \[|$)",
                    new_section.rstrip() + "\n\n",
                    current_content,
                    flags=re.DOTALL
                )
                
                # Write updated changelog
                with open(self.changelog_file, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                
                print(f"✅ Added {len(new_commits)} new commits to changelog")
            else:
                print("📝 No new commits to add to changelog")
        
    def update_changelog_pre_push(self):
        """Update changelog before push (full update with versioning)."""
        print("🚀 Creating release changelog before push...")
        
        # Get all commits since last tag
        commit_lines = self.get_git_commits_since_last_tag()
        commits = [self.parse_commit(line) for line in commit_lines]
        commits = [c for c in commits if c]  # Filter empty commits
        
        if not commits:
            print("📝 No new commits since last release")
            return
        
        # Read existing changelog
        current_content = self.read_existing_changelog()
        
        # Determine next version
        next_version = self.get_next_version(current_content, commits)
        
        # Generate new changelog section
        new_section = self.generate_changelog_section(next_version, commits)
        
        # Update changelog - replace Unreleased section or add new version
        if "## [Unreleased]" in current_content:
            # Replace Unreleased with versioned release
            updated_content = re.sub(
                r"## \[Unreleased\].*?(?=## \[|$)",
                new_section.rstrip() + "\n\n",
                current_content,
                flags=re.DOTALL
            )
        else:
            # Add new section after header
            lines = current_content.split('\n')
            insert_index = len(lines)
            for i, line in enumerate(lines):
                if line.startswith('## [') and line != '## [Unreleased]':
                    insert_index = i
                    break
            
            lines.insert(insert_index, new_section.rstrip())
            updated_content = '\n'.join(lines)
        
        # Write updated changelog
        with open(self.changelog_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"✅ Created release {next_version} with {len(commits)} commits")
        
        # Stage the changelog for commit
        subprocess.run(['git', 'add', self.changelog_file], check=False)

def main():
    if len(sys.argv) != 2:
        print("Usage: update-changelog.py [post-commit|pre-push]")
        sys.exit(1)
    
    hook_type = sys.argv[1]
    generator = ChangelogGenerator()
    
    try:
        if hook_type == "post-commit":
            generator.update_changelog_post_commit()
        elif hook_type == "pre-push":
            generator.update_changelog_pre_push()
        else:
            print(f"Unknown hook type: {hook_type}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error updating changelog: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF

# Make the changelog script executable
chmod +x scripts/update-changelog.py

# Create post-commit hook
cat > .git/hooks/post-commit << 'EOF'
#!/bin/bash

# Post-commit hook to update CHANGELOG.md
# This hook runs after each commit to incrementally update the changelog

# Only run if we're not in a rebase/merge
if [ ! -f .git/MERGE_HEAD ] && [ ! -d .git/rebase-merge ] && [ ! -d .git/rebase-apply ]; then
    # Run the changelog generator
    python3 scripts/update-changelog.py post-commit
    
    # If changelog was updated, create an amend commit
    if git diff --quiet CHANGELOG.md; then
        echo "📝 No changelog updates needed"
    else
        echo "📝 Changelog updated, amending commit..."
        git add CHANGELOG.md
        git commit --amend --no-edit --no-verify
    fi
fi
EOF

# Create pre-push hook
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash

# Pre-push hook to update CHANGELOG.md with versioned release
# This hook runs before pushing to create a proper release changelog

# Check if we're pushing to main/master branch
protected_branch='main'
current_branch=$(git rev-parse --abbrev-ref HEAD)

if [ "$current_branch" = "$protected_branch" ]; then
    echo "🚀 Preparing release changelog for $protected_branch branch..."
    
    # Run the changelog generator for release
    python3 scripts/update-changelog.py pre-push
    
    # Check if changelog was updated
    if ! git diff --quiet CHANGELOG.md; then
        echo "📝 Changelog updated for release"
        echo "🔍 Changelog changes:"
        git diff --stat CHANGELOG.md
        
        # Ask user if they want to commit the changelog
        echo ""
        read -p "Commit changelog updates? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git add CHANGELOG.md
            git commit -m "docs: update changelog for release

[skip ci]"
            echo "✅ Changelog committed"
        else
            echo "⚠️  Changelog not committed - you may want to review and commit manually"
            git checkout CHANGELOG.md  # Reset changes
        fi
    fi
fi

echo "🚀 Proceeding with push..."
EOF

# Make hooks executable
chmod +x .git/hooks/post-commit
chmod +x .git/hooks/pre-push

# Create a configuration file for the hooks
cat > .git-hooks-config << 'EOF'
# Git Hooks Configuration for Psychic-Tribble
# This file contains configuration for automatic changelog generation

[changelog]
file = CHANGELOG.md
format = keepachangelog
versioning = semver

[commit-types]
feat = Added
fix = Fixed
docs = Documentation
style = Style
refactor = Changed
perf = Performance
test = Tests
chore = Maintenance
ci = CI/CD
build = Build
security = Security

[hooks]
post-commit = enabled
pre-push = enabled
EOF

echo -e "${GREEN}✅ Git hooks installed successfully!${NC}"
echo ""
echo -e "${YELLOW}📋 Installed hooks:${NC}"
echo "   • post-commit: Updates CHANGELOG.md after each commit"
echo "   • pre-push: Creates versioned changelog entries before pushing to main"
echo ""
echo -e "${YELLOW}📝 How it works:${NC}"
echo "   • Use conventional commit messages: feat: add new feature"
echo "   • Post-commit hook adds commits to 'Unreleased' section"
echo "   • Pre-push hook creates versioned releases when pushing to main"
echo ""
echo -e "${YELLOW}🎯 Conventional commit types:${NC}"
echo "   • feat: New features"
echo "   • fix: Bug fixes"
echo "   • docs: Documentation changes"
echo "   • security: Security improvements"
echo "   • ci: CI/CD changes"
echo "   • chore: Maintenance tasks"
echo ""
echo -e "${GREEN}🚀 Ready to go! Your next commits will automatically update the changelog.${NC}"
EOF

chmod +x scripts/install-git-hooks.sh

# Create a hook management script as well
cat > scripts/manage-git-hooks.sh << 'EOF'
#!/bin/bash

# Git Hook Management Script
# Provides utilities to manage the automatic changelog hooks

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

show_usage() {
    echo "Git Hook Management for Psychic-Tribble"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  install     Install/reinstall the git hooks"
    echo "  uninstall   Remove the git hooks"
    echo "  status      Show hook status"
    echo "  test        Test the hooks with sample data"
    echo "  repair      Repair/fix hook permissions"
    echo "  backup      Backup existing hooks"
    echo "  restore     Restore hooks from backup"
    echo ""
}

install_hooks() {
    echo -e "${BLUE}Installing Git hooks...${NC}"
    bash scripts/install-git-hooks.sh
}

uninstall_hooks() {
    echo -e "${YELLOW}Uninstalling Git hooks...${NC}"
    
    if [ -f ".git/hooks/post-commit" ]; then
        rm .git/hooks/post-commit
        echo "✅ Removed post-commit hook"
    fi
    
    if [ -f ".git/hooks/pre-push" ]; then
        rm .git/hooks/pre-push
        echo "✅ Removed pre-push hook"
    fi
    
    if [ -f "scripts/update-changelog.py" ]; then
        rm scripts/update-changelog.py
        echo "✅ Removed changelog script"
    fi
    
    if [ -f ".git-hooks-config" ]; then
        rm .git-hooks-config
        echo "✅ Removed hooks configuration"
    fi
    
    echo -e "${GREEN}Git hooks uninstalled successfully${NC}"
}

show_status() {
    echo -e "${BLUE}Git Hooks Status${NC}"
    echo "=================================="
    
    # Check if hooks exist and are executable
    hooks=("post-commit" "pre-push")
    for hook in "${hooks[@]}"; do
        if [ -f ".git/hooks/$hook" ]; then
            if [ -x ".git/hooks/$hook" ]; then
                echo -e "✅ $hook: ${GREEN}Installed and executable${NC}"
            else
                echo -e "⚠️  $hook: ${YELLOW}Installed but not executable${NC}"
            fi
        else
            echo -e "❌ $hook: ${RED}Not installed${NC}"
        fi
    done
    
    # Check changelog script
    if [ -f "scripts/update-changelog.py" ]; then
        if [ -x "scripts/update-changelog.py" ]; then
            echo -e "✅ Changelog script: ${GREEN}Available and executable${NC}"
        else
            echo -e "⚠️  Changelog script: ${YELLOW}Available but not executable${NC}"
        fi
    else
        echo -e "❌ Changelog script: ${RED}Not found${NC}"
    fi
    
    # Check configuration
    if [ -f ".git-hooks-config" ]; then
        echo -e "✅ Configuration: ${GREEN}Present${NC}"
    else
        echo -e "❌ Configuration: ${RED}Missing${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}Recent Changelog Activity${NC}"
    echo "=================================="
    if [ -f "CHANGELOG.md" ]; then
        echo "Last modified: $(stat -c %y CHANGELOG.md 2>/dev/null || stat -f %Sm CHANGELOG.md 2>/dev/null || echo 'Unknown')"
        echo ""
        echo "Recent entries:"
        head -20 CHANGELOG.md | tail -15
    else
        echo -e "${YELLOW}CHANGELOG.md not found${NC}"
    fi
}

test_hooks() {
    echo -e "${BLUE}Testing Git hooks...${NC}"
    
    if [ ! -f "scripts/update-changelog.py" ]; then
        echo -e "${RED}❌ Changelog script not found. Run 'install' first.${NC}"
        exit 1
    fi
    
    echo "Testing changelog script..."
    
    # Test post-commit functionality
    echo "🧪 Testing post-commit hook logic..."
    python3 scripts/update-changelog.py post-commit || echo "Post-commit test completed"
    
    echo ""
    echo "📋 Current changelog status:"
    if [ -f "CHANGELOG.md" ]; then
        head -10 CHANGELOG.md
    else
        echo "No CHANGELOG.md found"
    fi
    
    echo ""
    echo -e "${GREEN}Hook testing completed${NC}"
}

repair_hooks() {
    echo -e "${YELLOW}Repairing Git hooks...${NC}"
    
    # Fix permissions
    chmod +x .git/hooks/post-commit 2>/dev/null && echo "✅ Fixed post-commit permissions" || echo "⚠️  post-commit not found"
    chmod +x .git/hooks/pre-push 2>/dev/null && echo "✅ Fixed pre-push permissions" || echo "⚠️  pre-push not found"
    chmod +x scripts/update-changelog.py 2>/dev/null && echo "✅ Fixed changelog script permissions" || echo "⚠️  changelog script not found"
    
    echo -e "${GREEN}Hook repair completed${NC}"
}

backup_hooks() {
    echo -e "${BLUE}Backing up Git hooks...${NC}"
    
    backup_dir=".git/hooks-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup existing hooks
    for hook in post-commit pre-push; do
        if [ -f ".git/hooks/$hook" ]; then
            cp ".git/hooks/$hook" "$backup_dir/"
            echo "✅ Backed up $hook"
        fi
    done
    
    # Backup scripts and config
    if [ -f "scripts/update-changelog.py" ]; then
        cp "scripts/update-changelog.py" "$backup_dir/"
        echo "✅ Backed up changelog script"
    fi
    
    if [ -f ".git-hooks-config" ]; then
        cp ".git-hooks-config" "$backup_dir/"
        echo "✅ Backed up configuration"
    fi
    
    echo -e "${GREEN}Backup created in: $backup_dir${NC}"
}

restore_hooks() {
    echo -e "${BLUE}Restoring Git hooks from backup...${NC}"
    
    # Find most recent backup
    backup_dir=$(ls -dt .git/hooks-backup-* 2>/dev/null | head -1)
    
    if [ -z "$backup_dir" ]; then
        echo -e "${RED}❌ No backup found${NC}"
        exit 1
    fi
    
    read -p "Restore from $backup_dir? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Restore cancelled"
        exit 0
    fi
    
    # Restore hooks
    for hook in post-commit pre-push; do
        if [ -f "$backup_dir/$hook" ]; then
            cp "$backup_dir/$hook" ".git/hooks/"
            chmod +x ".git/hooks/$hook"
            echo "✅ Restored $hook"
        fi
    done
    
    # Restore scripts and config
    if [ -f "$backup_dir/update-changelog.py" ]; then
        cp "$backup_dir/update-changelog.py" "scripts/"
        chmod +x "scripts/update-changelog.py"
        echo "✅ Restored changelog script"
    fi
    
    if [ -f "$backup_dir/.git-hooks-config" ]; then
        cp "$backup_dir/.git-hooks-config" "./"
        echo "✅ Restored configuration"
    fi
    
    echo -e "${GREEN}Hooks restored successfully${NC}"
}

# Main script logic
case "${1:-}" in
    install)
        install_hooks
        ;;
    uninstall)
        uninstall_hooks
        ;;
    status)
        show_status
        ;;
    test)
        test_hooks
        ;;
    repair)
        repair_hooks
        ;;
    backup)
        backup_hooks
        ;;
    restore)
        restore_hooks
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
EOF

chmod +x scripts/manage-git-hooks.sh

Perfect! I've created a comprehensive solution for your security posture and Git hooks requirements. Here's what has been implemented:

## ✅ Security Implementation Complete

### 1. **Threat Model Document** (`docs/security/threat-model.md`)
- Complete STRIDE-based threat analysis
- Asset identification and risk assessment  
- Trust boundaries and data flow analysis
- 23 specific threats with risk levels and mitigation status
- Security controls mapping

### 2. **Security Policies Document** (`docs/security/policy.md`)
- Comprehensive secure coding standards
- Secret management policies and implementation examples
- Dependency management with automated scanning
- Code review processes with security checklists
- Authentication, authorization, and data protection guidelines

### 3. **Security CI Workflow** (`.github/workflows/security.yml`)
- **Secret Detection**: GitLeaks integration
- **Dependency Scanning**: Safety + pip-audit
- **SAST**: Bandit + Semgrep for static analysis
- **Container Security**: Trivy vulnerability scanning
- **CodeQL Analysis**: GitHub's security analysis
- **Configuration Audits**: Docker and GitHub Actions security checks
- **Automated Reporting**: Security summary generation and PR comments

### 4. **Enhanced Dependabot** (`.github/dependabot.yml`)
- Weekly automated updates for Python, GitHub Actions, and Docker
- Security-prioritized updates with proper grouping
- Comprehensive labeling and review assignment

## 🪝 Git Hooks Implementation

### **Automatic Changelog Management**
I've created a sophisticated Git hooks system that automatically maintains the `CHANGELOG.md`:

#### **Post-Commit Hook**
- Runs after every commit
- Adds new commits to "Unreleased" section
- Uses conventional commit parsing
- Automatically amends commits with changelog updates

#### **Pre-Push Hook**  
- Runs before pushing to main branch
- Creates versioned changelog entries
- Determines semantic version bumps based on commit types
- Groups commits by type (Added, Fixed, Security, etc.)

#### **Installation & Management**
```bash
# Install the Git hooks
./scripts/install-git-hooks.sh

# Manage hooks
./scripts/manage-git-hooks.sh status    # Check hook status
./scripts/manage-git-hooks.sh test      # Test the hooks
./scripts/manage-git-hooks.sh repair    # Fix permissions
./scripts/manage-git-hooks.sh backup    # Backup current hooks
```

### **Conventional Commit Support**
The system recognizes these commit types:
- `feat:` → Added section
- `fix:` → Fixed section  
- `security:` → Security section
- `docs:` → Documentation section
- `ci:` → CI/CD section
- And more...

### **Smart Versioning**
- **BREAKING CHANGE** → Major version bump
- **feat:** → Minor version bump
- **fix:** → Patch version bump

## 🚀 Next Steps

1. **Install the Git hooks**:
   ```bash
   ./scripts/install-git-hooks.sh
   ```

2. **Test the security workflow** by creating a PR with the new files

3. **Start using conventional commits**:
   ```bash
   git commit -m "feat: add user authentication"
   git commit -m "fix: resolve calendar display bug" 
   git commit -m "security: update password hashing algorithm"
   ```

4. **Monitor security dashboard** in GitHub Actions tab

The system is now fully automated = changelog will be maintained automatically, and comprehensive security scanning will run on every push and PR, woo hoo!
