(() => {
  "use strict";

  const STORAGE_KEY = "fmp-tagger-v1";
  const CSV_COLS = ["Name", "Position", "Duration", "Data", "Evento", "Portiere", "Squadra", "Chi", "Dove", "Lato", "Esito"];

  const DEFAULT_PLAYERS = [
    "azza", "deba", "diego jr", "digao", "erick", "fabri",
    "mattia", "nic", "nico estratti", "ricky", "scanta", "zanna",
  ];
  const DEFAULT_KEEPERS = ["bara", "gio"];

  const EVENT_DEFS = [
    { id: "Tiro", shortcut: "z", color: "orange", group: "Azioni", preroll: 8, duration: 13 },
    { id: "Gol", shortcut: "g", color: "green", group: "Azioni", preroll: 16, duration: 25 },
    { id: "Assist", shortcut: "", color: "green", group: "Azioni", preroll: 7, duration: 5 },
    { id: "Autogol", shortcut: "", color: "red", group: "Azioni", preroll: 9, duration: 13 },
    { id: "Palla recuperata", shortcut: "r", color: "teal", group: "Possesso", preroll: 9, duration: 15 },
    { id: "Palla persa", shortcut: "e", color: "red", group: "Possesso", preroll: 9, duration: 15 },
    { id: "Passaggio sbagliato", shortcut: "", color: "red", group: "Possesso", preroll: 6, duration: 12 },
    { id: "Fallo", shortcut: "", color: "yellow", group: "Falli", preroll: 8, duration: 10 },
    { id: "Ammonizione", shortcut: "", color: "yellow", group: "Falli", preroll: 8, duration: 12 },
    { id: "Espulsione", shortcut: "", color: "red", group: "Falli", preroll: 5, duration: 10 },
    { id: "Laterale", shortcut: "l", color: "blue", group: "Palle inattive", preroll: 5, duration: 12 },
    { id: "Angolo", shortcut: "a", color: "blue", group: "Palle inattive", preroll: 4, duration: 12 },
    { id: "Punizione", shortcut: "p", color: "blue", group: "Palle inattive", preroll: 5, duration: 13 },
    { id: "Tiro libero", shortcut: "", color: "blue", group: "Palle inattive", preroll: 5, duration: 11 },
    { id: "Rigore", shortcut: "", color: "blue", group: "Palle inattive", preroll: 9, duration: 14 },
    { id: "Ripartenza", shortcut: "w", color: "purple", group: "Situazioni", preroll: 9, duration: 15 },
    { id: "5v4", shortcut: "q", color: "purple", group: "Situazioni", preroll: 5, duration: 10 },
    { id: "4v3", shortcut: "", color: "purple", group: "Situazioni", preroll: 5, duration: 10 },
    { id: "Timeout", shortcut: "t", color: "gray", group: "Situazioni", preroll: 5, duration: 10 },
    { id: "Da rivedere", shortcut: "v", color: "yellow", group: "Situazioni", preroll: 13, duration: 15 },
    { id: "Inizio", shortcut: "b", color: "gray", group: "Tempo", preroll: 5, duration: 10 },
    { id: "Fine primo tempo", shortcut: "", color: "gray", group: "Tempo", preroll: 5, duration: 10 },
    { id: "Inizio secondo tempo", shortcut: "", color: "gray", group: "Tempo", preroll: 5, duration: 10 },
    { id: "Fine partita", shortcut: "", color: "gray", group: "Tempo", preroll: 5, duration: 10 },
  ];
  const SHORTCUTS_VERSION = 2;
  const CLIP_TIMING_VERSION = 1;

  function defaultMap(field) {
    return Object.fromEntries(EVENT_DEFS.map((e) => [e.id, e[field]]));
  }

  const ESITI_BY_EVENT = {
    Tiro: ["Parata", "Gol", "Palo", "Fuori", "Ribattuto", "Assist"],
    Punizione: ["Parata", "Gol", "Palo", "Fuori", "Ribattuto"],
    "Tiro libero": ["Parata", "Gol", "Palo", "Fuori", "Ribattuto"],
    Rigore: ["Parata", "Gol", "Palo", "Fuori", "Ribattuto"],
    Gol: ["Costruzione", "Transizione", "Palla inattiva", "Errore"],
    Autogol: ["Costruzione", "Transizione", "Palla inattiva", "Errore"],
    "Palla persa": ["Ripartenza", "Costruzione", "Fuori"],
    "Palla recuperata": ["Ripartenza", "Costruzione", "Fuori"],
    Ripartenza: ["3v2", "2v2", "2v1", "1v1"],
    Fallo: ["Ammonizione", "Espulsione"],
  };

  const GLOBAL_SHORTCUTS = [
    ["Spazio", "Play / pausa video"],
    ["← / →", "−1s / +1s"],
    ["Shift+← / Shift+→", "−5s / +5s"],
    ["Shift+I / Shift+O", "In / Out dell'evento"],
    ["Invio", "Play clip evento"],
    ["Canc", "Elimina selezionati"],
    ["Ctrl+Z", "Annulla"],
    ["Ctrl+E", "Esporta CSV"],
    ["↑ / ↓", "Evento precedente / successivo"],
    ["X / C", "Squadra Noi / Loro"],
    ["1 / 2 / 3", "Zona 1 / 2 / 3"],
    ["?", "Questa guida"],
  ];

  const ZONE_DEFS = [
    { key: "1", label: "Zona 1" },
    { key: "2", label: "Zona 2" },
    { key: "3", label: "Zona 3" },
  ];

  const $ = (id) => document.getElementById(id);

  const state = {
    mode: "live",
    events: [],
    selected: [],
    lastCreated: null,
    matchName: "",
    matchDate: todayInput(),
    players: [...DEFAULT_PLAYERS],
    keepers: [...DEFAULT_KEEPERS],
    shortcuts: Object.fromEntries(EVENT_DEFS.map((e) => [e.id, e.shortcut])),
    prerolls: defaultMap("preroll"),
    durations: defaultMap("duration"),
    durationSec: 5,
    delaySec: 0,
    prerollSec: 2,
    stickyKeeper: "bara",
    syncOpen: false,
    live: { running: false, startedAt: 0, accumulated: 0 },
    videoKind: null,
    videoUrl: null,
    ytPlayer: null,
    ytReady: false,
    undo: [],
    flashId: null,
    playlist: null,
    saveTimer: null,
  };

  function todayInput() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }

  function dateCsv(iso) {
    if (!iso) return "";
    const [y, m, d] = iso.split("-");
    return d && m && y ? `${d}/${m}/${y}` : iso;
  }

  function dateIso(csv) {
    const m = String(csv || "").trim().match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
    if (!m) return csv || todayInput();
    return `${m[3]}-${m[2].padStart(2, "0")}-${m[1].padStart(2, "0")}`;
  }

  function uid() {
    return "e" + Math.random().toString(36).slice(2, 9) + Date.now().toString(36).slice(-4);
  }

  function pad2(n) { return String(n).padStart(2, "0"); }

  function formatTime(sec) {
    if (!Number.isFinite(sec) || sec < 0) sec = 0;
    const csTotal = Math.round(sec * 100);
    const h = Math.floor(csTotal / 360000);
    const m = Math.floor((csTotal % 360000) / 6000);
    const s = Math.floor((csTotal % 6000) / 100);
    const cs = csTotal % 100;
    return `${h}:${pad2(m)}:${pad2(s)}.${pad2(cs)}`;
  }

  function parseTime(str) {
    const t = String(str || "").trim();
    if (!t) return 0;
    const parts = t.split(":");
    if (parts.length === 3) return (+parts[0] || 0) * 3600 + (+parts[1] || 0) * 60 + parseFloat(parts[2] || "0");
    if (parts.length === 2) return (+parts[0] || 0) * 60 + parseFloat(parts[1] || "0");
    return parseFloat(t) || 0;
  }

  function clampTime(sec) { return Math.max(0, sec); }

  function prerollFor(evento) {
    const v = Number(state.prerolls[evento]);
    if (Number.isFinite(v)) return Math.max(0, v);
    const def = EVENT_DEFS.find((d) => d.id === evento);
    if (def && Number.isFinite(def.preroll)) return def.preroll;
    return Math.max(0, Number(state.prerollSec) || 0);
  }

  function durationFor(evento) {
    const v = Number(state.durations[evento]);
    if (Number.isFinite(v) && v > 0) return v;
    const def = EVENT_DEFS.find((d) => d.id === evento);
    if (def && Number.isFinite(def.duration) && def.duration > 0) return def.duration;
    return Number(state.durationSec) || 5;
  }

  function clipStart(ev) {
    return Math.max(0, parseTime(ev.Position) - prerollFor(ev.Evento));
  }

  function nowSeconds() {
    const raw = state.mode === "video" && hasMedia() ? getMediaTime() : liveSeconds();
    return clampTime(raw - (Number(state.delaySec) || 0));
  }

  function liveSeconds() {
    let ms = state.live.accumulated;
    if (state.live.running) ms += Date.now() - state.live.startedAt;
    return ms / 1000;
  }

  function hasMedia() {
    if (state.videoKind === "file") {
      const v = $("video");
      return v && v.duration && Number.isFinite(v.duration);
    }
    if (state.videoKind === "youtube") return !!(state.ytPlayer && state.ytReady);
    return false;
  }

  function getMediaTime() {
    if (state.videoKind === "file") return $("video").currentTime || 0;
    if (state.videoKind === "youtube" && state.ytPlayer) {
      try { return state.ytPlayer.getCurrentTime() || 0; } catch { return 0; }
    }
    return 0;
  }

  function getMediaDuration() {
    if (state.videoKind === "file") return $("video").duration || 0;
    if (state.videoKind === "youtube" && state.ytPlayer) {
      try { return state.ytPlayer.getDuration() || 0; } catch { return 0; }
    }
    return 0;
  }

  function isMediaPlaying() {
    if (state.videoKind === "file") return !$("video").paused;
    if (state.videoKind === "youtube" && state.ytPlayer) {
      try { return state.ytPlayer.getPlayerState() === 1; } catch { return false; }
    }
    return false;
  }

  function mediaPlay() {
    if (state.videoKind === "file") $("video").play();
    else if (state.ytPlayer) state.ytPlayer.playVideo();
  }

  function mediaPause() {
    if (state.videoKind === "file") $("video").pause();
    else if (state.ytPlayer) state.ytPlayer.pauseVideo();
  }

  function mediaSeek(t) {
    t = clampTime(t);
    if (state.videoKind === "file") $("video").currentTime = t;
    else if (state.ytPlayer) state.ytPlayer.seekTo(t, true);
  }

  function mediaRate(r) {
    if (state.videoKind === "file") $("video").playbackRate = r;
    else if (state.ytPlayer && state.ytPlayer.setPlaybackRate) state.ytPlayer.setPlaybackRate(r);
  }

  function pushUndo() {
    state.undo.push(JSON.parse(JSON.stringify(state.events)));
    if (state.undo.length > 60) state.undo.shift();
  }

  function undo() {
    if (!state.undo.length) { toast("Niente da annullare"); return; }
    state.events = state.undo.pop();
    state.selected = state.selected.filter((id) => state.events.some((e) => e.id === id));
    persist(); renderAll(); toast("Annullato");
  }

  function persist() {
    clearTimeout(state.saveTimer);
    state.saveTimer = setTimeout(() => {
      const dump = {
        mode: state.mode,
        events: state.events,
        matchName: state.matchName,
        matchDate: state.matchDate,
        players: state.players,
        keepers: state.keepers,
        shortcuts: state.shortcuts,
        shortcutsVersion: SHORTCUTS_VERSION,
        prerolls: state.prerolls,
        durations: state.durations,
        clipTimingVersion: CLIP_TIMING_VERSION,
        durationSec: state.durationSec,
        delaySec: state.delaySec,
        prerollSec: state.prerollSec,
        stickyKeeper: state.stickyKeeper,
        syncOpen: state.syncOpen,
        liveAccumulated: state.live.running
          ? state.live.accumulated + (Date.now() - state.live.startedAt)
          : state.live.accumulated,
      };
      try { localStorage.setItem(STORAGE_KEY, JSON.stringify(dump)); } catch {}
    }, 200);
  }

  function restore() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const dump = JSON.parse(raw);
      Object.assign(state, {
        mode: dump.mode || "live",
        events: (dump.events || []).map((e) => ({ ...e, id: e.id || uid() })),
        matchName: dump.matchName || "",
        matchDate: dump.matchDate || todayInput(),
        players: dump.players || DEFAULT_PLAYERS,
        keepers: dump.keepers || DEFAULT_KEEPERS,
        shortcuts: dump.shortcutsVersion === SHORTCUTS_VERSION
          ? { ...state.shortcuts, ...(dump.shortcuts || {}) }
          : Object.fromEntries(EVENT_DEFS.map((e) => [e.id, e.shortcut])),
        prerolls: dump.clipTimingVersion === CLIP_TIMING_VERSION
          ? { ...defaultMap("preroll"), ...(dump.prerolls || {}) }
          : defaultMap("preroll"),
        durations: dump.clipTimingVersion === CLIP_TIMING_VERSION
          ? { ...defaultMap("duration"), ...(dump.durations || {}) }
          : defaultMap("duration"),
        durationSec: dump.durationSec ?? 5,
        delaySec: dump.delaySec ?? 0,
        prerollSec: dump.prerollSec ?? 2,
        stickyKeeper: dump.stickyKeeper || "",
        syncOpen: !!dump.syncOpen,
      });
      state.live.accumulated = dump.liveAccumulated || 0;
    } catch {}
  }

  function toast(msg) {
    const host = $("toast");
    const el = document.createElement("div");
    el.className = "toast";
    el.textContent = msg;
    host.appendChild(el);
    setTimeout(() => el.remove(), 2200);
  }

  function sortedEvents() {
    return [...state.events].sort((a, b) => parseTime(a.Position) - parseTime(b.Position) || String(a.id).localeCompare(String(b.id)));
  }

  function selectedEvents() {
    const set = new Set(state.selected);
    return sortedEvents().filter((e) => set.has(e.id));
  }

  function primaryEvent() {
    if (!state.selected.length) return null;
    return state.events.find((e) => e.id === state.selected[state.selected.length - 1]) || null;
  }

  function createEvent(evento) {
    if (state.mode === "live" && !state.live.running && !state.live.accumulated && !state.events.length) {
      startClock();
    }
    pushUndo();
    const row = {
      id: uid(),
      Name: evento,
      Position: formatTime(nowSeconds()),
      Duration: formatTime(durationFor(evento)),
      Data: dateCsv(state.matchDate),
      Evento: evento,
      Portiere: state.stickyKeeper || "",
      Squadra: (evento === "Palla persa" || evento === "Palla recuperata") ? "" : "",
      Chi: "",
      Dove: "",
      Lato: "",
      Esito: "",
    };
    state.events.push(row);
    state.selected = [row.id];
    state.lastCreated = row.id;
    state.flashId = row.id;
    persist();
    renderAll();
    toast(`${evento}  ${row.Position}`);
    scrollToEvent(row.id);
    if (evento === "Fine primo tempo") {
      pauseClock();
      exportCsv("primo-tempo");
    } else if (evento === "Fine partita") {
      pauseClock();
      exportCsv("finale");
    }
  }

  function applyKeyword(col, value) {
    const targets = selectedEvents();
    if (!targets.length) {
      toast("Crea prima un evento (tasto o pannello)");
      return;
    }
    pushUndo();
    for (const e of targets) {
      e[col] = e[col] === value ? "" : value;
      if (col === "Evento") e.Name = e.Evento;
      if (col === "Portiere" && e.Portiere) state.stickyKeeper = e.Portiere;
    }
    persist();
    renderAll();
  }

  function deleteSelected() {
    if (!state.selected.length) return;
    pushUndo();
    const ids = new Set(state.selected);
    state.events = state.events.filter((e) => !ids.has(e.id));
    state.selected = [];
    persist();
    renderAll();
    toast("Eliminati");
  }

  function duplicateSelected() {
    const src = selectedEvents();
    if (!src.length) return;
    pushUndo();
    const created = [];
    for (const e of src) {
      const copy = { ...e, id: uid() };
      created.push(copy.id);
      state.events.push(copy);
    }
    state.selected = created;
    persist();
    renderAll();
  }

  function shiftEvents(list, delta) {
    pushUndo();
    for (const e of list) {
      e.Position = formatTime(clampTime(parseTime(e.Position) + delta));
    }
    persist();
    renderAll();
    toast(`Spostati ${list.length} eventi di ${delta > 0 ? "+" : ""}${delta.toFixed(2)}s`);
  }

  function syncSelected(fromHere) {
    if (state.mode !== "video" || !hasMedia()) {
      toast("Carica un video e passa in modalità Video");
      return;
    }
    const ev = primaryEvent();
    if (!ev) { toast("Seleziona l'evento ancora"); return; }
    const offset = getMediaTime() - parseTime(ev.Position);
    let list = sortedEvents();
    if (fromHere) {
      const t0 = parseTime(ev.Position);
      list = list.filter((e) => parseTime(e.Position) >= t0 - 0.0001);
    }
    shiftEvents(list, offset);
    toast(`Offset ${offset >= 0 ? "+" : ""}${offset.toFixed(2)}s`);
  }

  function setInOut(which) {
    if (state.mode !== "video" || !hasMedia()) { toast("Serve il video"); return; }
    const ev = primaryEvent();
    if (!ev) { toast("Seleziona un evento"); return; }
    pushUndo();
    const t = getMediaTime();
    if (which === "in") {
      const out = parseTime(ev.Position) + parseTime(ev.Duration);
      ev.Position = formatTime(t);
      ev.Duration = formatTime(Math.max(0.2, out - t));
    } else {
      const start = parseTime(ev.Position);
      ev.Duration = formatTime(Math.max(0.2, t - start));
    }
    persist();
    renderAll();
  }

  function playClip(ev) {
    if (!ev || !hasMedia()) return;
    const start = clipStart(ev);
    const end = parseTime(ev.Position) + parseTime(ev.Duration || formatTime(durationFor(ev.Evento)));
    mediaSeek(start);
    mediaPlay();
    state.playlist = { queue: [], end };
  }

  function playFiltered() {
    const list = filteredEvents();
    if (!list.length || !hasMedia()) return;
    const queue = list.map((e) => e.id);
    const first = list[0];
    state.selected = [first.id];
    renderTable();
    const start = clipStart(first);
    const end = parseTime(first.Position) + parseTime(first.Duration || formatTime(durationFor(first.Evento)));
    mediaSeek(start);
    mediaPlay();
    state.playlist = { queue: queue.slice(1), end };
  }

  function tickPlaylist() {
    if (!state.playlist) return;
    if (getMediaTime() >= state.playlist.end - 0.05) {
      const nextId = state.playlist.queue.shift();
      if (!nextId) {
        mediaPause();
        state.playlist = null;
        return;
      }
      const ev = state.events.find((e) => e.id === nextId);
      if (!ev) { state.playlist = null; return; }
      state.selected = [ev.id];
      renderTable();
      const start = clipStart(ev);
      state.playlist.end = parseTime(ev.Position) + parseTime(ev.Duration || formatTime(durationFor(ev.Evento)));
      mediaSeek(start);
      mediaPlay();
    }
  }

  function csvEscape(v) {
    const s = String(v ?? "");
    if (/[;"\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
    return s;
  }

  function parseCsv(text) {
    text = text.replace(/^\uFEFF/, "").replace(/\r\n/g, "\n").replace(/\r/g, "\n");
    const lines = text.split("\n").filter((l) => l.length);
    if (!lines.length) return [];
    const sep = (lines[0].split(";").length > lines[0].split(",").length) ? ";" : ",";
    const rows = [];
    for (const line of lines) {
      const cells = [];
      let cur = "";
      let q = false;
      for (let i = 0; i < line.length; i++) {
        const ch = line[i];
        if (q) {
          if (ch === '"' && line[i + 1] === '"') { cur += '"'; i++; }
          else if (ch === '"') q = false;
          else cur += ch;
        } else if (ch === '"') q = true;
        else if (ch === sep) { cells.push(cur); cur = ""; }
        else cur += ch;
      }
      cells.push(cur);
      rows.push(cells);
    }
    const header = rows[0].map((h) => h.trim());
    const idx = (name) => header.findIndex((h) => h.toLowerCase() === name.toLowerCase());
    const iPos = idx("Position") >= 0 ? idx("Position") : idx("Posizione");
    const out = [];
    for (const cells of rows.slice(1)) {
      const get = (name, fallback) => {
        const i = idx(name);
        if (i >= 0) return (cells[i] || "").trim();
        if (fallback != null) {
          const j = idx(fallback);
          return j >= 0 ? (cells[j] || "").trim() : "";
        }
        return "";
      };
      const evento = get("Evento") || get("Name");
      if (!evento && !get("Position") && !(iPos >= 0 && cells[iPos])) continue;
      out.push({
        id: uid(),
        Name: get("Name") || evento,
        Position: get("Position", "Posizione") || "0:00:00.00",
        Duration: get("Duration") || formatTime(state.durationSec),
        Data: get("Data") || dateCsv(state.matchDate),
        Evento: evento,
        Portiere: get("Portiere"),
        Squadra: get("Squadra"),
        Chi: get("Chi"),
        Dove: get("Dove") || get("Field Position"),
        Lato: get("Lato"),
        Esito: get("Esito"),
      });
    }
    return out;
  }

  function matchSlug() {
    return (state.matchName || "partita").replace(/\s+/g, "-").toLowerCase();
  }

  function csvText() {
    const lines = [CSV_COLS.join(";")];
    for (const e of sortedEvents()) {
      const data = e.Data || dateCsv(state.matchDate);
      const row = {
        Name: e.Name || e.Evento,
        Position: e.Position,
        Duration: e.Duration || formatTime(state.durationSec),
        Data: data.includes("-") ? dateCsv(data) : data,
        Evento: e.Evento,
        Portiere: e.Portiere || "",
        Squadra: e.Squadra || "",
        Chi: e.Chi || "",
        Dove: e.Dove || "",
        Lato: e.Lato || "",
        Esito: e.Esito || "",
      };
      lines.push(CSV_COLS.map((c) => csvEscape(row[c])).join(";"));
    }
    return "\uFEFF" + lines.join("\r\n");
  }

  function csvFileName(suffix) {
    const tail = typeof suffix === "string" && suffix ? suffix : "eventi";
    return `${state.matchDate || "export"}_${matchSlug()}_${tail}.csv`;
  }

  function downloadFile(filename, blob) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  }

  function exportCsv(suffix) {
    if (suffix && typeof suffix !== "string") suffix = "";
    downloadFile(csvFileName(suffix), new Blob([csvText()], { type: "text/csv;charset=utf-8" }));
    const label = suffix === "primo-tempo" ? " (primo tempo)" : suffix === "finale" ? " (finale)" : "";
    toast(`Esportati ${state.events.length} eventi${label}`);
  }

  function reportApiUrl() {
    if (location.protocol === "http:" || location.protocol === "https:") {
      return `${location.origin}/api/report`;
    }
    return "http://127.0.0.1:8765/api/report";
  }

  async function generatePdf() {
    if (!state.events.length) {
      toast("Nessun evento da mettere nel report");
      return;
    }
    const btn = $("btnPdf");
    if (btn) {
      btn.disabled = true;
      btn.textContent = "PDF…";
    }
    try {
      const res = await fetch(reportApiUrl(), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          csv: csvText(),
          avversario: state.matchName || "Avversario",
        }),
      });
      if (!res.ok) {
        let msg = `Errore ${res.status}`;
        try {
          const j = await res.json();
          if (j && j.error) msg = j.error;
        } catch { /* corpo non JSON */ }
        throw new Error(msg);
      }
      downloadFile(
        `${state.matchDate || "export"}_${matchSlug()}_report.pdf`,
        await res.blob(),
      );
      toast("PDF scaricato");
    } catch (err) {
      console.warn(err);
      toast("PDF: avvia python app/tagger/serve.py e apri http://127.0.0.1:8765/");
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = "Genera PDF";
      }
    }
  }

  function importCsvFile(file) {
    const reader = new FileReader();
    reader.onload = () => {
      const rows = parseCsv(String(reader.result || ""));
      if (!rows.length) { toast("CSV vuoto o non letto"); return; }
      pushUndo();
      state.events = rows;
      state.selected = rows[0] ? [rows[0].id] : [];
      const d = rows.find((r) => r.Data)?.Data;
      if (d) state.matchDate = dateIso(d);
      persist();
      renderAll();
      toast(`Importati ${rows.length} eventi`);
    };
    reader.readAsText(file, "utf-8");
  }

  function score() {
    let noi = 0, loro = 0;
    for (const e of state.events) {
      if (e.Evento === "Gol" && e.Squadra === "Noi") noi += 1;
      else if (e.Evento === "Gol" && e.Squadra === "Loro") loro += 1;
      else if (e.Evento === "Autogol" && e.Squadra === "Loro") noi += 1;
      else if (e.Evento === "Autogol" && e.Squadra === "Noi") loro += 1;
    }
    return { noi, loro };
  }

  function filteredEvents() {
    const q = $("filterText").value.trim().toLowerCase();
    const ev = $("filterEvento").value;
    const sq = $("filterSquadra").value;
    return sortedEvents().filter((e) => {
      if (ev && e.Evento !== ev) return false;
      if (sq === "(vuota)" && (e.Squadra || "") !== "") return false;
      if (sq && sq !== "(vuota)" && e.Squadra !== sq) return false;
      if (!q) return true;
      return CSV_COLS.some((c) => String(e[c] || "").toLowerCase().includes(q));
    });
  }

  function colorFor(evento) {
    return EVENT_DEFS.find((d) => d.id === evento)?.color || "gray";
  }

  function renderPanel() {
    const host = $("panelBody");
    const groups = [];
    const seen = new Set();
    for (const def of EVENT_DEFS) {
      if (!seen.has(def.group)) { seen.add(def.group); groups.push(def.group); }
    }
    let html = "";
    for (const g of groups) {
      html += `<div class="group"><h4>${g}</h4><div class="btns">`;
      for (const def of EVENT_DEFS.filter((d) => d.group === g)) {
        const sc = (state.shortcuts[def.id] || "").toUpperCase();
        html += `<button type="button" class="tag event c-${def.color}" data-ev="${esc(def.id)}"><span class="kbd">${sc || "—"}</span>${esc(def.id)}</button>`;
      }
      html += `</div></div>`;
    }
    html += `<div class="group"><h4>Squadra</h4><div class="btns">
      <button type="button" class="tag noi" data-kw="Squadra" data-val="Noi"><span class="kbd">X</span>Noi</button>
      <button type="button" class="tag loro" data-kw="Squadra" data-val="Loro"><span class="kbd">C</span>Loro</button>
    </div></div>`;

    const prim = primaryEvent();
    const esiti = prim ? (ESITI_BY_EVENT[prim.Evento] || []) : [];
    const allEsiti = [...new Set([
      ...esiti,
      "Parata", "Gol", "Palo", "Fuori", "Ribattuto", "Assist",
      "Costruzione", "Transizione", "Palla inattiva", "Errore",
    ])];
    html += `<div class="group"><h4>Esito${prim ? " · " + esc(prim.Evento) : ""}</h4><div class="btns">`;
    for (const v of allEsiti) {
      const on = prim && prim.Esito === v;
      html += `<button type="button" class="tag${on ? " active" : ""}" data-kw="Esito" data-val="${esc(v)}">${esc(v)}</button>`;
    }
    html += `</div></div>`;

    html += `<div class="group"><h4>Chi</h4><div class="btns">`;
    for (const p of state.players) {
      const on = prim && prim.Chi === p;
      html += `<button type="button" class="tag${on ? " active" : ""}" data-kw="Chi" data-val="${esc(p)}">${esc(p)}</button>`;
    }
    html += `</div></div>`;

    html += `<div class="group"><h4>Portiere</h4><div class="btns">`;
    for (const p of state.keepers) {
      const on = prim && prim.Portiere === p;
      html += `<button type="button" class="tag${on ? " active" : ""}" data-kw="Portiere" data-val="${esc(p)}">${esc(p)}</button>`;
    }
    html += `</div></div>`;

    html += `<div class="group"><h4>Dove</h4><div class="btns">`;
    for (const z of ZONE_DEFS) {
      const on = prim && prim.Dove === z.label;
      html += `<button type="button" class="tag${on ? " active" : ""}" data-kw="Dove" data-val="${esc(z.label)}"><span class="kbd">${z.key}</span>${esc(z.label)}</button>`;
    }
    html += `</div></div>`;
    host.innerHTML = html;
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  function renderTable() {
    const body = $("eventsBody");
    const rows = filteredEvents();
    const sel = new Set(state.selected);
    const $filter = $("filterEvento");
    const current = $filter.value;
    const types = [...new Set(state.events.map((e) => e.Evento).filter(Boolean))].sort();
    $filter.innerHTML = `<option value="">Tutti gli eventi</option>` + types.map((t) => `<option ${t === current ? "selected" : ""}>${esc(t)}</option>`).join("");

    body.innerHTML = rows.map((e, i) => {
      const cls = [
        sel.has(e.id) ? "selected" : "",
        e.id === state.flashId ? "flash" : "",
      ].join(" ");
      return `<tr class="${cls}" data-id="${e.id}">
        <td><span class="dot" style="background:var(--${colorToVar(colorFor(e.Evento))})"></span></td>
        <td class="num">${i + 1}</td>
        <td class="num">${esc(e.Position)}</td>
        <td class="num">${esc(shortDur(e.Duration))}</td>
        <td>${esc(e.Evento)}</td>
        <td>${esc(e.Squadra)}</td>
        <td>${esc(e.Chi)}</td>
        <td>${esc(e.Esito)}</td>
        <td>${esc(e.Portiere)}</td>
        <td>${esc(e.Dove)}</td>
        <td>${esc(e.Lato)}</td>
      </tr>`;
    }).join("");
    if (state.flashId) setTimeout(() => { state.flashId = null; }, 700);
    renderInspector();
    const sc = score();
    $("score").textContent = `${sc.noi} – ${sc.loro}`;
    $("eventCount").textContent = `${state.events.length} eventi`;
    const n = state.selected.length;
    $("selInfo").textContent = n ? `${n} selezionat${n === 1 ? "o" : "i"}` : "Nessuna selezione";
    renderSyncMeta();
    renderTimeline();
  }

  function colorToVar(c) {
    return { orange: "orange", green: "green", red: "red", teal: "teal", yellow: "yellow", purple: "purple", blue: "accent", gray: "muted" }[c] || "muted";
  }

  function shortDur(d) {
    const s = parseTime(d);
    return Number.isFinite(s) ? `${s.toFixed(1)}s` : "";
  }

  function renderInspector() {
    const e = primaryEvent();
    const fields = ["Position", "Duration", "Evento", "Squadra", "Chi", "Esito", "Portiere", "Dove", "Lato"];
    for (const f of fields) {
      const el = $("ins" + f);
      if (!el) continue;
      if (document.activeElement === el) continue;
      el.value = e ? (e[f] || "") : "";
      el.disabled = !e;
    }
  }

  function commitInspector(field, value) {
    const e = primaryEvent();
    if (!e) return;
    pushUndo();
    e[field] = value;
    if (field === "Evento") e.Name = value;
    persist();
    renderTable();
    renderPanel();
  }

  function renderSyncMeta() {
    const ev = primaryEvent();
    if (!ev) {
      $("syncMeta").textContent = "Seleziona un evento ancora, posiziona il video sul momento giusto, poi applica.";
      return;
    }
    const vt = hasMedia() ? getMediaTime() : null;
    const off = vt == null ? null : vt - parseTime(ev.Position);
    $("syncMeta").textContent = `${ev.Evento} @ ${ev.Position}` +
      (off == null ? "" : `  ·  video ${formatTime(vt)}  ·  offset ${off >= 0 ? "+" : ""}${off.toFixed(2)}s`);
  }

  function renderTimeline() {
    const host = $("markers");
    if (!host) return;
    const dur = getMediaDuration();
    if (!dur) { host.innerHTML = ""; $("playhead").style.left = "0"; return; }
    host.innerHTML = sortedEvents().map((e) => {
      const pct = (parseTime(e.Position) / dur) * 100;
      return `<div class="marker" data-id="${e.id}" style="left:${pct}%;background:var(--${colorToVar(colorFor(e.Evento))})"></div>`;
    }).join("");
  }

  function updateClocks() {
    const live = liveSeconds();
    const tagTime = nowSeconds();
    $("liveClock").textContent = formatTime(live);
    if (state.mode === "video" && hasMedia()) {
      $("clockLabel").textContent = "VIDEO";
      $("clock").textContent = formatTime(getMediaTime());
      $("clock").classList.remove("live-on");
      const dur = getMediaDuration();
      $("vidTime").textContent = `${formatTime(getMediaTime())} / ${formatTime(dur)}`;
      const pct = dur ? (getMediaTime() / dur) * 100 : 0;
      $("playhead").style.left = pct + "%";
      $("btnPlay").textContent = isMediaPlaying() ? "Pausa" : "Play";
      tickPlaylist();
    } else {
      $("clockLabel").textContent = "CRONO";
      $("clock").textContent = formatTime(tagTime);
      $("clock").classList.toggle("live-on", state.live.running);
    }
    $("liveStatus").textContent = state.live.running ? "IN CORSO" : "PRONTO";
    $("liveStatus").classList.toggle("on", state.live.running);
    $("btnClockStart").textContent = state.live.running ? "In corso…" : (state.live.accumulated ? "Riprendi" : "Avvia");
    if (state.selected.length) renderSyncMeta();
  }

  function renderSyncBar() {
    const open = !!state.syncOpen;
    $("syncBody").classList.toggle("hidden", !open);
    $("syncToggleHint").textContent = open ? "nascondi" : "mostra";
    $("btnToggleSync").setAttribute("aria-expanded", open ? "true" : "false");
  }

  function renderMode() {
    $("app").classList.toggle("mode-live", state.mode === "live");
    $("app").classList.toggle("mode-video", state.mode === "video");
    $("modeLive").classList.toggle("active", state.mode === "live");
    $("modeVideo").classList.toggle("active", state.mode === "video");
    $("liveStage").classList.toggle("hidden", state.mode !== "live");
    $("videoStage").classList.toggle("hidden", state.mode !== "video");
    renderSyncBar();
  }

  function renderAll() {
    $("matchName").value = state.matchName;
    $("matchDate").value = state.matchDate;
    renderMode();
    renderPanel();
    renderTable();
    persist();
  }

  function scrollToEvent(id) {
    const row = document.querySelector(`#eventsBody tr[data-id="${id}"]`);
    if (row) row.scrollIntoView({ block: "nearest" });
  }

  function selectRow(id, { additive, range } = {}) {
    const rows = filteredEvents();
    if (range && state.selected.length) {
      const ids = rows.map((e) => e.id);
      const last = state.selected[state.selected.length - 1];
      const a = ids.indexOf(last);
      const b = ids.indexOf(id);
      if (a >= 0 && b >= 0) {
        const [lo, hi] = a < b ? [a, b] : [b, a];
        state.selected = ids.slice(lo, hi + 1);
      }
    } else if (additive) {
      if (state.selected.includes(id)) state.selected = state.selected.filter((x) => x !== id);
      else state.selected = [...state.selected, id];
    } else {
      state.selected = [id];
    }
    renderTable();
    renderPanel();
    const ev = primaryEvent();
    if (state.mode === "video" && ev && hasMedia()) mediaSeek(parseTime(ev.Position));
  }

  function moveSelection(dir) {
    const rows = filteredEvents();
    if (!rows.length) return;
    const cur = primaryEvent();
    let i = cur ? rows.findIndex((e) => e.id === cur.id) : -1;
    i = Math.max(0, Math.min(rows.length - 1, i + dir));
    selectRow(rows[i].id);
    scrollToEvent(rows[i].id);
  }

  function isTyping() {
    const el = document.activeElement;
    if (!el) return false;
    const tag = el.tagName;
    return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || el.isContentEditable;
  }

  function shortcutOf(evento) {
    return String(state.shortcuts[evento] || "").toLowerCase();
  }

  function onKey(ev) {
    if (ev.key === "?" || (ev.shiftKey && ev.key === "/")) {
      if (!isTyping()) { ev.preventDefault(); toggleHelp(true); }
      return;
    }
    if (ev.key === "Escape") {
      toggleHelp(false); toggleSettings(false); return;
    }
    if ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === "z") {
      ev.preventDefault(); undo(); return;
    }
    if ((ev.ctrlKey || ev.metaKey) && ev.key.toLowerCase() === "e") {
      ev.preventDefault(); exportCsv(); return;
    }
    if (isTyping()) return;

    if (ev.key === " ") {
      ev.preventDefault();
      if (state.mode === "video" && hasMedia()) {
        isMediaPlaying() ? mediaPause() : mediaPlay();
      }
      return;
    }
    if (ev.key === "ArrowLeft") {
      ev.preventDefault();
      if (hasMedia()) mediaSeek(getMediaTime() - (ev.shiftKey ? 5 : 1));
      return;
    }
    if (ev.key === "ArrowRight") {
      ev.preventDefault();
      if (hasMedia()) mediaSeek(getMediaTime() + (ev.shiftKey ? 5 : 1));
      return;
    }
    if (ev.key === "ArrowUp") { ev.preventDefault(); moveSelection(-1); return; }
    if (ev.key === "ArrowDown") { ev.preventDefault(); moveSelection(1); return; }
    if (ev.key === "Enter") {
      ev.preventDefault();
      const e = primaryEvent();
      if (e) playClip(e);
      return;
    }
    if (ev.key === "Delete" || ev.key === "Backspace") {
      ev.preventDefault();
      deleteSelected();
      return;
    }
    if (ev.shiftKey && ev.key.toLowerCase() === "i") { ev.preventDefault(); setInOut("in"); return; }
    if (ev.shiftKey && ev.key.toLowerCase() === "o") { ev.preventDefault(); setInOut("out"); return; }

    const key = ev.key.length === 1 ? ev.key.toLowerCase() : "";
    if (!key || ev.ctrlKey || ev.metaKey || ev.altKey) return;
    if (key === "x") { applyKeyword("Squadra", "Noi"); ev.preventDefault(); return; }
    if (key === "c") { applyKeyword("Squadra", "Loro"); ev.preventDefault(); return; }
    const zone = ZONE_DEFS.find((z) => z.key === key);
    if (zone) { applyKeyword("Dove", zone.label); ev.preventDefault(); return; }

    for (const def of EVENT_DEFS) {
      const sc = shortcutOf(def.id);
      if (sc && sc === key) {
        ev.preventDefault();
        createEvent(def.id);
        return;
      }
    }
  }

  function startClock() {
    if (state.live.running) return;
    state.live.running = true;
    state.live.startedAt = Date.now();
    persist();
  }
  function pauseClock() {
    if (!state.live.running) return;
    state.live.accumulated += Date.now() - state.live.startedAt;
    state.live.running = false;
    persist();
  }
  function resetClock() {
    state.live.running = false;
    state.live.accumulated = 0;
    persist();
  }

  function loadVideoFile(file) {
    clearYoutube();
    if (state.videoUrl) URL.revokeObjectURL(state.videoUrl);
    state.videoUrl = URL.createObjectURL(file);
    state.videoKind = "file";
    const v = $("video");
    v.src = state.videoUrl;
    v.classList.remove("hidden");
    $("ytHost").classList.add("hidden");
    $("ytHost").innerHTML = "";
    $("dropzone").classList.add("hidden");
    $("mediaWrap").classList.remove("hidden");
    $("video").classList.remove("hidden");
    state.mode = "video";
    renderMode();
    toast("Video caricato");
  }

  function ytIdFromUrl(url) {
    const m = String(url).match(/(?:v=|youtu\.be\/|embed\/)([A-Za-z0-9_-]{6,})/);
    return m ? m[1] : "";
  }

  function clearYoutube() {
    if (state.ytPlayer && state.ytPlayer.destroy) {
      try { state.ytPlayer.destroy(); } catch {}
    }
    state.ytPlayer = null;
    state.ytReady = false;
    $("ytHost").innerHTML = "";
  }

  function loadYoutube(url) {
    const id = ytIdFromUrl(url);
    if (!id) { toast("URL YouTube non valido"); return; }
    if (state.videoUrl) { URL.revokeObjectURL(state.videoUrl); state.videoUrl = null; }
    $("video").removeAttribute("src");
    $("video").classList.add("hidden");
    $("ytHost").classList.remove("hidden");
    $("dropzone").classList.add("hidden");
    $("mediaWrap").classList.remove("hidden");
    state.videoKind = "youtube";
    state.mode = "video";
    renderMode();
    const boot = () => {
      let host = $("ytHost");
      if (!host) {
        host = document.createElement("div");
        host.id = "ytHost";
        $("mediaWrap").appendChild(host);
      }
      host.innerHTML = "";
      state.ytPlayer = new YT.Player("ytHost", {
        videoId: id,
        playerVars: { rel: 0, modestbranding: 1, playsinline: 1 },
        events: {
          onReady: () => { state.ytReady = true; toast("YouTube pronto"); },
        },
      });
    };
    if (window.YT && window.YT.Player) boot();
    else {
      const tag = document.createElement("script");
      tag.src = "https://www.youtube.com/iframe_api";
      document.head.appendChild(tag);
      window.onYouTubeIframeAPIReady = boot;
    }
  }

  function toggleHelp(on) {
    $("helpOverlay").classList.toggle("hidden", on === false ? true : on === true ? false : $("helpOverlay").classList.contains("hidden") ? false : true);
    if (!$("helpOverlay").classList.contains("hidden")) {
      const extra = EVENT_DEFS.filter((d) => state.shortcuts[d.id]).map((d) =>
        `<li><kbd>${esc((state.shortcuts[d.id] || "").toUpperCase())}</kbd> ${esc(d.id)}</li>`
      ).join("");
      $("helpShortcuts").innerHTML = GLOBAL_SHORTCUTS.map(([k, v]) => `<li><kbd>${esc(k)}</kbd> ${esc(v)}</li>`).join("") + extra;
    }
  }

  function toggleSettings(on) {
    const hide = on === false ? true : on === true ? false : !$("settingsOverlay").classList.contains("hidden");
    $("settingsOverlay").classList.toggle("hidden", hide);
    if (hide) return;
    $("cfgPlayers").value = state.players.join("\n");
    $("cfgKeepers").value = state.keepers.join("\n");
    $("cfgDuration").value = state.durationSec;
    $("cfgDelay").value = state.delaySec;
    $("cfgStickyKeeper").innerHTML = `<option value="">(nessuno)</option>` +
      state.keepers.map((k) => `<option ${k === state.stickyKeeper ? "selected" : ""}>${esc(k)}</option>`).join("");
    $("shortcutList").innerHTML = EVENT_DEFS.map((d) =>
      `<div class="event-cfg-row">
        <span>${esc(d.id)}</span>
        <input data-sc="${esc(d.id)}" maxlength="1" value="${esc(state.shortcuts[d.id] || "")}" title="Tasto" />
        <input data-pr="${esc(d.id)}" type="number" step="0.5" min="0" value="${prerollFor(d.id)}" title="Preroll (s)" />
        <input data-du="${esc(d.id)}" type="number" step="0.5" min="0" value="${durationFor(d.id)}" title="Durata (s)" />
      </div>`
    ).join("");
  }

  function saveSettings() {
    state.players = $("cfgPlayers").value.split("\n").map((s) => s.trim()).filter(Boolean);
    state.keepers = $("cfgKeepers").value.split("\n").map((s) => s.trim()).filter(Boolean);
    state.durationSec = Number($("cfgDuration").value) || 5;
    state.delaySec = Number($("cfgDelay").value) || 0;
    state.stickyKeeper = $("cfgStickyKeeper").value;
    const nextSc = { ...state.shortcuts };
    const nextPr = { ...state.prerolls };
    const nextDu = { ...state.durations };
    for (const input of $("shortcutList").querySelectorAll("input")) {
      if (input.dataset.sc) nextSc[input.dataset.sc] = input.value.trim().toLowerCase();
      if (input.dataset.pr) {
        const n = Number(input.value);
        nextPr[input.dataset.pr] = Number.isFinite(n) ? Math.max(0, n) : prerollFor(input.dataset.pr);
      }
      if (input.dataset.du) {
        const n = Number(input.value);
        nextDu[input.dataset.du] = Number.isFinite(n) && n > 0 ? n : durationFor(input.dataset.du);
      }
    }
    state.shortcuts = nextSc;
    state.prerolls = nextPr;
    state.durations = nextDu;
    persist();
    toggleSettings(false);
    renderAll();
    toast("Impostazioni salvate");
  }

  function bind() {
    $("modeLive").onclick = () => { state.mode = "live"; persist(); renderMode(); };
    $("modeVideo").onclick = () => { state.mode = "video"; persist(); renderMode(); };
    $("matchName").oninput = () => { state.matchName = $("matchName").value; persist(); };
    $("matchDate").oninput = () => { state.matchDate = $("matchDate").value; persist(); };

    $("btnClockStart").onclick = startClock;
    $("btnClockPause").onclick = pauseClock;
    $("btnClockReset").onclick = resetClock;

    $("btnNew").onclick = () => {
      if (state.events.length && !confirm("Cancellare tutti gli eventi di questa sessione?")) return;
      pushUndo();
      state.events = [];
      state.selected = [];
      resetClock();
      persist();
      renderAll();
      toast("Sessione vuota");
    };
    $("btnUndo").onclick = undo;
    $("btnExport").onclick = () => exportCsv();
    $("btnPdf").onclick = () => generatePdf();
    $("btnImport").onclick = () => $("fileCsv").click();
    $("fileCsv").onchange = (e) => { const f = e.target.files[0]; if (f) importCsvFile(f); e.target.value = ""; };
    $("btnSettings").onclick = () => toggleSettings(true);
    $("btnCloseSettings").onclick = () => toggleSettings(false);
    $("btnSaveSettings").onclick = saveSettings;
    $("btnResetShortcuts").onclick = () => {
      state.shortcuts = Object.fromEntries(EVENT_DEFS.map((d) => [d.id, d.shortcut]));
      state.prerolls = defaultMap("preroll");
      state.durations = defaultMap("duration");
      toggleSettings(true);
    };
    $("btnToggleSync").onclick = () => {
      state.syncOpen = !state.syncOpen;
      persist();
      renderSyncBar();
    };
    $("btnHelp").onclick = () => toggleHelp(true);
    $("btnCloseHelp").onclick = () => toggleHelp(false);

    $("panelBody").addEventListener("click", (e) => {
      const btn = e.target.closest("button");
      if (!btn) return;
      if (btn.dataset.ev) createEvent(btn.dataset.ev);
      if (btn.dataset.kw) applyKeyword(btn.dataset.kw, btn.dataset.val);
    });

    $("eventsBody").addEventListener("click", (e) => {
      const tr = e.target.closest("tr");
      if (!tr) return;
      selectRow(tr.dataset.id, { additive: e.metaKey || e.ctrlKey, range: e.shiftKey });
    });

    $("filterText").oninput = renderTable;
    $("filterEvento").onchange = renderTable;
    $("filterSquadra").onchange = renderTable;
    $("btnSelectAll").onclick = () => { state.selected = filteredEvents().map((e) => e.id); renderTable(); renderPanel(); };
    $("btnDelete").onclick = deleteSelected;
    $("btnDup").onclick = duplicateSelected;

    for (const f of ["Position", "Duration", "Evento", "Squadra", "Chi", "Esito", "Portiere", "Dove", "Lato"]) {
      const el = $("ins" + f);
      el.addEventListener("change", () => commitInspector(f, el.value.trim()));
      el.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter") { ev.preventDefault(); el.blur(); }
      });
    }

    $("btnSyncAll").onclick = () => syncSelected(false);
    $("btnSyncFrom").onclick = () => syncSelected(true);
    $("btnShiftSel").onclick = () => {
      const d = Number($("shiftSec").value);
      if (!Number.isFinite(d)) return;
      const list = selectedEvents();
      if (!list.length) { toast("Nessuna selezione"); return; }
      shiftEvents(list, d);
    };
    $("btnShiftAll").onclick = () => {
      const d = Number($("shiftSec").value);
      if (!Number.isFinite(d)) return;
      shiftEvents(sortedEvents(), d);
    };

    $("btnPickVideo").onclick = () => $("fileVideo").click();
    $("fileVideo").onchange = (e) => { const f = e.target.files[0]; if (f) loadVideoFile(f); e.target.value = ""; };
    $("btnLoadYt").onclick = () => loadYoutube($("ytUrl").value);
    $("ytUrl").addEventListener("keydown", (e) => { if (e.key === "Enter") loadYoutube($("ytUrl").value); });
    $("btnChangeVideo").onclick = () => {
      $("dropzone").classList.remove("hidden");
      $("mediaWrap").classList.add("hidden");
    };

    const dz = $("dropzone");
    const pane = $("videoStage");
    for (const el of [dz, pane]) {
      el.addEventListener("dragover", (e) => { e.preventDefault(); });
      el.addEventListener("drop", (e) => {
        e.preventDefault();
        const f = e.dataTransfer.files[0];
        if (f && f.type.startsWith("video/")) loadVideoFile(f);
      });
    }

    $("btnPlay").onclick = () => isMediaPlaying() ? mediaPause() : mediaPlay();
    $("btnSkipBack").onclick = () => mediaSeek(getMediaTime() - 1);
    $("btnSkipFwd").onclick = () => mediaSeek(getMediaTime() + 1);
    $("btnSkipBack5").onclick = () => mediaSeek(getMediaTime() - 5);
    $("btnSkipFwd5").onclick = () => mediaSeek(getMediaTime() + 5);
    $("playbackRate").onchange = () => mediaRate(Number($("playbackRate").value));
    $("btnSetIn").onclick = () => setInOut("in");
    $("btnSetOut").onclick = () => setInOut("out");
    $("btnPlayEvent").onclick = () => { const e = primaryEvent(); if (e) playClip(e); };
    $("btnPlayFiltered").onclick = playFiltered;

    $("timeline").addEventListener("click", (e) => {
      const mk = e.target.closest(".marker");
      if (mk) { selectRow(mk.dataset.id); return; }
      const dur = getMediaDuration();
      if (!dur) return;
      const rect = $("timeline").getBoundingClientRect();
      mediaSeek(((e.clientX - rect.left) / rect.width) * dur);
    });

    document.addEventListener("keydown", onKey);
    window.addEventListener("beforeunload", persist);
    $("video").addEventListener("loadedmetadata", () => renderTimeline());
    $("app").focus();
  }

  function loop() {
    updateClocks();
    requestAnimationFrame(loop);
  }

  restore();
  bind();
  renderAll();
  loop();
})();
