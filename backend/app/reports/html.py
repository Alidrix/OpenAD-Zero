from html import escape
import re
try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:  # pragma: no cover
    Environment = FileSystemLoader = select_autoescape = None
try:
    import markdown as md
except ImportError:  # pragma: no cover
    md = None

def _fallback_markdown(text: str) -> str:
    html=[]
    for line in text.splitlines():
        if line.startswith('# '): html.append(f'<h1>{escape(line[2:])}</h1>')
        elif line.startswith('## '): html.append(f'<h2>{escape(line[3:])}</h2>')
        elif line.startswith('- '): html.append(f'<li>{escape(line[2:])}</li>')
        elif line.strip(): html.append(f'<p>{escape(line)}</p>')
    return '\n'.join(html)

def _wrap(title: str, content: str, risk_summary: dict) -> str:
    badges=''.join(f'<span class="badge {escape(str(k))}">{escape(str(k))}: {escape(str(v))}</span>' for k,v in risk_summary.items())
    return f'''<!doctype html><html><head><meta charset="utf-8"><title>{escape(title)}</title><style>body{{font-family:Inter,Arial,sans-serif;margin:0;background:#f8fafc;color:#0f172a}}.wrap{{max-width:1100px;margin:0 auto;padding:32px}}.card{{background:white;border:1px solid #e2e8f0;border-radius:16px;padding:28px}}h1,h2{{color:#1e3a8a}}table{{width:100%;border-collapse:collapse;margin:16px 0}}th,td{{border:1px solid #cbd5e1;padding:8px;text-align:left}}th{{background:#eff6ff}}code{{background:#e2e8f0;padding:2px 5px;border-radius:4px}}.badges{{display:flex;gap:8px;flex-wrap:wrap}}.badge{{border-radius:999px;padding:4px 10px;font-weight:700}}.critical{{background:#7f1d1d;color:#fff}}.high{{background:#dc2626;color:#fff}}.medium{{background:#f59e0b}}.low{{background:#38bdf8}}.info{{background:#e2e8f0}}</style></head><body><main class="wrap"><section class="card"><h1>{escape(title)}</h1><div class="badges">{badges}</div><hr>{content}</section></main></body></html>'''

def render_html_report(markdown_content: str, data: dict) -> str:
    body = md.markdown(markdown_content, extensions=['tables','toc']) if md else _fallback_markdown(markdown_content)
    body = re.sub(r'<script\b.*?</script>', '', body, flags=re.I|re.S)
    title=f"OpenAD Zero Report - {data['mission'].get('name')}"
    return _wrap(title, body, data.get('risk_summary',{}))
