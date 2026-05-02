document.addEventListener("DOMContentLoaded", () => {
    const selects = document.querySelectorAll("select[name='stage_id']");
    selects.forEach((select) => {
        select.addEventListener("change", () => {
            select.closest("form").classList.add("changed");
        });
    });

    function digitsOnlyTel(v) {
        return String(v).replace(/\D/g, "");
    }

    /** 11 dígitos; após DDD o primeiro dígito deve ser 9 (celular). */
    function normalizeTelefone11Digits(raw) {
        let d = digitsOnlyTel(raw).slice(0, 11);
        if (d.length >= 3 && d[2] !== "9") {
            d = `${d.slice(0, 2)}9${d.slice(3)}`.slice(0, 11);
        }
        return d;
    }

    function formatTelefoneBr(raw) {
        const d = normalizeTelefone11Digits(raw);
        if (!d) return "";
        let s = `(${d.slice(0, 2)}`;
        if (d.length <= 2) return s;
        s += `) ${d.slice(2, 3)}`;
        if (d.length <= 3) return s;
        s += ` ${d.slice(3, 7)}`;
        if (d.length <= 7) return s;
        s += ` ${d.slice(7, 11)}`;
        return s;
    }

    /** Vazio (opcional) ou exatamente 11 dígitos com o 3º = 9. */
    function telefoneLeadValid(value) {
        const d = digitsOnlyTel(value);
        if (d.length === 0) return true;
        return d.length === 11 && d[2] === "9";
    }

    function refreshTelefoneValidity(input) {
        if (!input) return;
        if (telefoneLeadValid(input.value)) {
            input.setCustomValidity("");
        } else {
            input.setCustomValidity(
                "Informe 11 dígitos: DDD (2) + número (9). O primeiro dígito após o DDD deve ser 9. Ex.: (11) 9 8765 4321."
            );
        }
    }

    function initTelefoneBrMask(input) {
        if (!input) return;
        const apply = () => {
            const next = formatTelefoneBr(input.value);
            if (next !== input.value) {
                input.value = next;
            }
            refreshTelefoneValidity(input);
        };
        input.addEventListener("input", apply);
        input.addEventListener("blur", () => {
            apply();
            refreshTelefoneValidity(input);
        });
        input.addEventListener("paste", () => setTimeout(apply, 0));
        apply();
    }

    const leadForm = document.getElementById("lead-form");
    if (leadForm) {
        const categorySelect = document.getElementById("id_categoria_profissional");
        const specialtySelect = document.getElementById("id_especialidade");
        const faseSelect = document.getElementById("id_fase_academica");

        const wrapSpecialty = document.getElementById("wrap-especialidade");
        const wrapFase = document.getElementById("wrap-fase_academica");

        const studentCategoryIds = (leadForm.dataset.studentCategories || "")
            .split(",")
            .map((item) => item.trim())
            .filter((item) => item.length > 0);

        function clearSelect(selectEl) {
            if (!selectEl) return;
            selectEl.value = "";
        }

        function setVisibility(element, show) {
            if (!element) return;
            element.style.display = show ? "" : "none";
        }

        async function loadSpecialtiesByCategory(categoryId) {
            if (!specialtySelect) return;
            specialtySelect.innerHTML = '<option value="">---------</option>';
            if (!categoryId) return;

            const response = await fetch(`/kanban/api/especialidades/?categoria_id=${encodeURIComponent(categoryId)}`);
            const data = await response.json();
            (data.results || []).forEach((item) => {
                const option = document.createElement("option");
                option.value = String(item.id);
                option.textContent = item.nome;
                specialtySelect.appendChild(option);
            });
        }

        function applyCategoryRules() {
            const selectedCategory = categorySelect ? categorySelect.value : "";
            const isStudent = studentCategoryIds.includes(selectedCategory);

            setVisibility(wrapSpecialty, true);
            if (specialtySelect) {
                specialtySelect.removeAttribute("required");
            }

            setVisibility(wrapFase, isStudent);
            if (faseSelect) {
                if (isStudent) {
                    faseSelect.setAttribute("required", "required");
                } else {
                    faseSelect.removeAttribute("required");
                    clearSelect(faseSelect);
                }
            }
        }

        if (categorySelect) {
            categorySelect.addEventListener("change", async () => {
                if (categorySelect.value) {
                    await loadSpecialtiesByCategory(categorySelect.value);
                } else if (specialtySelect) {
                    specialtySelect.innerHTML = '<option value="">---------</option>';
                    clearSelect(specialtySelect);
                }
                applyCategoryRules();
            });
        }

        (async () => {
            if (categorySelect && categorySelect.value) {
                const selectedSpecialty = specialtySelect ? specialtySelect.value : "";
                await loadSpecialtiesByCategory(categorySelect.value);
                if (specialtySelect) {
                    specialtySelect.value = selectedSpecialty;
                }
            }
            applyCategoryRules();
        })();

        const telInput = document.getElementById("id_telefone");
        initTelefoneBrMask(telInput);
        leadForm.addEventListener("submit", (e) => {
            if (!telInput) return;
            refreshTelefoneValidity(telInput);
            if (!telefoneLeadValid(telInput.value)) {
                e.preventDefault();
                telInput.reportValidity();
            }
        });
    }

    function initLocationCascade(form) {
        const est = form.querySelector("#id_estado_local");
        const cid = form.querySelector("#id_cidade_local");
        if (!est || !cid) {
            return;
        }
        const initialCity = cid.value;
        async function loadCities(estadoId, keepCityId) {
            cid.innerHTML = '<option value="">---------</option>';
            if (!estadoId) {
                return;
            }
            const response = await fetch(`/kanban/api/cidades/?estado_id=${encodeURIComponent(estadoId)}`);
            const data = await response.json();
            (data.results || []).forEach((item) => {
                const option = document.createElement("option");
                option.value = String(item.id);
                option.textContent = item.nome;
                cid.appendChild(option);
            });
            if (keepCityId) {
                cid.value = String(keepCityId);
            }
        }
        est.addEventListener("change", () => {
            loadCities(est.value, null);
        });
        if (est.value) {
            loadCities(est.value, initialCity);
        }
    }

    document.querySelectorAll("form").forEach((form) => {
        initLocationCascade(form);
    });

    const kanbanBoard = document.getElementById("kanban-board");
    if (kanbanBoard) {
        /* dataset.* pode falhar em casos raros; getAttribute reflete o HTML gerado pelo Django */
        const previewTemplate =
            kanbanBoard.getAttribute("data-preview-template") || kanbanBoard.dataset.previewTemplate || "";
        const transitionTemplate =
            kanbanBoard.getAttribute("data-transition-template") || kanbanBoard.dataset.transitionTemplate || "";
        const dialog = document.getElementById("kanban-lead-dialog");
        const dialogBody = document.getElementById("kanban-lead-dialog-body");
        const closeX = document.getElementById("kanban-modal-close-x");
        const transitionDialog = document.getElementById("kanban-transition-dialog");
        const transitionForm = document.getElementById("kanban-transition-form");
        const transitionCloseX = document.getElementById("kanban-transition-close-x");
        const trCancel = document.getElementById("tr-cancel");
        const trError = document.getElementById("tr-error");
        const trTitle = document.getElementById("tr-title");
        const trEtapaAnt = document.getElementById("tr-etapa-anterior");
        const trEtapaNova = document.getElementById("tr-etapa-nova");
        const trColab = document.getElementById("tr-colaborador-id");
        const csrfInputPage = document.querySelector('main input[name="csrfmiddlewaretoken"]');
        const csrfInputTransition = transitionForm
            ? transitionForm.querySelector('input[name="csrfmiddlewaretoken"]')
            : null;
        const csrfToken = csrfInputTransition
            ? csrfInputTransition.value
            : csrfInputPage
              ? csrfInputPage.value
              : "";

        const PLACEHOLDER = "888888888";
        let suppressCardClickUntil = 0;

        function urlFromTemplate(tpl, leadId) {
            return tpl.split(PLACEHOLDER).join(String(leadId));
        }

        /** Caminho absoluto no mesmo host (sempre com / inicial no path) para não duplicar segmentos da URL atual. */
        function toAbsoluteRequestUrl(pathOrUrl) {
            const s = String(pathOrUrl || "").trim();
            if (!s) return "";
            if (/^https?:\/\//i.test(s)) return s;
            const path = s.startsWith("/") ? s : `/${s}`;
            try {
                return new URL(path, window.location.origin).href;
            } catch {
                return path.startsWith("/") ? `${window.location.origin}${path}` : s;
            }
        }

        function ensureEmptyHint(zone) {
            if (!zone.querySelector(".kanban-card")) {
                const p = document.createElement("p");
                p.className = "kanban-column-empty";
                p.textContent = "Sem leads nesta etapa.";
                zone.appendChild(p);
            }
        }

        function removeEmptyHint(zone) {
            zone.querySelectorAll(".kanban-column-empty").forEach((el) => el.remove());
        }

        const FORWARD = ["novo", "em_contato", "proposta_enviada", "convertido"];
        const MSG_SKIP =
            "Não é possível avançar para esta etapa. Conclua a etapa anterior primeiro.";

        function clientTransitionAllowed(oldStatus, newStatus) {
            if (oldStatus === newStatus) {
                return { ok: false, message: "O lead já está nesta etapa." };
            }
            if (oldStatus === "perdido") {
                return { ok: false, message: "Este lead já está como perdido." };
            }
            if (newStatus === "perdido") {
                return { ok: true, message: null };
            }
            if (!FORWARD.includes(oldStatus) || !FORWARD.includes(newStatus)) {
                return { ok: false, message: "Transição não permitida." };
            }
            const iOld = FORWARD.indexOf(oldStatus);
            const iNew = FORWARD.indexOf(newStatus);
            if (iNew === iOld + 1) return { ok: true, message: null };
            if (iNew > iOld + 1) return { ok: false, message: MSG_SKIP };
            return { ok: false, message: "Transição não permitida." };
        }

        function transitionSectionId(oldStatus, newStatus) {
            if (newStatus === "perdido") return "tr-sec-perdido";
            if (oldStatus === "novo" && newStatus === "em_contato") return "tr-sec-novo-em_contato";
            if (oldStatus === "em_contato" && newStatus === "proposta_enviada") return "tr-sec-em_contato-proposta";
            if (oldStatus === "proposta_enviada" && newStatus === "convertido") return "tr-sec-proposta-convertido";
            return null;
        }

        function prepareTransitionForm(activeSectionId) {
            document.querySelectorAll(".kanban-tr-section").forEach((sec) => {
                const isAlways = sec.classList.contains("tr-sec-always");
                const isActive = sec.id === activeSectionId;
                const show = isAlways || isActive;
                sec.hidden = !show;
                sec.querySelectorAll("input,select,textarea").forEach((el) => {
                    if (el.name === "csrfmiddlewaretoken") return;
                    el.disabled = !show;
                });
            });
        }

        function resetTransitionForm() {
            if (!transitionForm) return;
            transitionForm.reset();
            if (trError) {
                trError.hidden = true;
                trError.textContent = "";
            }
        }

        let pendingTransition = null;

        function openTransitionModal(card, targetZone, oldStatus, newStatus) {
            if (!transitionDialog || !transitionForm || !trEtapaAnt || !trEtapaNova || !trColab) return;
            const secId = transitionSectionId(oldStatus, newStatus);
            if (!secId) {
                window.alert("Transição não suportada.");
                return;
            }
            pendingTransition = { card, targetZone, oldZone: card.closest("[data-drop-zone]") };
            resetTransitionForm();
            trEtapaAnt.value = oldStatus;
            trEtapaNova.value = newStatus;
            const leadId = card.dataset.leadId;
            const defColab = (card.dataset.colaboradorId || "").trim();
            trColab.value = defColab || "";
            prepareTransitionForm(secId);
            const labels = {
                "tr-sec-perdido": "Registrar perda do lead",
                "tr-sec-novo-em_contato": "Novo → Em contato",
                "tr-sec-em_contato-proposta": "Em contato → Proposta enviada",
                "tr-sec-proposta-convertido": "Proposta enviada → Convertido",
            };
            if (trTitle) trTitle.textContent = labels[secId] || "Registrar transição";
            transitionDialog.showModal();
        }

        function closeTransitionModal() {
            if (transitionDialog) transitionDialog.close();
            pendingTransition = null;
        }

        async function openLeadPreview(leadId) {
            if (!dialog || !dialogBody) return;
            dialogBody.innerHTML = '<p class="text-muted">Carregando…</p>';
            dialog.showModal();

            const path = urlFromTemplate(previewTemplate, leadId);
            if (!previewTemplate || !previewTemplate.includes(PLACEHOLDER) || !path) {
                dialogBody.innerHTML =
                    '<p class="text-muted">URL do preview não configurada. Recarregue a página ou verifique o template do Kanban.</p>';
                return;
            }
            const requestUrl = toAbsoluteRequestUrl(path);

            let res;
            try {
                res = await fetch(requestUrl, {
                    credentials: "same-origin",
                    headers: { Accept: "text/html" },
                    redirect: "follow",
                });
            } catch (err) {
                const hint =
                    err && err.message
                        ? `${err.message}. `
                        : "";
                dialogBody.innerHTML = `<p class="text-muted">${hint}Verifique se o servidor está rodando, se você acessa o CRM pelo mesmo endereço (ex.: não misturar <code>localhost</code> com <code>127.0.0.1</code> com bloqueio de cookies), desative extensões que bloqueiam requisições e abra a aba Rede (F12) ao clicar no card.</p>`;
                return;
            }

            if (!res.ok) {
                dialogBody.innerHTML = `<p class="text-muted">Não foi possível carregar o lead (HTTP ${res.status}).</p>`;
                return;
            }

            try {
                const html = await res.text();
                dialogBody.innerHTML = html;
            } catch (err) {
                const msg = err && err.message ? err.message : "Falha ao ler a resposta.";
                dialogBody.innerHTML = `<p class="text-muted">${msg}</p>`;
            }
        }

        if (closeX && dialog) {
            closeX.addEventListener("click", () => dialog.close());
        }
        if (dialogBody) {
            dialogBody.addEventListener("click", (e) => {
                const btn = e.target.closest("[data-kanban-close]");
                if (btn && dialog) dialog.close();
            });
        }
        if (dialog) {
            dialog.addEventListener("click", (e) => {
                if (e.target === dialog) dialog.close();
            });
        }

        kanbanBoard.querySelectorAll(".kanban-card").forEach((card) => {
            card.addEventListener("click", (e) => {
                if (Date.now() < suppressCardClickUntil) return;
                const id = card.dataset.leadId;
                if (id) openLeadPreview(id);
            });
            card.addEventListener("keydown", (e) => {
                if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    if (Date.now() < suppressCardClickUntil) return;
                    const id = card.dataset.leadId;
                    if (id) openLeadPreview(id);
                }
            });
        });

        let draggedLeadId = null;
        let dragSourceZone = null;

        kanbanBoard.querySelectorAll(".kanban-card").forEach((card) => {
            card.addEventListener("dragstart", (e) => {
                draggedLeadId = card.dataset.leadId;
                dragSourceZone = card.closest("[data-drop-zone]");
                e.dataTransfer.effectAllowed = "move";
                e.dataTransfer.setData("text/plain", draggedLeadId || "");
                card.classList.add("kanban-card-dragging");
            });
            card.addEventListener("dragend", () => {
                card.classList.remove("kanban-card-dragging");
                draggedLeadId = null;
                dragSourceZone = null;
                kanbanBoard.querySelectorAll(".kanban-drop-hover").forEach((z) => z.classList.remove("kanban-drop-hover"));
            });
        });

        kanbanBoard.querySelectorAll("[data-drop-zone]").forEach((zone) => {
            zone.addEventListener("dragover", (e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = "move";
                zone.classList.add("kanban-drop-hover");
            });
            zone.addEventListener("dragleave", () => {
                zone.classList.remove("kanban-drop-hover");
            });
            zone.addEventListener("drop", (e) => {
                e.preventDefault();
                zone.classList.remove("kanban-drop-hover");
                const leadId = e.dataTransfer.getData("text/plain");
                const column = zone.closest(".kanban-column");
                const newStatus = column ? column.dataset.status : null;
                if (!leadId || !newStatus) return;

                const card = kanbanBoard.querySelector(`.kanban-card[data-lead-id="${CSS.escape(leadId)}"]`);
                if (!card) return;
                const oldStatus = card.dataset.status;
                if (oldStatus === newStatus) return;

                const rule = clientTransitionAllowed(oldStatus, newStatus);
                if (!rule.ok) {
                    window.alert(rule.message || "Transição não permitida.");
                    return;
                }
                if (!transitionTemplate || !transitionTemplate.includes(PLACEHOLDER)) {
                    window.alert("URL de transição não configurada.");
                    return;
                }
                openTransitionModal(card, zone, oldStatus, newStatus);
            });
        });

        if (transitionCloseX && transitionDialog) {
            transitionCloseX.addEventListener("click", () => closeTransitionModal());
        }
        if (trCancel && transitionDialog) {
            trCancel.addEventListener("click", () => closeTransitionModal());
        }
        if (transitionDialog) {
            transitionDialog.addEventListener("click", (e) => {
                if (e.target === transitionDialog) closeTransitionModal();
            });
            transitionDialog.addEventListener("close", () => {
                pendingTransition = null;
            });
        }

        if (transitionForm) {
            transitionForm.addEventListener("submit", async (e) => {
                e.preventDefault();
                if (!pendingTransition) return;
                const { card, targetZone, oldZone } = pendingTransition;
                const leadId = card.dataset.leadId;
                if (!leadId || !csrfToken) return;

                if (trError) {
                    trError.hidden = true;
                    trError.textContent = "";
                }

                const fd = new FormData(transitionForm);
                fd.set("csrfmiddlewaretoken", csrfToken);
                fd.set("etapa_anterior", card.dataset.status);

                try {
                    const res = await fetch(toAbsoluteRequestUrl(urlFromTemplate(transitionTemplate, leadId)), {
                        method: "POST",
                        body: fd,
                        headers: { "X-Requested-With": "XMLHttpRequest" },
                        credentials: "same-origin",
                    });
                    let data = null;
                    try {
                        data = await res.json();
                    } catch {
                        data = null;
                    }
                    if (!res.ok) {
                        const msg =
                            data && data.message
                                ? data.message
                                : `Não foi possível concluir (${res.status}).`;
                        if (trError) {
                            trError.textContent = msg;
                            trError.hidden = false;
                        } else {
                            window.alert(msg);
                        }
                        return;
                    }
                    if (!data || !data.ok) {
                        const msg = (data && data.message) || "Resposta inválida.";
                        if (trError) {
                            trError.textContent = msg;
                            trError.hidden = false;
                        } else {
                            window.alert(msg);
                        }
                        return;
                    }
                    const newStatus = data.status;
                    suppressCardClickUntil = Date.now() + 500;
                    removeEmptyHint(targetZone);
                    targetZone.appendChild(card);
                    card.dataset.status = newStatus;
                    if (oldZone) ensureEmptyHint(oldZone);
                    closeTransitionModal();
                    resetTransitionForm();
                } catch {
                    window.alert("Erro de rede ao registrar a transição.");
                }
            });
        }
    }

    initKanbanFilterDropdowns();
});

