"""Tests for OpticMCP server module structure."""


def test_import_module():
    """Test that the module can be imported."""
    import optic_mcp

    assert hasattr(optic_mcp, "__version__")
    assert optic_mcp.__version__.count(".") == 2


def test_mcp_tools_registered():
    """Test that all MCP tools are available."""
    from optic_mcp import server

    assert hasattr(server, "list_cameras")
    assert hasattr(server, "capture_image")
    assert hasattr(server, "save_image")
    assert hasattr(server, "rtsp_capture_image")
    assert hasattr(server, "rtsp_save_image")
    assert hasattr(server, "rtsp_check_stream")
