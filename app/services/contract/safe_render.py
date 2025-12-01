from jinja2 import Environment, BaseLoader, StrictUndefined
import json

def render_contract_template_string(template_str: str, **context) -> str:
    env = Environment(
        loader=BaseLoader(),
        autoescape=True,
        undefined=StrictUndefined,  # error if a placeholder is missing/misspelled
    )
    env.filters["tojson"] = lambda v: json.dumps(v, ensure_ascii=False, indent=2)
    return env.from_string(template_str).render(**context)
