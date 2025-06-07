#!/bin/bash

# Prompta CLI Manual Test Script
# This script tests all CLI commands to ensure they work correctly
# Run this from the package directory: ./tests/manual/test_cli_commands.sh

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_RUN=0
TESTS_PASSED=0

# Helper functions
log_test() {
    echo -e "${YELLOW}[TEST $((++TESTS_RUN))] $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ PASSED: $1${NC}"
    ((TESTS_PASSED++))
}

log_error() {
    echo -e "${RED}❌ FAILED: $1${NC}"
}

run_command() {
    local cmd="$1"
    local description="$2"
    
    log_test "$description"
    echo "Command: $cmd"
    
    if eval "$cmd"; then
        log_success "$description"
        echo ""
    else
        log_error "$description"
        echo ""
        return 1
    fi
}

# Start testing
echo "=================================================="
echo "🧪 Prompta CLI Manual Test Suite"
echo "=================================================="
echo ""

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
    echo ""
fi

# Test 1: Version check
run_command "python -m prompta --version" "Check CLI version"

# Test 2: Help commands
run_command "python -m prompta --help" "Show main help"
run_command "python -m prompta status --help" "Show status help"
run_command "python -m prompta project --help" "Show project help" 
run_command "python -m prompta prompt --help" "Show prompt help"
run_command "python -m prompta export --help" "Show export help"

# Test 3: Status and connectivity
run_command "python -m prompta status" "Check full status"
run_command "python -m prompta ping" "Quick ping test"

# Test 4: Project management
run_command "python -m prompta project list" "List projects"
run_command "python -m prompta project list --page 1 --page-size 5" "List projects with pagination"

# Check if we have any projects to test with
PROJECT_COUNT=$(python -m prompta project list --page-size 1 2>/dev/null | grep -c "^[a-f0-9\-]" || echo "0")

if [ "$PROJECT_COUNT" -gt 0 ]; then
    # Get first project ID for testing
    PROJECT_ID=$(python -m prompta project list --page-size 1 2>/dev/null | grep "^[a-f0-9\-]" | head -1 | cut -d' ' -f1)
    
    if [ ! -z "$PROJECT_ID" ]; then
        run_command "python -m prompta project show $PROJECT_ID" "Show project details"
    fi
else
    echo "⚠️  No projects found - skipping project detail tests"
fi

# Test 5: Prompt management
run_command "python -m prompta prompt list" "List prompts"
run_command "python -m prompta prompt list --page 1 --page-size 5" "List prompts with pagination"
run_command "python -m prompta prompt list --tags frontend" "List prompts by tags"

# Check if we have any prompts to test with
PROMPT_COUNT=$(python -m prompta prompt list --page-size 1 2>/dev/null | grep -v "^Name" | grep -v "^─" | grep -c "│" || echo "0")

if [ "$PROMPT_COUNT" -gt 0 ]; then
    # Get first prompt name for testing
    PROMPT_NAME=$(python -m prompta prompt list --page-size 1 2>/dev/null | grep "│" | head -1 | cut -d'│' -f1 | xargs)
    
    if [ ! -z "$PROMPT_NAME" ]; then
        run_command "python -m prompta prompt show \"$PROMPT_NAME\"" "Show prompt content"
        run_command "python -m prompta prompt info \"$PROMPT_NAME\"" "Show prompt info"
        run_command "python -m prompta prompt version list \"$PROMPT_NAME\"" "List prompt versions"
    fi
else
    echo "⚠️  No prompts found - skipping prompt detail tests"
fi

# Test 6: Search functionality
run_command "python -m prompta prompt search react" "Search prompts by content"

# Test 7: Create test prompt from file
TEST_FILE="test_prompt_temp.md"
cat > "$TEST_FILE" << 'EOF'
# Test Prompt

This is a test prompt for CLI testing.

## Purpose
Testing the CLI create functionality.

## Tags
- test
- cli
- automation
EOF

run_command "python -m prompta prompt create $TEST_FILE --name 'CLI Test Prompt' --description 'Test prompt for CLI' --tags 'test,cli' --message 'Created via CLI test'" "Create prompt from file"

# Clean up test file
rm -f "$TEST_FILE"

# Test 8: Export functionality
if [ "$PROJECT_COUNT" -gt 0 ] && [ ! -z "$PROJECT_ID" ]; then
    # Create test output directory
    mkdir -p test_exports
    
    run_command "python -m prompta export project $PROJECT_ID --output test_exports --format files" "Export project as files"
    run_command "python -m prompta export project $PROJECT_ID --output test_exports --format json" "Export project as JSON"
    
    # Clean up
    rm -rf test_exports
fi

# Test 9: Export all with filters
run_command "python -m prompta export all --tags frontend --format json --output test_export_all.json" "Export all prompts by tag as JSON"

# Clean up export file
rm -f test_export_all.json

# Test 10: Legacy alias commands
run_command "python -m prompta list" "Test legacy 'list' alias"

if [ "$PROMPT_COUNT" -gt 0 ] && [ ! -z "$PROMPT_NAME" ]; then
    run_command "python -m prompta show \"$PROMPT_NAME\"" "Test legacy 'show' alias"
fi

# Test 11: Error handling tests
echo ""
echo "=================================================="
echo "🔍 Testing Error Handling"
echo "=================================================="

# Test with non-existent resources
log_test "Test non-existent prompt"
if python -m prompta prompt show "non-existent-prompt-12345" 2>/dev/null; then
    log_error "Should have failed for non-existent prompt"
else
    log_success "Correctly handled non-existent prompt"
    ((TESTS_PASSED++))
fi
((TESTS_RUN++))

log_test "Test non-existent project"
if python -m prompta project show "non-existent-project-12345" 2>/dev/null; then
    log_error "Should have failed for non-existent project"
else
    log_success "Correctly handled non-existent project"
    ((TESTS_PASSED++))
fi
((TESTS_RUN++))

# Final summary
echo ""
echo "=================================================="
echo "📊 Test Summary"
echo "=================================================="
echo "Tests run: $TESTS_RUN"
echo "Tests passed: $TESTS_PASSED"
echo "Tests failed: $((TESTS_RUN - TESTS_PASSED))"

if [ $TESTS_PASSED -eq $TESTS_RUN ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed.${NC}"
    exit 1
fi