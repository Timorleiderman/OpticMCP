# OpticMCP - Agent Guidelines

## Commands
- Run server: `uv run python optic_mcp.py`
- Run client test: `uv run python client.py`
- Test camera directly: `uv run python test_camera.py`

## Code Style
- Python 3.13+, use type hints for all function signatures
- Docstrings: multi-line describing what the function does and returns
- Naming: `snake_case` for functions/variables, descriptive names
- Imports: stdlib → third-party → local, one per line
- Error handling: raise `RuntimeError` with context, use `try/finally` for cleanup

## Critical: OpenCV + MCP
OpenCV prints to stderr which corrupts MCP stdio. Always suppress stderr at fd level
BEFORE importing cv2 (see `_suppress_opencv_stderr()` in optic_mcp.py).

## MCP Tools
When adding camera/vision tools, use the `@mcp.tool()` decorator. Tools should
return JSON-serializable data or base64-encoded images for binary data.
