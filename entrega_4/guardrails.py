import re


_BLOCKED_PATTERNS = (
    re.compile(
        r"\b(ignore|ignora|ignorá|olvida|olvidá)\b.{0,100}"
        r"\b(instrucciones|reglas|prompt|system|políticas|politicas)\b",
        re.I,
    ),
    re.compile(r"\b(revela|revelá|muestra|mostrá|dame|pasame|pasá)\b.{0,80}\b(claves?|credenciales?|contraseñas?|passwords?|secretos?)\b", re.I),
    re.compile(r"\b(system prompt|developer message|api key|secret key)\b", re.I),
    re.compile(
        r"\b(a partir de ahora|from now on|sos ahora|eres ahora)\b.{0,80}"
        r"\b(administrador|admin|developer|desarrollador|sistema|system)\b",
        re.I,
    ),
)

MAX_INPUT_LENGTH = 4000

_EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
_PHONE_PATTERN = re.compile(
    r"(?<!\w)(?:\+\d{1,3}[\s().-]?(?:9[\s().-]?)?)?"
    r"(?:\(?\d{2,4}\)?[\s().-]?)?\d{3,4}[\s.-]\d{4}(?!\w)"
)
_PHONE_DIGITS_PATTERN = re.compile(r"(?<!\d)\+?\d{10,15}(?!\d)")
_CUIL_PATTERN = re.compile(r"(?<!\d)(?:\d{2}-\d{8}-\d|\d{11})(?!\d)")
_DNI_PATTERN = re.compile(r"(?<!\d)\d{7,8}(?!\d)")

_WRITE_INTENT = re.compile(
    r"\b(registr(a|á|ar)|guard(a|á|ar)|anot(a|á|ar)|agend(a|á|ar)|"
    r"seguimiento|dej(a|á) asentad[oa])\b",
    re.I,
)


class GuardrailBlock(ValueError):
    """Raised when a request matches a deterministic safety rule."""


def validate_input_length(text: str) -> str:
    """Trim input and enforce the maximum accepted query length.

    Raises:
        ValueError: If the trimmed query is empty or longer than 4000 characters.
    """
    normalized = text.strip()
    if not normalized:
        raise ValueError("La consulta no puede estar vacía.")
    if len(normalized) > MAX_INPUT_LENGTH:
        raise ValueError(f"La consulta supera el límite de {MAX_INPUT_LENGTH} caracteres.")
    return normalized


def validate_prompt_injection(text: str) -> None:
    """Reject common prompt-injection and credential-exfiltration requests.

    The checks are deterministic and run before any model or tool is invoked.

    Raises:
        GuardrailBlock: If the query matches a blocked instruction pattern.
    """
    normalized = " ".join(text.split())
    if any(pattern.search(normalized) for pattern in _BLOCKED_PATTERNS):
        raise GuardrailBlock("Consulta bloqueada por las reglas de seguridad.")


def validate_request(text: str) -> None:
    """Validate prompt-injection patterns before passing a request to the agent."""
    validate_prompt_injection(text)


def mask_personal_data(text: str) -> str:
    """Mask common personal identifiers in text before it leaves the API.

    Masks email addresses, phone numbers, Argentine CUIT/CUIL, and 7-8 digit
    DNI-like identifiers while leaving scouting source IDs such as DOC-006 intact.
    """
    masked = _EMAIL_PATTERN.sub("[EMAIL REDACTADO]", text)
    masked = _CUIL_PATTERN.sub("[CUIL REDACTADO]", masked)
    masked = _PHONE_PATTERN.sub("[TELÉFONO REDACTADO]", masked)
    masked = _PHONE_DIGITS_PATTERN.sub("[TELÉFONO REDACTADO]", masked)
    return _DNI_PATTERN.sub("[DNI REDACTADO]", masked)


def explicitly_requests_write(text: str) -> bool:
    """Return whether the user explicitly asked to persist a scouting note."""
    return bool(_WRITE_INTENT.search(text))
