"""Regras de transição de etapas do Kanban (validação alinhada ao backend e ao frontend)."""

from __future__ import annotations

MSG_SKIP = "Não é possível avançar para esta etapa. Conclua a etapa anterior primeiro."
MSG_BACKWARD = "Transição não permitida."
MSG_JA_PERDIDO = "Este lead já está como perdido."
MSG_MESMA_ETAPA = "O lead já está nesta etapa."

FORWARD = ("novo", "em_contato", "proposta_enviada", "convertido")


def transition_allowed(old_status: str, new_status: str) -> tuple[bool, str | None]:
    """
    Retorna (permitido, mensagem_erro).
    Fluxo linear: NOVO → EM CONTATO → PROPOSTA ENVIADA → CONVERTIDO.
    PERDIDO a partir de qualquer etapa exceto já estar em PERDIDO.
    """
    if old_status == new_status:
        return False, MSG_MESMA_ETAPA
    if old_status == "perdido":
        return False, MSG_JA_PERDIDO
    if new_status == "perdido":
        return True, None

    if old_status not in FORWARD or new_status not in FORWARD:
        return False, MSG_BACKWARD

    i_old = FORWARD.index(old_status)
    i_new = FORWARD.index(new_status)

    if i_new == i_old + 1:
        return True, None
    if i_new > i_old + 1:
        return False, MSG_SKIP
    return False, MSG_BACKWARD
