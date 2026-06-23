ALLOWED_TOOLS={'nmap'}
def ensure_allowed_tool(tool:str)->None:
    if tool not in ALLOWED_TOOLS: raise ValueError(f'Tool not allowed: {tool}')
