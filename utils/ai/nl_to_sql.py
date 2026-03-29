import re, logging
from django.conf import settings
logger = logging.getLogger(__name__)

class NLToSQLEngine:
    SYSTEM_PROMPT = """You are a SQL expert. Write a safe SELECT query answering the user's question.
The table is called 'data'. Only use columns from the provided schema.
Format your response as:
SQL:
<sql>
EXPLANATION:
<explanation>"""
    def __init__(self, dataset):
        self.dataset = dataset
    def generate(self, question: str) -> dict:
        schema = self._build_schema_context()
        prompt = f"Schema:\n{schema}\n\nQuestion: {question}"
        try:
            if settings.LLM_PROVIDER == "anthropic":
                return self._call_anthropic(prompt)
            return self._call_openai(prompt)
        except Exception as exc:
            return {"success": False, "sql": "", "explanation": str(exc), "tokens_used": 0}
    def _build_schema_context(self) -> str:
        lines = [f"Table: data ({self.dataset.row_count} rows)"]
        for col in self.dataset.columns.all():
            sample = ", ".join(str(v) for v in col.sample_values[:3])
            lines.append(f"  {col.name} ({col.data_type}): e.g. {sample}")
        return "\n".join(lines)
    def _call_anthropic(self, prompt):
        import anthropic
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        msg = client.messages.create(model=settings.LLM_MODEL, max_tokens=settings.LLM_MAX_TOKENS,
            system=self.SYSTEM_PROMPT, messages=[{"role":"user","content":prompt}])
        return {"success": True, **self._parse(msg.content[0].text),
                "tokens_used": msg.usage.input_tokens + msg.usage.output_tokens}
    def _call_openai(self, prompt):
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        r = client.chat.completions.create(model="gpt-4o-mini",
            messages=[{"role":"system","content":self.SYSTEM_PROMPT},{"role":"user","content":prompt}])
        return {"success": True, **self._parse(r.choices[0].message.content), "tokens_used": r.usage.total_tokens}
    def _parse(self, text):
        sql = re.search(r"SQL:\s*(.+?)(?=EXPLANATION:|$)", text, re.DOTALL)
        exp = re.search(r"EXPLANATION:\s*(.+)", text, re.DOTALL)
        return {
            "sql": re.sub(r"```sql|```","", sql.group(1)).strip() if sql else "",
            "explanation": exp.group(1).strip() if exp else "",
        }
