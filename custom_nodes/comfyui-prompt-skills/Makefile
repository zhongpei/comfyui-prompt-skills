# ComfyUI Prompt Skills - Makefile
# 三层解耦架构构建与测试

.PHONY: help install install-dev build build-vue test lint clean all standalone debug

# 默认目标
help:
	@echo "ComfyUI Prompt Skills - 可用命令:"
	@echo ""
	@echo "  make install          - 安装 Python 依赖"
	@echo "  make install-dev      - 安装开发依赖 (包含测试)"
	@echo "  make build            - 构建所有 (Python + Vue)"
	@echo "  make build-vue        - 仅构建 Vue 前端"
	@echo "  make package          - 打包 Python wheel"
	@echo "  make dist             - 创建完整发布包"
	@echo "  make deploy           - 部署到远程服务器"
	@echo "  make test             - 运行单元测试 (快速)"
	@echo "  make test-integration - 运行集成测试 (启动 OpenCode Server)"
	@echo "  make test-all         - 运行所有测试"
	@echo "  make standalone       - 启动独立前端测试服务器"
	@echo "  make debug            - 启动调试模式服务器"
	@echo "  make lint             - 代码检查"
	@echo "  make clean            - 清理构建产物"
	@echo "  make all              - 完整安装+构建+测试"
	@echo ""


# ============================================
# 安装
# ============================================

install:
	@echo "📦 Installing Python dependencies..."
	pip install -e .

install-dev:
	@echo "📦 Installing Python dev dependencies..."
	pip install -e ".[dev]"

install-vue:
	@echo "📦 Installing Node.js dependencies..."
	cd web && npm install

# ============================================
# 构建
# ============================================

build: build-vue
	@echo "✅ Build complete!"

build-vue:
	@echo "🔨 Building Vue frontend..."
	cd web && npm run build
	@echo "✅ Vue build output in js/"

# ============================================
# 打包与发布
# ============================================

package: build
	@echo "📦 Building Python wheel package..."
	pip install build
	python -m build --wheel
	@echo "✅ Wheel package built in dist/"

dist: package
	@echo "📦 Creating distribution package..."
	rm -rf dist/deploy
	mkdir -p dist/deploy
	cp -r js/ dist/deploy/js/
	cp -r skills/ dist/deploy/skills/
	cp -r data/ dist/deploy/data/
	cp -r backend/ dist/deploy/backend/
	cp -r nodes/ dist/deploy/nodes/
	cp __init__.py dist/deploy/
	cp install.sh dist/deploy/
	cp dist/*.whl dist/deploy/
	cp ../../opencode.json dist/deploy/
	@echo "✅ Distribution package ready in dist/deploy/"

deploy:
	@echo "🚀 Deploying to remote server..."
	../../sync.sh


# ============================================
# 测试
# ============================================

test:
	@echo "🧪 Running unit tests..."
	COMFYUI_PROMPT_SKILLS_TESTING=1 PYTHONPATH=. pytest tests/ -v --ignore=tests/test_integration.py

test-integration:
	@echo "🧪 Running integration tests (requires OpenCode Server)..."
	@echo "   OpenCode Server will be started automatically..."
	COMFYUI_PROMPT_SKILLS_TESTING=1 PYTHONPATH=. pytest tests/test_integration.py -v -s --timeout=60

test-all:
	@echo "🧪 Running all tests..."
	COMFYUI_PROMPT_SKILLS_TESTING=1 PYTHONPATH=. pytest tests/ -v -s --timeout=60

test-cov:
	@echo "🧪 Running tests with coverage..."
	COMFYUI_PROMPT_SKILLS_TESTING=1 PYTHONPATH=. pytest tests/ -v --cov=backend --cov-report=term-missing --ignore=tests/test_integration.py

test-quick:
	@echo "🧪 Running quick tests..."
	COMFYUI_PROMPT_SKILLS_TESTING=1 PYTHONPATH=. pytest tests/ -v -x --tb=short --ignore=tests/test_integration.py

# ============================================
# 代码质量
# ============================================

lint:
	@echo "🔍 Running linters..."
	-ruff check backend/ nodes/
	-mypy backend/ nodes/ --ignore-missing-imports

format:
	@echo "🎨 Formatting code..."
	ruff format backend/ nodes/

# ============================================
# 清理
# ============================================

clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf js/prompt-skills.*.js js/style.css
	rm -rf web/node_modules
	rm -rf __pycache__ */__pycache__ */*/__pycache__
	rm -rf .pytest_cache tests/.pytest_cache
	rm -rf *.egg-info
	rm -rf .ruff_cache
	@echo "✅ Clean complete!"

clean-all: clean
	@echo "🧹 Deep cleaning..."
	rm -rf .venv
	rm -rf web/dist
	rm -rf dist/

# ============================================
# 开发工作流
# ============================================

dev-setup: install-dev install-vue build-vue
	@echo "✅ Development environment ready!"

dev-vue:
	@echo "🔄 Starting Vue dev server..."
	cd web && npm run dev

standalone:
	@echo "🚀 Starting standalone Flask server..."
	@echo "   访问 http://127.0.0.1:5000/standalone/ 进行测试"
	@echo ""
	COMFYUI_PROMPT_SKILLS_TESTING=1 python -c "from backend.logic import create_app, socketio; app = create_app(debug=True); socketio.run(app, host='127.0.0.1', port=5000, allow_unsafe_werkzeug=True)"

debug:
	@echo "🔧 Starting Flask server in DEBUG mode..."
	@echo "   环境变量 COMFYUI_PROMPT_SKILLS_DEBUG=1 已启用"
	@echo "   访问 http://127.0.0.1:5000/standalone/ 进行测试"
	@echo ""
	COMFYUI_PROMPT_SKILLS_TESTING=1 COMFYUI_PROMPT_SKILLS_DEBUG=1 python -c "from backend.logic import create_app, socketio; app = create_app(debug=True); socketio.run(app, host='127.0.0.1', port=5000, allow_unsafe_werkzeug=True)"

# ============================================
# 完整流程
# ============================================

all: install-dev install-vue build test
	@echo ""
	@echo "🎉 All done! Ready to use in ComfyUI."