function initKanbanFilterDropdowns() {
    const form = document.getElementById("kanban-filters-form");
    if (!form) return;

    function closeAllMsPanels() {
        form.querySelectorAll(".kanban-ms-panel").forEach((p) => {
            p.hidden = true;
            const w = p.closest("[data-kanban-ms]");
            const tr = w?.querySelector(".kanban-ms-trigger");
            if (tr) tr.setAttribute("aria-expanded", "false");
        });
    }

    form.querySelectorAll("[data-kanban-ms]").forEach((wrap) => {
        const trigger = wrap.querySelector(".kanban-ms-trigger");
        const panel = wrap.querySelector(".kanban-ms-panel");
        const search = wrap.querySelector(".kanban-ms-search");
        const list = wrap.querySelector(".kanban-ms-list");
        const textEl = wrap.querySelector(".kanban-ms-trigger-text");
        const emptyLabel = wrap.dataset.msEmptyLabel || "Todos";
        if (!trigger || !panel || !search || !list || !textEl) return;

        const cbs = () => [...list.querySelectorAll('input[type="checkbox"]')];
        const items = () => [...list.querySelectorAll(".kanban-ms-item")];

        function syncTrigger() {
            const total = cbs().length;
            const n = cbs().filter((c) => c.checked).length;
            if (n === 0) textEl.textContent = emptyLabel;
            else if (total > 0 && n === total) textEl.textContent = `${emptyLabel} (${n})`;
            else if (n === 1) textEl.textContent = "1 selecionado";
            else textEl.textContent = `${n} selecionados`;
        }

        trigger.addEventListener("click", (e) => {
            e.stopPropagation();
            const opening = panel.hidden;
            form.querySelectorAll(".kanban-ms-panel").forEach((p) => {
                if (p !== panel) {
                    p.hidden = true;
                    const t = p.closest("[data-kanban-ms]")?.querySelector(".kanban-ms-trigger");
                    if (t) t.setAttribute("aria-expanded", "false");
                }
            });
            if (opening) {
                panel.hidden = false;
                trigger.setAttribute("aria-expanded", "true");
                search.focus();
            } else {
                panel.hidden = true;
                trigger.setAttribute("aria-expanded", "false");
            }
        });

        panel.addEventListener("click", (e) => e.stopPropagation());

        search.addEventListener("keydown", (e) => {
            if (e.key === "Enter") e.preventDefault();
        });

        search.addEventListener("input", () => {
            const q = search.value.trim().toLowerCase();
            items().forEach((item) => {
                const hay = (item.getAttribute("data-search") || item.textContent || "").toLowerCase();
                item.style.display = !q || hay.includes(q) ? "" : "none";
            });
        });

        const allBtn = wrap.querySelector("[data-ms-all]");
        const clearBtn = wrap.querySelector("[data-ms-clear]");
        if (allBtn) {
            allBtn.addEventListener("click", (e) => {
                e.preventDefault();
                search.value = "";
                items().forEach((item) => {
                    item.style.display = "";
                    const c = item.querySelector('input[type="checkbox"]');
                    if (c) c.checked = true;
                });
                syncTrigger();
            });
        }
        if (clearBtn) {
            clearBtn.addEventListener("click", (e) => {
                e.preventDefault();
                search.value = "";
                items().forEach((item) => {
                    item.style.display = "";
                    const c = item.querySelector('input[type="checkbox"]');
                    if (c) c.checked = false;
                });
                syncTrigger();
            });
        }

        list.addEventListener("change", () => syncTrigger());

        syncTrigger();
    });

    document.addEventListener("click", (e) => {
        if (!e.target.closest("#kanban-filters-form [data-kanban-ms]")) {
            closeAllMsPanels();
        }
    });

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && form.contains(document.activeElement)) {
            closeAllMsPanels();
        }
    });
}
