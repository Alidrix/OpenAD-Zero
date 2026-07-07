from __future__ import annotations

from fastapi import APIRouter

from app.tool_catalog.families import FAMILIES
from app.tool_catalog.readiness import tool_readiness
from app.tool_catalog.registry import get_tool_catalog, list_template_metadata, list_tools

router = APIRouter(prefix='/v2/tool-catalog', tags=['v2-tool-catalog'])


@router.get('')
def catalog():
    return get_tool_catalog()


@router.get('/families')
def families():
    return [family.to_dict() for family in FAMILIES.values()]


@router.get('/tools')
def tools():
    return [tool.to_dict() for tool in list_tools()]


@router.get('/templates')
def templates():
    return [template.to_dict(include_argv=False) for template in list_template_metadata()]


@router.get('/readiness')
def readiness():
    return tool_readiness()
