from dotenv import load_dotenv
from fastmcp import FastMCP
from osf_assistant.tools.preregistration import generate_preregistration, osf_upload
from osf_assistant.tools.evidence import search_evidence, format_evidence_table

load_dotenv()

mcp = FastMCP(name="OSF Assistant")

mcp.tool()(generate_preregistration)
mcp.tool()(osf_upload)
mcp.tool()(search_evidence)
mcp.tool()(format_evidence_table)

if __name__ == "__main__":
    mcp.run()
