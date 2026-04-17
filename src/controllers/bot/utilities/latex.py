"""
Convert LaTeX math expressions to Telegram-readable Unicode + <code> blocks.
Applied at display time only — the database stores original LaTeX.
"""
import re

_GREEK = {
    r'\alpha': 'α', r'\beta': 'β', r'\gamma': 'γ', r'\delta': 'δ',
    r'\epsilon': 'ε', r'\zeta': 'ζ', r'\eta': 'η', r'\theta': 'θ',
    r'\iota': 'ι', r'\kappa': 'κ', r'\lambda': 'λ', r'\mu': 'μ',
    r'\nu': 'ν', r'\xi': 'ξ', r'\pi': 'π', r'\rho': 'ρ',
    r'\sigma': 'σ', r'\tau': 'τ', r'\phi': 'φ', r'\chi': 'χ',
    r'\psi': 'ψ', r'\omega': 'ω',
    r'\Gamma': 'Γ', r'\Delta': 'Δ', r'\Theta': 'Θ', r'\Lambda': 'Λ',
    r'\Pi': 'Π', r'\Sigma': 'Σ', r'\Phi': 'Φ', r'\Psi': 'Ψ', r'\Omega': 'Ω',
}

_SYMBOLS = {
    r'\cdot': '·', r'\times': '×', r'\div': '÷',
    r'\leq': '≤', r'\geq': '≥', r'\le': '≤', r'\ge': '≥',
    r'\neq': '≠', r'\approx': '≈',
    r'\infty': '∞', r'\pm': '±', r'\mp': '∓',
    r'\in': '∈', r'\notin': '∉', r'\subset': '⊂', r'\subseteq': '⊆',
    r'\cup': '∪', r'\cap': '∩', r'\emptyset': '∅',
    r'\to': '→', r'\Rightarrow': '⇒', r'\implies': '⟹', r'\Leftrightarrow': '⇔',
    r'\ldots': '…', r'\cdots': '…',
    r'\left(': '(', r'\right)': ')',
    r'\left[': '[', r'\right]': ']',
    r'\left\{': '{', r'\right\}': '}',
    r'\left|': '|', r'\right|': '|',
}

_SUP_MAP = str.maketrans('0123456789+-=()', '⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾')
_SUB_MAP = str.maketrans('0123456789+-=()', '₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎')

_STRIP_CMDS = (
    r'\displaystyle', r'\textstyle', r'\scriptstyle',
    r'\mathrm', r'\mathbf', r'\mathit', r'\mathbb', r'\text',
    r'\overline', r'\underline', r'\hat', r'\vec', r'\bar',
    r'\tilde', r'\dot', r'\ddot', r'\widehat', r'\widetilde',
)


def _clean_latex(expr: str) -> str:
    """Convert a LaTeX expression string to readable Unicode, HTML-safe output."""
    # LaTeX environments: \begin{...}...\end{...} → keep inner content
    expr = re.sub(r'\\begin\{[^}]+\}', '', expr)
    expr = re.sub(r'\\end\{[^}]+\}', '', expr)

    # LaTeX line break \\ → newline
    expr = expr.replace('\\\\', '\n')

    # \frac{a}{b} → (a)/(b)  — loop handles nested fracs
    for _ in range(5):
        expr, n = re.subn(r'\\frac\{([^{}]*)\}\{([^{}]*)\}', r'(\1)/(\2)', expr)
        if not n:
            break

    # \sqrt[n]{x} → ⁿ√(x),  \sqrt{x} → √(x)
    expr = re.sub(r'\\sqrt\[([^\]]+)\]\{([^{}]+)\}', r'\1√(\2)', expr)
    expr = re.sub(r'\\sqrt\{([^{}]+)\}', r'√(\1)', expr)

    # Superscripts: ^{abc}
    def _sup(m):
        inner = m.group(1)
        return inner.translate(_SUP_MAP) if all(c in '0123456789+-=()' for c in inner) else f'^{inner}'
    expr = re.sub(r'\^\{([^{}]+)\}', _sup, expr)
    expr = re.sub(r'\^([0-9])', lambda m: m.group(1).translate(_SUP_MAP), expr)

    # Subscripts: _{abc}
    def _sub(m):
        inner = m.group(1)
        return inner.translate(_SUB_MAP) if all(c in '0123456789+-=()' for c in inner) else f'_{inner}'
    expr = re.sub(r'_\{([^{}]+)\}', _sub, expr)
    expr = re.sub(r'_([0-9])', lambda m: m.group(1).translate(_SUB_MAP), expr)

    # Greek letters and math symbols
    for cmd, sym in {**_GREEK, **_SYMBOLS}.items():
        expr = expr.replace(cmd, sym)

    # Formatting commands that wrap content: \cmd{x} → x
    for cmd in _STRIP_CMDS:
        expr = re.sub(re.escape(cmd) + r'\{([^{}]*)\}', r'\1', expr)
        expr = expr.replace(cmd, '')

    # Remove any remaining unknown \commands
    expr = re.sub(r'\\[a-zA-Z]+\*?\s?', '', expr)
    # Strip bare braces left over
    expr = expr.replace('{', '').replace('}', '')
    # HTML-escape so output is safe for Telegram HTML parse_mode
    expr = expr.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return expr.strip()


def render_for_telegram(text: str) -> str:
    """
    Process a question text for Telegram display.
    Strips LaTeX delimiters and converts expressions to readable Unicode.
    Does NOT add <code> tags — wrap manually where needed.
    """
    # Display math: $$...$$ and \[...\] — keep on own line
    text = re.sub(r'\$\$(.*?)\$\$', lambda m: f'\n{_clean_latex(m.group(1).strip())}', text, flags=re.DOTALL)
    text = re.sub(r'\\\[(.*?)\\\]', lambda m: f'\n{_clean_latex(m.group(1).strip())}', text, flags=re.DOTALL)
    # Inline math: $...$ and \(...\)
    text = re.sub(r'\$(.*?)\$', lambda m: _clean_latex(m.group(1).strip()), text)
    text = re.sub(r'\\\((.*?)\\\)', lambda m: _clean_latex(m.group(1).strip()), text)

    # Clean bare LaTeX outside any existing <code> blocks
    segments = re.split(r'(<code>.*?</code>)', text, flags=re.DOTALL)
    return ''.join(
        seg if seg.startswith('<code>') else _clean_latex(seg)
        for seg in segments
    )