"""Tests for OpticMCP server module structure."""


def test_import_module():
    """Test that the module can be imported."""
    import optic_mcp

    assert hasattr(optic_mcp, "__version__")
    assert optic_mcp.__version__.count(".") == 2


def test_mcp_tools_registered():
    """Test that all MCP tools are available."""
    from optic_mcp import server

    # USB tools
    assert hasattr(server, "list_cameras")
    assert hasattr(server, "save_image")
    # RTSP tools
    assert hasattr(server, "rtsp_save_image")
    assert hasattr(server, "rtsp_check_stream")
    # HLS tools
    assert hasattr(server, "hls_save_image")
    assert hasattr(server, "hls_check_stream")
    # Streaming tools
    assert hasattr(server, "start_stream")
    assert hasattr(server, "stop_stream")
    assert hasattr(server, "list_streams")
    # Dashboard tools
    assert hasattr(server, "start_dashboard")
    assert hasattr(server, "stop_dashboard")
