.PHONY: test test-unit test-integration sync clean help start-server stop-server

# Default target
help:
	@echo "Available targets:"
	@echo "  make test             - Run all tests (starts server if needed)"
	@echo "  make test-unit        - Run unit tests only (no server required)"
	@echo "  make test-integration - Run integration tests only (requires server)"
	@echo "  make start-server     - Start OpenCode server"
	@echo "  make stop-server      - Stop OpenCode server"
	@echo "  make sync             - Sync to remote server"
	@echo "  make clean            - Clean cache files"

# Plugin directory
PLUGIN_DIR := custom_nodes/comfyui-prompt-skills
TEST_DIR := $(PLUGIN_DIR)/tests

# Start OpenCode server in background
start-server:
	@echo "Starting OpenCode server..."
	@pkill -f "opencode serve" 2>/dev/null || true
	@sleep 1
	@opencode serve --port 4096 --hostname 127.0.0.1 &
	@echo "Waiting for server to start..."
	@sleep 5
	@echo "Server started on http://127.0.0.1:4096"

# Stop OpenCode server
stop-server:
	@echo "Stopping OpenCode server..."
	@pkill -f "opencode serve" 2>/dev/null || true
	@echo "Server stopped"

# Run all tests
test: stop-server start-server
	@echo ""
	@echo "============================================================"
	@echo "Running all tests..."
	@echo "============================================================"
	@cd $(TEST_DIR) && python run_tests.py
	@echo ""
	@echo "Stopping server after tests..."
	@$(MAKE) stop-server

# Run unit tests only (no server required)
test-unit:
	@echo ""
	@echo "============================================================"
	@echo "Running unit tests only..."
	@echo "============================================================"
	@cd $(TEST_DIR) && python -c "\
import sys; \
sys.path.insert(0, '..'); \
from run_tests import *; \
result = TestResult(); \
print('--- Unit Tests ---'); \
run_test(result, 'OutputFormatter basic', test_output_formatter); \
run_test(result, 'OutputFormatter validation', test_output_formatter_validation); \
run_test(result, 'OutputFormatter fallback', test_output_formatter_fallback); \
run_test(result, 'Bridge system prompt', test_bridge_system_prompt); \
run_test(result, 'Bridge fallback response', test_bridge_fallback_response); \
run_test(result, 'Bridge parse response', test_bridge_parse_response); \
run_test(result, 'Style library', test_style_library); \
run_test(result, 'Skill files', test_skill_files); \
run_test(result, 'ServerManager singleton', test_server_manager_singleton); \
run_test(result, 'ServerManager config', test_server_manager_config); \
result.summary(); \
sys.exit(0 if result.failed == 0 else 1); \
"

# Run integration tests only
test-integration: start-server
	@echo ""
	@echo "============================================================"
	@echo "Running integration tests only..."
	@echo "============================================================"
	@cd $(TEST_DIR) && python -c "\
import sys; \
sys.path.insert(0, '..'); \
from run_tests import *; \
result = TestResult(); \
manager = get_server_manager(); \
if not manager.is_running: \
    print('ERROR: Server not running'); \
    sys.exit(1); \
print('--- Integration Tests ---'); \
run_test(result, 'Server available', test_server_available); \
run_test(result, 'Session create (API)', test_session_create); \
run_test(result, 'Session list', test_session_list); \
run_test(result, 'SessionManager create', test_session_manager_create); \
run_test(result, 'SessionManager get_or_create', test_session_manager_get_or_create); \
run_test(result, 'Session send message', test_session_send_message); \
run_test(result, 'Prompt generation (photo)', test_prompt_generation); \
run_test(result, 'Prompt generation (hanfu)', test_prompt_generation_hanfu); \
run_test(result, 'Prompt generation (manga)', test_prompt_generation_manga); \
run_test(result, 'Full workflow', test_full_workflow); \
result.summary(); \
sys.exit(0 if result.failed == 0 else 1); \
"
	@$(MAKE) stop-server

# Sync to remote server
sync:
	@./sync.sh

# Clean cache files
clean:
	@echo "Cleaning cache files..."
	@find $(PLUGIN_DIR) -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find $(PLUGIN_DIR) -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -f $(PLUGIN_DIR)/logs/.session_cache.json 2>/dev/null || true
	@echo "Done"
