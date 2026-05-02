from django import template

register = template.Library()


@register.filter
def telefone_br(value):
    """Exibe (DD) 9 9999 9999 a partir de 11 digitos; caso contrario devolve o valor ou '-'."""
    if value is None or str(value).strip() == "":
        return "-"
    d = "".join(c for c in str(value) if c.isdigit())
    if len(d) != 11:
        return str(value)
    return f"({d[:2]}) {d[2]} {d[3:7]} {d[7:11]}"
