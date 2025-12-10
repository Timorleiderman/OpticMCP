"""
MCP Client for testing the Optic MCP server.
"""
import asyncio
import base64
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    """Connect to the Optic MCP server and test camera tools."""
    
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "-q", "python", "optic_mcp.py"],
    )
    
    print("Connecting to Optic MCP server...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            print("Connected!\n")
            
            # List available tools
            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                desc = tool.description or ""
                print(f"  - {tool.name}: {desc[:60]}...")
            print()
            
            # List cameras
            print("Listing cameras...")
            result = await session.call_tool("list_cameras", {})
            
            # Parse all camera entries from content
            cameras = []
            for content in result.content:  # type: ignore
                camera_text = getattr(content, "text", str(content))
                print(f"  Found: {camera_text}")
                cameras.append(json.loads(camera_text))
            print()
            
            if not cameras:
                print("No cameras found!")
                return
            
            # Use the first available camera
            camera_index = cameras[0]["index"]
            print(f"Using camera at index {camera_index}")
            
            # Capture an image
            print("Capturing image...")
            result = await session.call_tool("capture_image", {"camera_index": camera_index})
            content = result.content[0]  # type: ignore
            image_data = getattr(content, "text", str(content))
            
            # Save the base64 image to a file
            image_bytes = base64.b64decode(image_data)
            
            output_path = "mcp_captured_image.jpg"
            with open(output_path, "wb") as f:
                f.write(image_bytes)
            
            print(f"Image saved to {output_path} ({len(image_bytes)} bytes)")
            
            # Also test save_image tool
            print("\nTesting save_image tool...")
            result = await session.call_tool(
                "save_image", 
                {"file_path": "mcp_saved_image.jpg", "camera_index": camera_index}
            )
            content = result.content[0]  # type: ignore
            save_result = getattr(content, "text", str(content))
            print(f"Result: {save_result}")


if __name__ == "__main__":
    asyncio.run(main())
