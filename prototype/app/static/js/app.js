/* Dashboard de Retencion de Clientes - logica de frontend (vanilla JS) */
(() => {
  "use strict";

  const state = {
    pagina: 1,
    tamanoPagina: 10,
    totalPaginas: 1,
    ofertaSeleccionada: null,
    clienteModalActual: null,
    catalogoOfertas: [],
  };

  const el = (id) => document.getElementById(id);

  // ---------------------------------------------------------------- utils
  function debounce(fn, ms) {
    let t;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), ms);
    };
  }

  function mostrarToast(mensaje) {
    const toast = el("toast");
    toast.textContent = mensaje;
    toast.classList.add("is-visible");
    setTimeout(() => toast.classList.remove("is-visible"), 3500);
  }

  async function apiFetch(url, opciones) {
    const resp = await fetch(url, opciones);
    if (!resp.ok) {
      let detalle = resp.statusText;
      try {
        const data = await resp.json();
        detalle = data.detail || detalle;
      } catch (_) { /* respuesta sin cuerpo JSON */ }
      throw new Error(detalle);
    }
    if (resp.status === 204) return null;
    return resp.json();
  }

  function formatearMoneda(valor) {
    return new Intl.NumberFormat("es-CO", { maximumFractionDigits: 0 }).format(valor);
  }

  function formatearFecha(iso) {
    if (!iso) return "-";
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleString("es-CO", { dateStyle: "medium", timeStyle: "short" });
  }

  // ---------------------------------------------------------------- tabs
  function initTabs() {
    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("is-active"));
        document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("is-active"));
        btn.classList.add("is-active");
        el(`tab-${btn.dataset.tab}`).classList.add("is-active");
        if (btn.dataset.tab === "seguimiento") cargarOfertasEnviadas();
      });
    });
  }

  // ---------------------------------------------------------------- filtros / selects
  async function cargarOpcionesFiltros() {
    const opciones = await apiFetch("/api/clientes/filtros");
    const mapa = {
      "f-genero": opciones.gender,
      "f-education": opciones.education_level,
      "f-marital": opciones.marital_status,
      "f-income": opciones.income_category,
      "f-card": opciones.card_category,
      "f-attrition": opciones.attrition_flag,
    };
    for (const [id, valores] of Object.entries(mapa)) {
      const select = el(id);
      valores.forEach((v) => {
        const opt = document.createElement("option");
        opt.value = v;
        opt.textContent = v;
        select.appendChild(opt);
      });
    }
  }

  function leerFiltros() {
    const params = new URLSearchParams();

    if (el("filtro-solo-riesgo").checked) {
      params.set("riesgo_min", "50");
    }
    if (el("f-buscar").value.trim()) params.set("buscar_clientnum", el("f-buscar").value.trim());
    if (el("f-nivel").value) params.set("nivel_riesgo", el("f-nivel").value);
    if (el("f-genero").value) params.set("genero", el("f-genero").value);
    if (el("f-education").value) params.set("education_level", el("f-education").value);
    if (el("f-marital").value) params.set("marital_status", el("f-marital").value);
    if (el("f-income").value) params.set("income_category", el("f-income").value);
    if (el("f-card").value) params.set("card_category", el("f-card").value);
    if (el("f-attrition").value) params.set("attrition_flag", el("f-attrition").value);
    if (el("f-oferta").value) params.set("oferta_enviada", el("f-oferta").value);

    const [ordenarPor, orden] = el("f-orden").value.split(":");
    params.set("ordenar_por", ordenarPor);
    params.set("orden", orden);

    params.set("pagina", String(state.pagina));
    params.set("tamano_pagina", String(state.tamanoPagina));
    return params;
  }

  function limpiarFiltros() {
    el("filtro-solo-riesgo").checked = false;
    el("f-buscar").value = "";
    ["f-nivel", "f-genero", "f-education", "f-marital", "f-income", "f-card", "f-attrition", "f-oferta"]
      .forEach((id) => (el(id).value = ""));
    el("f-orden").value = "probabilidad_cancelacion:desc";
    state.pagina = 1;
    cargarClientes();
  }

  // ---------------------------------------------------------------- render tabla clientes
  function badgeRiesgo(cliente) {
    return `<span class="risk-badge nivel-${cliente.nivel_riesgo_slug}">
      <span class="dot"></span>${cliente.probabilidad_cancelacion.toFixed(1)}% &middot; ${cliente.nivel_riesgo}
    </span>`;
  }

  function badgeEstadoCliente(cliente) {
    const activo = cliente.Attrition_Flag === "Existing Customer";
    return `<span class="status-badge ${activo ? "status-existing" : "status-attrited"}">
      ${activo ? "Activo" : "Cancelado"}
    </span>`;
  }

  function badgeSeguimiento(cliente) {
    if (!cliente.oferta_enviada) {
      return `<span class="tracking-badge tracking-none">Sin contactar</span>`;
    }
    return `<span class="tracking-badge tracking-enviada">Oferta enviada</span>`;
  }

  function renderClientesTabla(data) {
    const tbody = el("clientes-tbody");
    if (!data.clientes.length) {
      tbody.innerHTML = `<tr><td colspan="10" class="empty-state">No hay clientes que coincidan con los filtros.</td></tr>`;
      renderPaginacion(data);
      return;
    }

    tbody.innerHTML = data.clientes.map((c) => `
      <tr>
        <td>
          <div class="client-id">${c.nombre_display}</div>
          <div class="client-sub">${c.correo_demo}</div>
        </td>
        <td>${badgeRiesgo(c)}</td>
        <td>${c.Customer_Age}</td>
        <td>${c.Gender}</td>
        <td>${c.Education_Level}</td>
        <td>${c.Income_Category}</td>
        <td>${c.Card_Category}</td>
        <td>${badgeEstadoCliente(c)}</td>
        <td>${badgeSeguimiento(c)}</td>
        <td><button class="btn btn-primary btn-sm" data-clientnum="${c.CLIENTNUM}">
          ${c.oferta_enviada ? "Reenviar oferta" : "Enviar oferta"}
        </button></td>
      </tr>
    `).join("");

    tbody.querySelectorAll("button[data-clientnum]").forEach((btn) => {
      btn.addEventListener("click", () => abrirModalOferta(Number(btn.dataset.clientnum)));
    });

    renderPaginacion(data);
  }

  function renderPaginacion(data) {
    state.totalPaginas = data.total_paginas;
    const cont = el("pagination");
    if (data.total_paginas <= 1) {
      cont.innerHTML = `<span>${data.total} cliente(s)</span>`;
      return;
    }
    let html = `<button id="pg-prev" ${data.pagina <= 1 ? "disabled" : ""}>&laquo; Anterior</button>`;
    html += `<span>Pagina ${data.pagina} de ${data.total_paginas} &middot; ${data.total} cliente(s)</span>`;
    html += `<button id="pg-next" ${data.pagina >= data.total_paginas ? "disabled" : ""}>Siguiente &raquo;</button>`;
    cont.innerHTML = html;

    el("pg-prev")?.addEventListener("click", () => { state.pagina -= 1; cargarClientes(); });
    el("pg-next")?.addEventListener("click", () => { state.pagina += 1; cargarClientes(); });
  }

  async function cargarClientes() {
    const params = leerFiltros();
    const data = await apiFetch(`/api/clientes?${params.toString()}`);
    renderClientesTabla(data);
  }

  // ---------------------------------------------------------------- dashboard KPIs
  async function cargarResumen() {
    const resumen = await apiFetch("/api/dashboard/resumen");
    el("kpi-total").textContent = formatearMoneda(resumen.total_clientes);
    el("kpi-riesgo").textContent = `${formatearMoneda(resumen.total_en_riesgo)} (${resumen.porcentaje_en_riesgo}%)`;
    el("kpi-promedio").textContent = `${resumen.probabilidad_promedio}%`;
    el("kpi-pendientes").textContent = formatearMoneda(resumen.clientes_pendientes_contacto);

    const dist = resumen.distribucion_riesgo;
    const max = Math.max(dist.bajo, dist.moderado, dist.alto, dist.critico, 1);
    for (const nivel of ["bajo", "moderado", "alto", "critico"]) {
      const pct = Math.max(6, Math.round((dist[nivel] / max) * 100));
      document.querySelector(`.risk-bar-item[data-nivel="${nivel}"] .risk-bar-fill`).style.height = `${pct}%`;
      el(`count-${nivel}`).textContent = dist[nivel];
    }
  }

  // ---------------------------------------------------------------- modal enviar oferta
  async function abrirModalOferta(clientnum) {
    const cliente = await apiFetch(`/api/clientes/${clientnum}`);
    state.clienteModalActual = cliente;
    state.ofertaSeleccionada = null;

    el("modal-client-info").innerHTML =
      `<strong>${cliente.nombre_display}</strong> &middot; riesgo de cancelacion
       <strong>${cliente.probabilidad_cancelacion.toFixed(1)}%</strong> (${cliente.nivel_riesgo}) &middot;
       tarjeta ${cliente.Card_Category}`;

    if (!state.catalogoOfertas.length) {
      state.catalogoOfertas = await apiFetch("/api/ofertas/catalogo");
    }

    el("offers-grid").innerHTML = state.catalogoOfertas.map((o) => `
      <div class="offer-card" data-oferta="${o.id}">
        <h4>${o.nombre}</h4>
        <p>${o.descripcion}</p>
        <span class="offer-benefit">${o.beneficio}</span>
      </div>
    `).join("");

    el("offers-grid").querySelectorAll(".offer-card").forEach((card) => {
      card.addEventListener("click", () => {
        el("offers-grid").querySelectorAll(".offer-card").forEach((c) => c.classList.remove("is-selected"));
        card.classList.add("is-selected");
        state.ofertaSeleccionada = card.dataset.oferta;
        el("modal-confirm").disabled = false;
      });
    });

    el("email-preview").hidden = true;
    el("modal-confirm").disabled = true;
    el("modal-confirm").textContent = "Simular envio";
    el("modal-backdrop").classList.add("is-open");
  }

  function cerrarModal() {
    el("modal-backdrop").classList.remove("is-open");
  }

  async function confirmarEnvioOferta() {
    if (!state.ofertaSeleccionada || !state.clienteModalActual) return;
    const boton = el("modal-confirm");
    boton.disabled = true;
    boton.textContent = "Enviando...";

    try {
      const resultado = await apiFetch("/api/ofertas/enviar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          clientnum: state.clienteModalActual.CLIENTNUM,
          oferta_id: state.ofertaSeleccionada,
        }),
      });

      const correo = resultado.correo_simulado;
      el("email-preview").hidden = false;
      el("email-preview").innerHTML = `
        <span class="email-badge">Correo simulado enviado</span>
        <div class="email-row"><strong>Para:</strong> ${correo.para}</div>
        <div class="email-row"><strong>Asunto:</strong> ${correo.asunto}</div>
        <pre>${correo.cuerpo}</pre>
      `;
      boton.textContent = "Enviado";
      mostrarToast(`Oferta enviada (simulada) a ${state.clienteModalActual.nombre_display}`);

      await Promise.all([cargarClientes(), cargarResumen()]);
    } catch (err) {
      mostrarToast(`Error al enviar la oferta: ${err.message}`);
      boton.disabled = false;
      boton.textContent = "Simular envio";
    }
  }

  // ---------------------------------------------------------------- seguimiento
  function badgeEstadoSeguimiento(estado) {
    return `<span class="tracking-badge tracking-${estado}">${estado.replace("_", " ")}</span>`;
  }

  async function cargarOfertasEnviadas() {
    const estado = el("s-estado").value;
    const params = new URLSearchParams();
    if (estado) params.set("estado_seguimiento", estado);

    const ofertas = await apiFetch(`/api/ofertas/enviadas?${params.toString()}`);
    const tbody = el("ofertas-tbody");

    if (!ofertas.length) {
      tbody.innerHTML = `<tr><td colspan="6" class="empty-state">Aun no se han enviado ofertas.</td></tr>`;
      return;
    }

    const estados = ["enviada", "contactado", "aceptada", "rechazada", "sin_respuesta"];

    tbody.innerHTML = ofertas.map((o) => `
      <tr>
        <td>Cliente #${o.clientnum}</td>
        <td>${o.oferta_nombre}</td>
        <td>${o.correo_destino}</td>
        <td>${formatearFecha(o.fecha_envio)}</td>
        <td>${badgeEstadoSeguimiento(o.estado_seguimiento)}</td>
        <td>
          <select class="tracking-select" data-id="${o.id}">
            ${estados.map((e) => `<option value="${e}" ${e === o.estado_seguimiento ? "selected" : ""}>${e.replace("_", " ")}</option>`).join("")}
          </select>
        </td>
      </tr>
    `).join("");

    tbody.querySelectorAll(".tracking-select").forEach((select) => {
      select.addEventListener("change", async () => {
        try {
          await apiFetch(`/api/ofertas/enviadas/${select.dataset.id}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ estado_seguimiento: select.value }),
          });
          mostrarToast("Seguimiento actualizado");
          cargarOfertasEnviadas();
        } catch (err) {
          mostrarToast(`No se pudo actualizar: ${err.message}`);
        }
      });
    });
  }

  // ---------------------------------------------------------------- listeners
  function initFiltros() {
    el("filtro-solo-riesgo").addEventListener("change", () => { state.pagina = 1; cargarClientes(); });
    el("f-buscar").addEventListener("input", debounce(() => { state.pagina = 1; cargarClientes(); }, 350));
    ["f-nivel", "f-genero", "f-education", "f-marital", "f-income", "f-card", "f-attrition", "f-oferta", "f-orden"]
      .forEach((id) => el(id).addEventListener("change", () => { state.pagina = 1; cargarClientes(); }));
    el("f-limpiar").addEventListener("click", limpiarFiltros);
  }

  function initModal() {
    el("modal-close").addEventListener("click", cerrarModal);
    el("modal-cancel").addEventListener("click", cerrarModal);
    el("modal-backdrop").addEventListener("click", (e) => { if (e.target.id === "modal-backdrop") cerrarModal(); });
    el("modal-confirm").addEventListener("click", confirmarEnvioOferta);
  }

  function initSeguimiento() {
    el("s-estado").addEventListener("change", cargarOfertasEnviadas);
  }

  // ---------------------------------------------------------------- boot
  async function init() {
    initTabs();
    initFiltros();
    initModal();
    initSeguimiento();

    await Promise.all([cargarOpcionesFiltros(), cargarResumen(), cargarClientes()]);
  }

  document.addEventListener("DOMContentLoaded", init);
})();
