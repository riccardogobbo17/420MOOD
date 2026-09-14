(() => {
  "use strict";

  const STORAGE_KEY = "fmp-tagger-v1";
  const CSV_COLS = ["Name", "Position", "Duration", "Data", "Evento", "Portiere", "Squadra", "Chi", "Dove", "Lato", "Esito"];

  const DEFAULT_PLAYERS = [
    "azza", "deba", "diego jr", "digao", "erick", "fabri",
    "mattia", "nic", "nico estratti", "ricky", "scanta", "zanna",
  ];
  const DEFAULT_KEEPERS = ["bara", "gio"];

  let EVENT_DEFS = [
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
  const BUILTIN_EVENT_DEFS = EVENT_DEFS.map((e) => ({ ...e }));
  const SHORTCUTS_VERSION = 2;
  const CLIP_TIMING_VERSION = 1;

  function defaultMap(field) {
    return Object.fromEntries(EVENT_DEFS.map((e) => [e.id, e[field]]));
  }

  let ESITI_BY_EVENT = {
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
  const BUILTIN_ESITI = JSON.parse(JSON.stringify(ESITI_BY_EVENT));

  const GLOBAL_SHORTCUTS = [
    ["Spazio", "Play / pausa video"],
    ["← / →", "−1s / +1s"],
    ["Shift+← / Shift+→", "−5s / +5s"],
    ["Shift+I / Shift+O", "In / Out dell'evento"],
    ["Invio", "Play clip evento"],
    ["Canc", "Elimina selezionati"],
    ["Cmd/Ctrl+Z", "Annulla"],
    ["Ctrl+E", "Esporta CSV"],
    ["↑ / ↓", "Evento precedente / successivo"],
    ["X / C", "Squadra Noi / Loro"],
    ["1 / 2 / 3", "Zona 1 / 2 / 3"],
    ["?", "Questa guida"],
  ];

  let ZONE_DEFS = [
    { key: "1", label: "Zona 1" },
    { key: "2", label: "Zona 2" },
    { key: "3", label: "Zona 3" },
  ];
  const BUILTIN_ZONES = ZONE_DEFS.map((z) => ({ ...z }));

  const PLAYER_CH = "fmp-tagger-player";
  const playerBus = ("BroadcastChannel" in window) ? new BroadcastChannel(PLAYER_CH) : null;

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
    sourceOpen: false,
    controlsOpen: false,
    panelOpen: true,
    eventsOpen: true,
    filterTypes: [],
    live: { running: false, startedAt: 0, accumulated: 0 },
    videoKind: null,
    videoUrl: null,
    videoFile: null,
    ytUrl: "",
    localFileName: "",
    layout: { panelW: 380 },
    ytPlayer: null,
    ytReady: false,
    popout: { win: null, ready: false, loaded: false, time: 0, duration: 0, paused: true, retry: null },
    undo: [],
    flashId: null,
    playheadIds: [],
    playlist: null,
    saveTimer: null,
    diskTimer: null,
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

  function formatClock(sec) {
    if (!Number.isFinite(sec) || sec < 0) sec = 0;
    const t = Math.floor(sec);
    const h = Math.floor(t / 3600);
    const m = Math.floor((t % 3600) / 60);
    const s = t % 60;
    return `${h}:${pad2(m)}:${pad2(s)}`;
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

  function clipRange(ev) {
    const start = parseTime(ev.Position);
    const dur = parseTime(ev.Duration || formatTime(durationFor(ev.Evento)));
    return { start, end: start + Math.max(0.2, dur) };
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

  function popoutOpen() {
    return !!(state.popout.win && !state.popout.win.closed);
  }

  function popoutMaster() {
    return popoutOpen() && state.popout.loaded;
  }

  function postPlayer(msg) {
    msg.source = "tagger";
    if (playerBus) {
      try { playerBus.postMessage(msg); } catch {
        try {
          const copy = { ...msg };
          delete copy.file;
          playerBus.postMessage(copy);
        } catch { /* ignore */ }
      }
    }
    if (popoutOpen()) {
      try { state.popout.win.postMessage(msg, "*"); } catch { /* ignore */ }
    }
  }

  function hasMedia() {
    if (popoutMaster()) return true;
    if (state.videoKind === "file") {
      const v = $("video");
      return v && v.duration && Number.isFinite(v.duration);
    }
    if (state.videoKind === "youtube") return !!(state.ytPlayer && state.ytReady);
    return false;
  }

  function getMediaTime() {
    if (popoutMaster()) return state.popout.time || 0;
    if (state.videoKind === "file") return $("video").currentTime || 0;
    if (state.videoKind === "youtube" && state.ytPlayer) {
      try { return state.ytPlayer.getCurrentTime() || 0; } catch { return 0; }
    }
    return 0;
  }

  function getMediaDuration() {
    if (popoutMaster()) return state.popout.duration || 0;
    if (state.videoKind === "file") return $("video").duration || 0;
    if (state.videoKind === "youtube" && state.ytPlayer) {
      try { return state.ytPlayer.getDuration() || 0; } catch { return 0; }
    }
    return 0;
  }

  function isMediaPlaying() {
    if (popoutMaster()) return !state.popout.paused;
    if (state.videoKind === "file") return !$("video").paused;
    if (state.videoKind === "youtube" && state.ytPlayer) {
      try { return state.ytPlayer.getPlayerState() === 1; } catch { return false; }
    }
    return false;
  }

  function mediaPlay() {
    if (popoutMaster()) { postPlayer({ type: "cmd", cmd: "play" }); return; }
    if (state.videoKind === "file") $("video").play();
    else if (state.ytPlayer) state.ytPlayer.playVideo();
  }

  function mediaPause() {
    if (popoutMaster()) { postPlayer({ type: "cmd", cmd: "pause" }); return; }
    if (state.videoKind === "file") $("video").pause();
    else if (state.ytPlayer) state.ytPlayer.pauseVideo();
  }

  function mediaSeek(t) {
    t = clampTime(t);
    if (popoutMaster()) { postPlayer({ type: "cmd", cmd: "seek", value: t }); state.popout.time = t; return; }
    if (state.videoKind === "file") $("video").currentTime = t;
    else if (state.ytPlayer) state.ytPlayer.seekTo(t, true);
  }

  function mediaRate(r) {
    if (popoutMaster()) { postPlayer({ type: "cmd", cmd: "rate", value: r }); return; }
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
        sourceOpen: state.sourceOpen,
        controlsOpen: state.controlsOpen,
        panelOpen: state.panelOpen !== false,
        eventsOpen: state.eventsOpen !== false,
        filterTypes: Array.isArray(state.filterTypes) ? state.filterTypes : [],
        videoKind: state.videoKind,
        ytUrl: state.ytUrl || "",
        localFileName: state.localFileName || "",
        layout: state.layout,
        liveAccumulated: state.live.running
          ? state.live.accumulated + (Date.now() - state.live.startedAt)
          : state.live.accumulated,
        savedAt: new Date().toISOString(),
      };
      try { localStorage.setItem(STORAGE_KEY, JSON.stringify(dump)); } catch {}
      scheduleDiskSession();
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
        sourceOpen: !!dump.sourceOpen,
        controlsOpen: !!dump.controlsOpen,
        panelOpen: dump.panelOpen !== false,
        eventsOpen: true,
        filterTypes: Array.isArray(dump.filterTypes) ? dump.filterTypes : [],
        videoKind: dump.videoKind || null,
        ytUrl: dump.ytUrl || "",
        localFileName: dump.localFileName || "",
        layout: { stageH: null, eventsH: null, panelW: 380, ...(dump.layout || {}) },
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
      Position: formatTime(clampTime(nowSeconds() - prerollFor(evento))),
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
    const { start, end } = clipRange(ev);
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
    const { start, end } = clipRange(first);
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
      const { start, end } = clipRange(ev);
      state.playlist.end = end;
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

  function csvText(list) {
    const lines = [CSV_COLS.join(";")];
    for (const e of (list || sortedEvents())) {
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
    const stem = `${matchSlug()}_${state.matchDate || "export"}`;
    if (!suffix || suffix === "eventi") return `${stem}.csv`;
    return `${stem}_${suffix}.csv`;
  }

  function downloadFile(filename, blob) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  }

  function exportCsv(suffix, list) {
    if (suffix && typeof suffix !== "string") suffix = "";
    const rows = list || sortedEvents();
    if (!rows.length) { toast("Nessun evento da esportare"); return; }
    const name = csvFileName(suffix);
    const text = csvText(rows);
    const label = suffix === "primo-tempo" ? " (primo tempo)" : suffix === "finale" ? " (finale)" : suffix === "selezione" ? " selezionati" : "";
    fetch(sessionApiUrl("csv"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        filename: name,
        csv: text,
        avversario: state.matchName,
        data: state.matchDate,
      }),
    }).then(async (res) => {
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || "export csv");
      toast(`CSV (${rows.length}${label}) in sessioni/${data.file || name}`);
    }).catch(() => {
      downloadFile(name, new Blob([text], { type: "text/csv;charset=utf-8" }));
      toast(`Esportati ${rows.length} eventi${label} (download)`);
    });
  }

  function clipsForExport() {
    const list = selectedEvents();
    if (!list.length) { toast("Seleziona almeno un evento"); return null; }
    return list.map((e, i) => {
      const { start, end } = clipRange(e);
      return {
        n: i + 1,
        id: e.id,
        name: e.Name || e.Evento,
        evento: e.Evento,
        start: e.Position,
        startSec: start,
        duration: e.Duration,
        durationSec: Math.max(0.2, end - start),
        endSec: end,
        squadra: e.Squadra || "",
        chi: e.Chi || "",
        esito: e.Esito || "",
      };
    });
  }

  function sourceForExport() {
    if (state.videoKind === "youtube") return { kind: "youtube", url: state.ytUrl || $("ytUrl")?.value || "" };
    if (state.videoKind === "file") return { kind: "file", name: state.localFileName || "video.mp4" };
    return { kind: "none", name: "" };
  }

  function exportClipJson() {
    const clips = clipsForExport();
    if (!clips) return;
    const body = {
      source: sourceForExport(),
      note: "start = Position (già dopo preroll). duration = Duration. Per un solo video: taglia con ffmpeg e carica a mano su YouTube.",
      clips,
    };
    downloadFile(
      `${state.matchDate || "export"}_${matchSlug()}_clips.json`,
      new Blob([JSON.stringify(body, null, 2)], { type: "application/json" }),
    );
    toast(`Clip list: ${clips.length} clip`);
  }

  function exportM3u() {
    const clips = clipsForExport();
    if (!clips) return;
    const src = sourceForExport();
    const media = src.kind === "youtube" ? src.url : (src.name || "video.mp4");
    const lines = ["#EXTM3U", `#PLAYLIST:${matchSlug()}`];
    for (const c of clips) {
      lines.push(`#EXTINF:${Math.round(c.durationSec)},${c.name}`);
      lines.push(`#EXTVLCOPT:start-time=${c.startSec.toFixed(2)}`);
      lines.push(`#EXTVLCOPT:stop-time=${c.endSec.toFixed(2)}`);
      lines.push(media);
    }
    downloadFile(
      `${state.matchDate || "export"}_${matchSlug()}_clips.m3u`,
      new Blob([lines.join("\n")], { type: "audio/x-mpegurl" }),
    );
    toast(`M3U: ${clips.length} clip`);
  }

  function exportFfmpeg() {
    const clips = clipsForExport();
    if (!clips) return;
    const src = sourceForExport();
    const infile = src.kind === "file" ? (src.name || "video.mp4") : "video.mp4";
    const lines = [
      "#!/bin/bash",
      "# Taglia i clip selezionati e li concatena.",
      "# YouTube: scarica prima il file (es. yt-dlp) e rinominalo, poi lancia lo script.",
      "# Upload automatico su YouTube non è supportato da questa app.",
      `IN="${infile.replace(/"/g, '\\"')}"`,
      "OUT=highlights.mp4",
      "LIST=$(mktemp)",
      "trap 'rm -f \"$LIST\" clip_*.mp4' EXIT",
      "",
    ];
    clips.forEach((c) => {
      const name = `clip_${String(c.n).padStart(3, "0")}.mp4`;
      lines.push(`ffmpeg -y -ss ${c.startSec.toFixed(2)} -t ${c.durationSec.toFixed(2)} -i "$IN" -c copy "${name}"`);
      lines.push(`echo "file '${name}'" >> "$LIST"`);
    });
    lines.push('ffmpeg -y -f concat -safe 0 -i "$LIST" -c copy "$OUT"');
    lines.push('echo "Creato $OUT — caricalo a mano su YouTube se serve."');
    downloadFile(
      `${state.matchDate || "export"}_${matchSlug()}_ffmpeg.sh`,
      new Blob([lines.join("\n") + "\n"], { type: "text/x-shellscript" }),
    );
    toast(`Script ffmpeg: ${clips.length} clip`);
  }

  function sessionPayload() {
    return {
      version: 1,
      savedAt: new Date().toISOString(),
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
      sourceOpen: state.sourceOpen,
      controlsOpen: state.controlsOpen,
      panelOpen: state.panelOpen !== false,
      eventsOpen: state.eventsOpen !== false,
      filterTypes: Array.isArray(state.filterTypes) ? state.filterTypes : [],
      videoKind: state.videoKind,
      ytUrl: state.ytUrl || "",
      localFileName: state.localFileName || "",
      layout: state.layout,
      liveAccumulated: state.live.running
        ? state.live.accumulated + (Date.now() - state.live.startedAt)
        : state.live.accumulated,
    };
  }

  function saveSessionFile() {
    saveDiskSession({ toastOk: true });
  }

  function scheduleDiskSession() {
    clearTimeout(state.diskTimer);
    state.diskTimer = setTimeout(() => saveDiskSession(), 500);
  }

  async function saveDiskSession({ toastOk } = {}) {
    try {
      const res = await fetch(sessionApiUrl(), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(sessionPayload()),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || "salvataggio sessione");
      if (toastOk) toast(`Sessione in sessioni/${data.file || "ultima.json"}`);
    } catch (err) {
      if (toastOk) {
        downloadFile(
          `${state.matchDate || "export"}_${matchSlug()}_sessione.json`,
          new Blob([JSON.stringify(sessionPayload(), null, 2)], { type: "application/json" }),
        );
        toast("Sessione scaricata (serve.py non raggiungibile)");
      }
    }
  }

  function flushDiskSession() {
    const body = JSON.stringify(sessionPayload());
    try {
      if (navigator.sendBeacon) {
        navigator.sendBeacon(sessionApiUrl(), new Blob([body], { type: "application/json" }));
        return;
      }
    } catch { /* ignore */ }
    saveDiskSession();
  }

  async function loadDiskSession() {
    try {
      const res = await fetch(sessionApiUrl());
      if (!res.ok) return;
      const dump = await res.json();
      if (!dump || !Array.isArray(dump.events)) return;
      applySessionDump(dump, { restoreVideo: true });
    } catch { /* serve.py spento */ }
  }

  function applySessionDump(dump, { restoreVideo } = { restoreVideo: true }) {
    if (!dump || typeof dump !== "object") { toast("Sessione non valida"); return; }
    Object.assign(state, {
      mode: dump.mode || state.mode,
      events: (dump.events || []).map((e) => ({ ...e, id: e.id || uid() })),
      matchName: dump.matchName || "",
      matchDate: dump.matchDate || todayInput(),
      players: dump.players || DEFAULT_PLAYERS,
      keepers: dump.keepers || DEFAULT_KEEPERS,
      shortcuts: dump.shortcutsVersion === SHORTCUTS_VERSION
        ? { ...defaultMap("shortcut"), ...(dump.shortcuts || {}) }
        : (dump.shortcuts || state.shortcuts),
      prerolls: dump.clipTimingVersion === CLIP_TIMING_VERSION
        ? { ...defaultMap("preroll"), ...(dump.prerolls || {}) }
        : (dump.prerolls || state.prerolls),
      durations: dump.clipTimingVersion === CLIP_TIMING_VERSION
        ? { ...defaultMap("duration"), ...(dump.durations || {}) }
        : (dump.durations || state.durations),
      durationSec: dump.durationSec ?? state.durationSec,
      delaySec: dump.delaySec ?? state.delaySec,
      prerollSec: dump.prerollSec ?? state.prerollSec,
      stickyKeeper: dump.stickyKeeper || "",
      syncOpen: !!dump.syncOpen,
      sourceOpen: !!dump.sourceOpen,
      controlsOpen: !!dump.controlsOpen,
      panelOpen: dump.panelOpen !== false,
      eventsOpen: dump.eventsOpen !== false,
      filterTypes: Array.isArray(dump.filterTypes) ? dump.filterTypes : [],
      videoKind: dump.videoKind || null,
      ytUrl: dump.ytUrl || "",
      localFileName: dump.localFileName || "",
      layout: { stageH: null, eventsH: null, panelW: 380, ...(dump.layout || {}) },
    });
    state.live.accumulated = dump.liveAccumulated || 0;
    state.live.running = false;
    state.selected = [];
    persist();
    applyLayout();
    renderAll();
    renderVideoSource();
    if (restoreVideo) resumeVideoSource();
  }

  function loadSessionFile(file) {
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const dump = JSON.parse(String(reader.result || ""));
        if (state.events.length && !confirm("Sostituire la sessione attuale?")) return;
        applySessionDump(dump);
        toast(`Sessione: ${state.events.length} eventi`);
      } catch {
        toast("JSON sessione non valido");
      }
    };
    reader.readAsText(file, "utf-8");
  }

  function reportApiUrl() {
    if (location.protocol === "http:" || location.protocol === "https:") {
      return `${location.origin}/api/report`;
    }
    return "http://127.0.0.1:8765/api/report";
  }

  function configApiUrl() {
    if (location.protocol === "http:" || location.protocol === "https:") {
      return `${location.origin}/api/config`;
    }
    return "http://127.0.0.1:8765/api/config";
  }

  function sessionApiUrl(extra) {
    const tail = extra ? `/api/session/${extra}` : "/api/session";
    if (location.protocol === "http:" || location.protocol === "https:") {
      return `${location.origin}${tail}`;
    }
    return `http://127.0.0.1:8765${tail}`;
  }

  function syncEventMaps() {
    const nextSc = {};
    const nextPr = {};
    const nextDu = {};
    for (const def of EVENT_DEFS) {
      nextSc[def.id] = def.shortcut || state.shortcuts[def.id] || "";
      nextPr[def.id] = Number.isFinite(def.preroll) ? def.preroll : (state.prerolls[def.id] ?? 5);
      nextDu[def.id] = Number.isFinite(def.duration) && def.duration > 0 ? def.duration : (state.durations[def.id] ?? 5);
    }
    state.shortcuts = nextSc;
    state.prerolls = nextPr;
    state.durations = nextDu;
  }

  function applyConfig(cfg) {
    if (!cfg || typeof cfg !== "object") return;
    const rosa = cfg.rosa || {};
    if (Array.isArray(rosa.giocatori) && rosa.giocatori.length) {
      state.players = rosa.giocatori.map((s) => String(s).trim()).filter(Boolean);
    }
    if (Array.isArray(rosa.portieri) && rosa.portieri.length) {
      state.keepers = rosa.portieri.map((s) => String(s).trim()).filter(Boolean);
    }
    if (rosa.portiere_sticky != null) state.stickyKeeper = String(rosa.portiere_sticky || "");
    const list = (cfg.eventi && cfg.eventi.eventi) || (Array.isArray(cfg.eventi) ? cfg.eventi : null);
    if (Array.isArray(list) && list.length) {
      EVENT_DEFS = list.map((e) => ({
        id: String(e.id || "").trim(),
        shortcut: String(e.shortcut || "").trim().toLowerCase().slice(0, 1),
        color: String(e.color || "gray"),
        group: String(e.group || "Altro"),
        preroll: Number(e.preroll) || 0,
        duration: Number(e.duration) || 5,
      })).filter((e) => e.id);
      syncEventMaps();
    }
    const attr = cfg.attributi || {};
    if (attr.esiti && typeof attr.esiti === "object") {
      ESITI_BY_EVENT = { ...attr.esiti };
    }
    if (Array.isArray(attr.zone) && attr.zone.length) {
      ZONE_DEFS = attr.zone.map((z) => ({
        key: String(z.key || "").trim().slice(0, 1),
        label: String(z.label || "").trim(),
      })).filter((z) => z.key && z.label);
    }
    const opt = cfg.opzioni || {};
    if (opt.durata_fallback != null) state.durationSec = Number(opt.durata_fallback) || 5;
    if (opt.ritardo_tagging != null) state.delaySec = Number(opt.ritardo_tagging) || 0;
    if (cfg.path && $("cfgPath")) {
      $("cfgPath").innerHTML = `Cartella config: <code>${esc(cfg.path)}</code>. Si ricarica ad ogni avvio di serve.py.`;
    }
  }

  function configPayload() {
    return {
      rosa: {
        giocatori: state.players,
        portieri: state.keepers,
        portiere_sticky: state.stickyKeeper,
      },
      eventi: {
        eventi: EVENT_DEFS.map((d) => ({
          id: d.id,
          shortcut: state.shortcuts[d.id] || d.shortcut || "",
          color: d.color,
          group: d.group,
          preroll: prerollFor(d.id),
          duration: durationFor(d.id),
        })),
      },
      attributi: {
        esiti: ESITI_BY_EVENT,
        zone: ZONE_DEFS,
      },
      opzioni: {
        durata_fallback: state.durationSec,
        ritardo_tagging: state.delaySec,
      },
    };
  }

  async function loadDiskConfig() {
    try {
      const res = await fetch(configApiUrl());
      if (!res.ok) return;
      const cfg = await res.json();
      applyConfig(cfg);
      persist();
    } catch {
      /* serve.py non in esecuzione */
    }
  }

  async function saveDiskConfig() {
    const res = await fetch(configApiUrl(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(configPayload()),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || "salvataggio config fallito");
    applyConfig(data);
    return data;
  }

  function esitiText() {
    return Object.entries(ESITI_BY_EVENT).map(([k, vals]) =>
      `${k}: ${(vals || []).join(", ")}`
    ).join("\n");
  }

  function parseEsiti(text) {
    const out = {};
    for (const line of String(text || "").split("\n")) {
      const t = line.trim();
      if (!t) continue;
      const idx = t.indexOf(":");
      if (idx < 1) continue;
      const key = t.slice(0, idx).trim();
      const vals = t.slice(idx + 1).split(",").map((s) => s.trim()).filter(Boolean);
      if (key) out[key] = vals;
    }
    return out;
  }

  function zoneText() {
    return ZONE_DEFS.map((z) => `${z.key} = ${z.label}`).join("\n");
  }

  function parseZone(text) {
    const out = [];
    for (const line of String(text || "").split("\n")) {
      const t = line.trim();
      if (!t) continue;
      const m = t.match(/^(.+?)\s*=\s*(.+)$/) || t.match(/^(\S+)\s+(.+)$/);
      if (!m) continue;
      const key = m[1].trim().slice(0, 1);
      const label = m[2].trim();
      if (key && label) out.push({ key, label });
    }
    return out.length ? out : ZONE_DEFS;
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
    const types = new Set(state.filterTypes || []);
    const sq = $("filterSquadra").value;
    return sortedEvents().filter((e) => {
      if (types.size && !types.has(e.Evento)) return false;
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

  function typeFilterLabel() {
    const sel = state.filterTypes || [];
    if (!sel.length) return "Tutti i tipi";
    if (sel.length === 1) return sel[0];
    if (sel.length === 2) return sel.join(", ");
    return `${sel.length} tipi`;
  }

  function renderTypeFilter() {
    const types = [...new Set(state.events.map((e) => e.Evento).filter(Boolean))].sort();
    const known = new Set(types);
    state.filterTypes = (state.filterTypes || []).filter((t) => known.has(t));
    const sel = new Set(state.filterTypes);
    const btn = $("btnFilterEvento");
    if (btn) btn.textContent = typeFilterLabel() + " ▾";
    const menu = $("filterEventoMenu");
    if (!menu) return;
    menu.innerHTML = `<button type="button" data-types="all">Tutti</button>` + types.map((t) => {
      const on = sel.has(t);
      const n = state.events.filter((e) => e.Evento === t).length;
      return `<label class="check"><input type="checkbox" data-type="${esc(t)}" ${on ? "checked" : ""}/>${esc(t)} <span class="muted">${n}</span></label>`;
    }).join("");
  }

  function placeTypeMenu() {
    const btn = $("btnFilterEvento");
    const menu = $("filterEventoMenu");
    if (!btn || !menu) return;
    const r = btn.getBoundingClientRect();
    menu.style.left = Math.max(8, Math.min(r.left, window.innerWidth - 220)) + "px";
    menu.style.bottom = (window.innerHeight - r.top + 4) + "px";
    menu.style.top = "auto";
    menu.style.right = "auto";
  }

  function renderTable() {
    const body = $("eventsBody");
    const rows = filteredEvents();
    const sel = new Set(state.selected);
    renderTypeFilter();

    const play = new Set(state.playheadIds || []);
    body.innerHTML = rows.map((e, i) => {
      const cls = [
        sel.has(e.id) ? "selected" : "",
        play.has(e.id) ? "playhead" : "",
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
    if ($("eventFoldMeta")) {
      const total = state.events.length;
      $("eventFoldMeta").textContent = rows.length === total
        ? `${total} eventi`
        : `${rows.length} / ${total} eventi`;
    }
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
    host.innerHTML = filteredEvents().map((e) => {
      const pct = (parseTime(e.Position) / dur) * 100;
      return `<div class="marker" data-id="${e.id}" style="left:${pct}%;background:var(--${colorToVar(colorFor(e.Evento))})"></div>`;
    }).join("");
  }

  function updateClocks() {
    const live = liveSeconds();
    const tagTime = nowSeconds();
    $("liveClock").textContent = formatClock(live);
    if (state.mode === "video" && hasMedia()) {
      $("clockLabel").textContent = "VIDEO";
      $("clock").textContent = formatClock(getMediaTime());
      $("clock").classList.remove("live-on");
      const dur = getMediaDuration();
      $("vidTime").textContent = `${formatClock(getMediaTime())} / ${formatClock(dur)}`;
      const pct = dur ? (getMediaTime() / dur) * 100 : 0;
      $("playhead").style.left = pct + "%";
      $("btnPlay").textContent = isMediaPlaying() ? "Pausa" : "Play";
      tickPlaylist();
    } else {
      $("clockLabel").textContent = "CRONO";
      $("clock").textContent = formatClock(tagTime);
      $("clock").classList.toggle("live-on", state.live.running);
    }
    $("liveStatus").textContent = state.live.running ? "IN CORSO" : "PRONTO";
    $("liveStatus").classList.toggle("on", state.live.running);
    $("btnClockStart").textContent = state.live.running ? "In corso…" : (state.live.accumulated ? "Riprendi" : "Avvia");
    if (state.selected.length) renderSyncMeta();
    updatePlayheadRow();
  }

  function playheadEventIds(t) {
    const rows = filteredEvents();
    if (!rows.length) return [];
    let best = -1;
    for (const e of rows) {
      const p = parseTime(e.Position);
      if (p <= t + 0.04) best = p;
      else break;
    }
    if (best < 0) return [];
    return rows.filter((e) => Math.abs(parseTime(e.Position) - best) < 0.04).map((e) => e.id);
  }

  function updatePlayheadRow() {
    const body = $("eventsBody");
    if (!body) return;
    let ids = [];
    if (state.mode === "video" && hasMedia()) {
      ids = playheadEventIds(getMediaTime());
    }
    const prev = state.playheadIds || [];
    const same = prev.length === ids.length && prev.every((id, i) => id === ids[i]);
    if (same) return;
    state.playheadIds = ids;
    const set = new Set(ids);
    for (const tr of body.querySelectorAll("tr")) {
      tr.classList.toggle("playhead", set.has(tr.dataset.id));
    }
    const row = body.querySelector("tr.playhead");
    if (row && state.eventsOpen !== false) row.scrollIntoView({ block: "nearest" });
  }

  function setFold(foldId, bodyId, open) {
    const fold = $(foldId);
    const body = $(bodyId);
    if (fold) fold.classList.toggle("open", !!open);
    if (body) body.classList.toggle("hidden", !open);
    const btn = fold && fold.querySelector(".fold-toggle");
    if (btn) btn.setAttribute("aria-expanded", open ? "true" : "false");
  }

  function renderFolds() {
    const needFile = state.videoKind === "file" && !state.videoUrl && !!state.localFileName;
    setFold("sourceFold", "sourceBody", !!state.sourceOpen || needFile);
    setFold("controlsFold", "videoControls", !!state.controlsOpen);
    setFold("syncBar", "syncBody", !!state.syncOpen);
    setFold("panel", "panelInner", state.panelOpen !== false);
    setFold("eventsPane", "eventsInner", state.eventsOpen !== false);
    $("app").classList.toggle("panel-collapsed", state.panelOpen === false);
    $("app").classList.toggle("events-collapsed", state.eventsOpen === false);
    if ($("eventFoldMeta")) $("eventFoldMeta").textContent = `${state.events.length} eventi`;
    applyLayout();
  }

  function renderMode() {
    $("app").classList.toggle("mode-live", state.mode === "live");
    $("app").classList.toggle("mode-video", state.mode === "video");
    $("modeLive").classList.toggle("active", state.mode === "live");
    $("modeVideo").classList.toggle("active", state.mode === "video");
    $("liveStage").classList.toggle("hidden", state.mode !== "live");
    $("videoStage").classList.toggle("hidden", state.mode !== "video");
    renderFolds();
    if (state.mode === "video") renderVideoSource();
  }

  function applyLayout() {
    const app = $("app");
    const pane = $("eventsPane");
    const L = state.layout || {};
    let frac = Number(L.eventsFrac);
    if (!Number.isFinite(frac) && L.stageH && L.eventsH) {
      frac = L.eventsH / (Number(L.stageH) + Number(L.eventsH));
    }
    if (!Number.isFinite(frac) || frac < 0.16 || frac > 0.5) frac = 0.32;
    state.layout.eventsFrac = frac;
    const pct = Math.round(frac * 100) + "%";
    app.style.setProperty("--events-pct", pct);
    app.style.removeProperty("--events-frac");
    if (pane) {
      if (state.eventsOpen === false) {
        pane.style.flex = "";
        pane.style.maxHeight = "";
      } else {
        pane.style.flex = `0 1 ${pct}`;
      }
    }
    const maxPanel = Math.max(180, Math.floor((app.clientWidth || window.innerWidth) * 0.42));
    const panelW = Number(L.panelW);
    if (Number.isFinite(panelW) && panelW > 0) {
      app.style.setProperty("--panel-w", Math.max(180, Math.min(panelW, maxPanel)) + "px");
    }
    app.style.removeProperty("--stage-h");
    app.style.removeProperty("--events-h");
  }

  function bindSplitters() {
    const app = $("app");
    function drag(el, kind, onMove) {
      el.addEventListener("mousedown", (e) => {
        e.preventDefault();
        el.classList.add("dragging");
        app.classList.add(kind === "v" ? "dragging-v" : "dragging");
        const move = (ev) => onMove(ev);
        const up = () => {
          el.classList.remove("dragging");
          app.classList.remove("dragging", "dragging-v");
          document.removeEventListener("mousemove", move);
          document.removeEventListener("mouseup", up);
          persist();
        };
        document.addEventListener("mousemove", move);
        document.addEventListener("mouseup", up);
      });
    }
    drag($("splitV"), "v", (ev) => {
      const rect = app.getBoundingClientRect();
      const frac = (rect.bottom - ev.clientY) / Math.max(1, rect.height);
      state.layout.eventsFrac = Math.max(0.16, Math.min(0.48, frac));
      applyLayout();
    });
    drag($("splitH"), "h", (ev) => {
      const stage = $("stage").getBoundingClientRect();
      const panelW = Math.max(220, Math.min(stage.width - 220, stage.right - ev.clientX));
      state.layout.panelW = Math.round(panelW);
      applyLayout();
    });
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
      toggleHelp(false); toggleSettings(false); togglePush(false); return;
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

  function resetYtHost() {
    const wrap = $("mediaWrap");
    const old = $("ytHost");
    if (old) old.remove();
    const host = document.createElement("div");
    host.id = "ytHost";
    host.className = "hidden";
    wrap.appendChild(host);
    return host;
  }

  function renderVideoSource() {
    const fileReady = state.videoKind === "file" && !!state.videoUrl;
    const ytReady = state.videoKind === "youtube" && !!state.ytUrl;
    const needFile = state.videoKind === "file" && !state.videoUrl && !!state.localFileName;
    $("dropzone").classList.toggle("hidden", fileReady || ytReady || needFile);
    $("mediaWrap").classList.toggle("hidden", !fileReady && !ytReady);
    $("reattachBar").classList.toggle("hidden", !needFile);
    if (needFile) $("reattachName").textContent = state.localFileName;
    if (state.ytUrl && $("ytUrl") && document.activeElement !== $("ytUrl")) {
      $("ytUrl").value = state.ytUrl;
    }
    const popped = popoutMaster();
    if ($("popoutPlaceholder")) $("popoutPlaceholder").classList.toggle("hidden", !popped);
    if (popped) {
      $("video").classList.add("hidden");
      $("ytHost").classList.add("hidden");
    }
    if (needFile) $("sourceHint").textContent = `Atteso: ${state.localFileName}`;
    else if (popped) $("sourceHint").textContent = "Video sull'altra finestra";
    else if (fileReady) $("sourceHint").textContent = state.localFileName || "File locale";
    else if (ytReady) $("sourceHint").textContent = "YouTube — puoi cambiare URL o file.";
    else $("sourceHint").textContent = "Puoi cambiare file o URL in qualsiasi momento.";
  }

  function resumeVideoSource() {
    if (state.videoKind === "youtube" && state.ytUrl) {
      $("ytUrl").value = state.ytUrl;
      loadYoutube(state.ytUrl);
    } else {
      renderVideoSource();
    }
  }

  function loadVideoFile(file) {
    clearYoutube();
    if (state.videoUrl) URL.revokeObjectURL(state.videoUrl);
    state.videoFile = file;
    state.videoUrl = URL.createObjectURL(file);
    state.videoKind = "file";
    state.localFileName = file.name || "video.mp4";
    state.ytUrl = "";
    const v = $("video");
    v.src = state.videoUrl;
    v.classList.remove("hidden");
    $("ytHost").classList.add("hidden");
    state.mode = "video";
    persist();
    renderMode();
    renderVideoSource();
    notifyPopoutLoad();
    toast("Video caricato: " + state.localFileName);
  }

  function ytIdFromUrl(url) {
    const m = String(url || "").match(/(?:v=|youtu\.be\/|embed\/|shorts\/)([A-Za-z0-9_-]{6,})/);
    return m ? m[1] : "";
  }

  function clearYoutube() {
    if (state.ytPlayer && state.ytPlayer.destroy) {
      try { state.ytPlayer.destroy(); } catch {}
    }
    state.ytPlayer = null;
    state.ytReady = false;
    resetYtHost();
  }

  function loadYoutube(url) {
    const id = ytIdFromUrl(url);
    if (!id) { toast("URL YouTube non valido"); return; }
    const canonical = `https://www.youtube.com/watch?v=${id}`;
    clearYoutube();
    if (state.videoUrl) { URL.revokeObjectURL(state.videoUrl); state.videoUrl = null; }
    state.videoFile = null;
    $("video").removeAttribute("src");
    $("video").classList.add("hidden");
    const host = $("ytHost");
    host.classList.remove("hidden");
    state.videoKind = "youtube";
    state.ytUrl = canonical;
    state.localFileName = "";
    state.mode = "video";
    $("ytUrl").value = canonical;
    persist();
    renderMode();
    renderVideoSource();
    const boot = () => {
      const node = $("ytHost") || resetYtHost();
      node.classList.remove("hidden");
      state.ytPlayer = new YT.Player(node.id, {
        videoId: id,
        playerVars: { rel: 0, modestbranding: 1, playsinline: 1 },
        events: {
          onReady: () => { state.ytReady = true; notifyPopoutLoad(); toast("YouTube pronto"); },
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

  function popoutPayload() {
    return {
      type: "load",
      kind: state.videoKind,
      ytUrl: state.ytUrl,
      videoId: ytIdFromUrl(state.ytUrl),
      file: state.videoFile || null,
      blobUrl: state.videoUrl || "",
      time: state.popout.time || 0,
      paused: true,
      rate: Number($("playbackRate") && $("playbackRate").value) || 1,
    };
  }

  function notifyPopoutLoad() {
    if (!popoutOpen()) return;
    state.popout.time = getMediaTime();
    sendPopoutLoad();
  }

  function sendPopoutLoad() {
    const msg = popoutPayload();
    postPlayer(msg);
    if (popoutOpen()) {
      try { state.popout.win.postMessage(msg, "*"); } catch { /* ignore */ }
    }
  }

  function stopPopoutHandshake() {
    if (state.popout.retry) {
      clearInterval(state.popout.retry);
      state.popout.retry = null;
    }
  }

  function startPopoutHandshake() {
    stopPopoutHandshake();
    state.popout.tries = 0;
    sendPopoutLoad();
    state.popout.retry = setInterval(() => {
      if (!popoutOpen()) { stopPopoutHandshake(); return; }
      if (state.popout.loaded) { stopPopoutHandshake(); return; }
      state.popout.tries = (state.popout.tries || 0) + 1;
      if (state.popout.tries > 25) {
        stopPopoutHandshake();
        toast("Il video non è arrivato nella nuova finestra. Clicca Play lì, o chiudi e riapri.");
        return;
      }
      postPlayer({ type: "hello" });
      sendPopoutLoad();
    }, 350);
  }

  function onPlayerMsg(msg) {
    if (!msg || msg.source !== "player") return;
    if (msg.type === "ready") {
      state.popout.ready = true;
      sendPopoutLoad();
    } else if (msg.type === "loaded") {
      state.popout.loaded = true;
      state.popout.time = msg.time || state.popout.time || 0;
      state.popout.duration = msg.duration || 0;
      state.popout.paused = !!msg.paused;
      stopPopoutHandshake();
      if (state.videoKind === "file") $("video").pause();
      else if (state.ytPlayer) state.ytPlayer.pauseVideo();
      renderVideoSource();
    } else if (msg.type === "time") {
      state.popout.time = msg.time || 0;
      state.popout.duration = msg.duration || 0;
      state.popout.paused = !!msg.paused;
    } else if (msg.type === "closed") {
      reclaimPopout();
    }
  }

  function reclaimPopout() {
    stopPopoutHandshake();
    const t = state.popout.time || 0;
    state.popout.win = null;
    state.popout.ready = false;
    state.popout.loaded = false;
    if (state.videoKind === "file" && $("video")) {
      $("video").classList.remove("hidden");
      $("video").currentTime = t;
    } else if (state.videoKind === "youtube" && state.ytPlayer) {
      $("ytHost").classList.remove("hidden");
      try { state.ytPlayer.seekTo(t, true); } catch { /* ignore */ }
    }
    renderVideoSource();
    toast("Video tornato qui");
  }

  function openPopout() {
    if (state.mode !== "video") { toast("Passa a modalità Video"); return; }
    const ready = (state.videoKind === "file" && (state.videoFile || state.videoUrl))
      || (state.videoKind === "youtube" && state.ytUrl);
    if (!ready) { toast("Carica prima un video"); return; }
    stopPopoutHandshake();
    state.popout.ready = false;
    state.popout.loaded = false;
    state.popout.time = getMediaTime();
    mediaPause();
    const url = (location.protocol === "http:" || location.protocol === "https:")
      ? `${location.origin}/player.html?v=2`
      : "http://127.0.0.1:8765/player.html?v=2";
    const win = window.open(url, "fmpPlayer", "width=1280,height=720,menubar=no,toolbar=no,location=no,status=no");
    if (!win) {
      toast("Popup bloccato: clicca di nuovo «Apri video su altra finestra»");
      return;
    }
    state.popout.win = win;
    try { win.focus(); } catch { /* ignore */ }
    startPopoutHandshake();
    toast("Se il video non compare, clicca Play nella nuova finestra");
  }

  function fullscreenHere() {
    const el = $("mediaWrap");
    if (!el || !el.requestFullscreen) { toast("Fullscreen non supportato"); return; }
    if (document.fullscreenElement) {
      document.exitFullscreen().catch(() => {});
      return;
    }
    el.requestFullscreen().catch(() => toast("Fullscreen rifiutato"));
  }

  function apiUrl(path) {
    if (location.protocol === "http:" || location.protocol === "https:") {
      return `${location.origin}${path}`;
    }
    return `http://127.0.0.1:8765${path}`;
  }

  function setPushStatus(text, kind) {
    const el = $("pushStatus");
    el.textContent = text;
    el.className = "push-status" + (kind ? " " + kind : "");
  }

  async function loadPartiteList() {
    const sel = $("pushPartita");
    sel.innerHTML = `<option value="">— nuova partita —</option>`;
    try {
      const res = await fetch(apiUrl("/api/partite"));
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || res.statusText);
      for (const p of data.partite || []) {
        const opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = `${p.data || ""} — ${p.avversario || ""} — ${p.categoria || ""} (${p.id})`;
        opt.dataset.avversario = p.avversario || "";
        opt.dataset.data = p.data || "";
        opt.dataset.competizione = p.competizione || "";
        opt.dataset.categoria = p.categoria || "Prima Squadra";
        opt.dataset.yt = p.yt_link || "";
        sel.appendChild(opt);
      }
      setPushStatus(`Trovate ${(data.partite || []).length} partite su ${data.tables ? data.tables.partite : "DB"}`, "ok");
    } catch (err) {
      setPushStatus("Serve python app/tagger/serve.py — " + (err.message || err), "err");
    }
  }

  async function refreshPushInfo() {
    $("pushCountAll").textContent = String(state.events.length);
    $("pushCountSel").textContent = String(state.selected.length);
    const id = $("pushPartita").value;
    if (!id) {
      $("pushMatchInfo").textContent = "Compila avversario e data, poi Crea partita oppure Carica (crea e invia).";
      return;
    }
    try {
      const res = await fetch(apiUrl("/api/eventi-count?partita_id=" + encodeURIComponent(id)));
      const data = await res.json();
      $("pushMatchInfo").textContent = `Partita ${id}: ${data.count || 0} eventi già nel DB.`;
    } catch {
      $("pushMatchInfo").textContent = `Partita ${id}`;
    }
  }

  function fillPushFormFromSession() {
    $("pushAvversario").value = state.matchName || "";
    $("pushData").value = state.matchDate || todayInput();
    $("pushYt").value = state.ytUrl || "";
  }

  function togglePush(on) {
    const hide = on === false ? true : on === true ? false : !$("pushOverlay").classList.contains("hidden");
    $("pushOverlay").classList.toggle("hidden", hide);
    if (hide) return;
    fillPushFormFromSession();
    refreshPushInfo();
    loadPartiteList().then(refreshPushInfo);
  }

  async function createPartitaFromForm() {
    const body = {
      data: $("pushData").value,
      avversario: $("pushAvversario").value.trim(),
      competizione: $("pushCompetizione").value.trim(),
      categoria: $("pushCategoria").value.trim() || "Prima Squadra",
      yt_link: $("pushYt").value.trim(),
    };
    setPushStatus("Creo la partita…");
    const res = await fetch(apiUrl("/api/partite"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "creazione fallita");
    await loadPartiteList();
    $("pushPartita").value = data.partita.id;
    return data.partita;
  }

  function eventsForPush() {
    return $("pushScopeSel").checked ? selectedEvents() : sortedEvents();
  }

  async function pushToSupabase() {
    const rows = eventsForPush();
    if (!rows.length) { setPushStatus("Nessun evento da caricare", "err"); return; }
    const btn = $("btnDoPush");
    btn.disabled = true;
    setPushStatus("Invio in corso…");
    try {
      let partitaId = $("pushPartita").value;
      const create = (!partitaId) ? {
        data: $("pushData").value,
        avversario: $("pushAvversario").value.trim(),
        competizione: $("pushCompetizione").value.trim(),
        categoria: $("pushCategoria").value.trim() || "Prima Squadra",
        yt_link: $("pushYt").value.trim(),
      } : null;
      if (create && (!create.data || !create.avversario)) {
        throw new Error("Per una nuova partita servono data e avversario");
      }
      const res = await fetch(apiUrl("/api/push"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          partita_id: partitaId,
          create,
          replace: $("pushReplace").checked,
          data: $("pushData").value || state.matchDate,
          events: rows,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "push fallito");
      let msg = `OK: ${data.inserted} eventi su ${data.partita_id}`;
      if (data.deleted) msg += ` (sostituiti ${data.deleted})`;
      if (data.failed) {
        msg += `\nFalliti ${data.failed}`;
        for (const err of data.errors || []) {
          msg += `\n- ${err.posizione || "?"} ${err.evento || ""}: ${err.error}`;
        }
        setPushStatus(msg, "err");
      } else {
        setPushStatus(msg, "ok");
      }
      toast(data.failed ? `Inviati ${data.inserted}, errori ${data.failed}` : `Inviati ${data.inserted} eventi`);
      await loadPartiteList();
      $("pushPartita").value = data.partita_id;
      refreshPushInfo();
    } catch (err) {
      setPushStatus(String(err.message || err), "err");
    } finally {
      btn.disabled = false;
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

  function fillSettingsForm() {
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
        <button type="button" class="danger-ghost" data-del="${esc(d.id)}" title="Rimuovi">×</button>
      </div>`
    ).join("");
    if ($("cfgEsiti")) $("cfgEsiti").value = esitiText();
    if ($("cfgZone")) $("cfgZone").value = zoneText();
  }

  function readSettingsForm() {
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
    for (const def of EVENT_DEFS) {
      def.shortcut = state.shortcuts[def.id] || "";
      def.preroll = prerollFor(def.id);
      def.duration = durationFor(def.id);
    }
    if ($("cfgEsiti")) ESITI_BY_EVENT = parseEsiti($("cfgEsiti").value);
    if ($("cfgZone")) ZONE_DEFS = parseZone($("cfgZone").value);
  }

  function toggleSettings(on) {
    const hide = on === false ? true : on === true ? false : !$("settingsOverlay").classList.contains("hidden");
    $("settingsOverlay").classList.toggle("hidden", hide);
    if (hide) return;
    fillSettingsForm();
  }

  async function saveSettings() {
    readSettingsForm();
    persist();
    renderAll();
    try {
      await saveDiskConfig();
      toast("Impostazioni salvate in app/tagger/config/");
    } catch (err) {
      toast("Salvate in sessione. Per il disco avvia serve.py: " + (err.message || err));
    }
    toggleSettings(false);
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
      state.filterTypes = [];
      resetClock();
      persist();
      renderAll();
      toast("Sessione vuota");
    };
    $("btnSaveSession").onclick = () => { closeMenus(); saveSessionFile(); };
    $("btnLoadSession").onclick = () => { closeMenus(); $("fileSession").click(); };
    $("fileSession").onchange = (e) => { const f = e.target.files[0]; if (f) loadSessionFile(f); e.target.value = ""; };

    function closeMenus() {
      for (const id of ["sessionMenu", "exportMenu", "dbMenu", "filterEventoMenu"]) {
        const el = $(id);
        if (el) el.classList.add("hidden");
      }
    }
    function toggleMenu(menuId, e) {
      e.stopPropagation();
      const menu = $(menuId);
      const was = !menu.classList.contains("hidden");
      closeMenus();
      if (!was) menu.classList.remove("hidden");
    }
    $("btnSessionMenu").onclick = (e) => toggleMenu("sessionMenu", e);
    $("btnExportMenu").onclick = (e) => toggleMenu("exportMenu", e);
    $("btnDbMenu").onclick = (e) => toggleMenu("dbMenu", e);
    document.addEventListener("click", closeMenus);
    for (const id of ["sessionWrap", "exportWrap", "dbWrap", "filterEventoWrap"]) {
      const el = $(id);
      if (el) el.addEventListener("click", (e) => e.stopPropagation());
    }

    $("btnExport").onclick = () => { closeMenus(); exportCsv(); };
    $("btnExportSel").onclick = () => {
      closeMenus();
      const list = selectedEvents();
      if (!list.length) { toast("Seleziona almeno un evento"); return; }
      exportCsv("selezione", list);
    };
    $("btnExportClips").onclick = () => { closeMenus(); exportClipJson(); };
    $("btnExportM3u").onclick = () => { closeMenus(); exportM3u(); };
    $("btnExportFfmpeg").onclick = () => { closeMenus(); exportFfmpeg(); };
    $("btnPdf").onclick = () => { closeMenus(); generatePdf(); };
    $("btnPushDb").onclick = () => { closeMenus(); togglePush(true); };
    $("btnClosePush").onclick = () => togglePush(false);
    $("btnCreatePartita").onclick = () => {
      createPartitaFromForm().then((row) => {
        setPushStatus(`Partita creata: ${row.id}`, "ok");
        refreshPushInfo();
      }).catch((err) => setPushStatus(String(err.message || err), "err"));
    };
    $("btnDoPush").onclick = () => pushToSupabase();
    $("pushPartita").onchange = () => {
      const opt = $("pushPartita").selectedOptions[0];
      if (opt && opt.value) {
        $("pushAvversario").value = opt.dataset.avversario || "";
        $("pushData").value = opt.dataset.data || "";
        $("pushCompetizione").value = opt.dataset.competizione || "";
        $("pushCategoria").value = opt.dataset.categoria || "Prima Squadra";
        $("pushYt").value = opt.dataset.yt || "";
      } else {
        fillPushFormFromSession();
      }
      refreshPushInfo();
    };
    $("btnImport").onclick = () => { closeMenus(); $("fileCsv").click(); };
    $("fileCsv").onchange = (e) => { const f = e.target.files[0]; if (f) importCsvFile(f); e.target.value = ""; };
    $("btnSettings").onclick = () => toggleSettings(true);
    $("btnCloseSettings").onclick = () => toggleSettings(false);
    $("btnSaveSettings").onclick = saveSettings;
    $("btnResetShortcuts").onclick = () => {
      EVENT_DEFS = BUILTIN_EVENT_DEFS.map((e) => ({ ...e }));
      ESITI_BY_EVENT = JSON.parse(JSON.stringify(BUILTIN_ESITI));
      ZONE_DEFS = BUILTIN_ZONES.map((z) => ({ ...z }));
      state.players = [...DEFAULT_PLAYERS];
      state.keepers = [...DEFAULT_KEEPERS];
      state.stickyKeeper = DEFAULT_KEEPERS[0] || "";
      syncEventMaps();
      fillSettingsForm();
    };
    if ($("btnAddEvent")) {
      $("btnAddEvent").onclick = () => {
        readSettingsForm();
        const id = ($("newEventId").value || "").trim();
        if (!id) { toast("Nome evento mancante"); return; }
        if (EVENT_DEFS.some((d) => d.id === id)) { toast("Evento già presente"); return; }
        EVENT_DEFS.push({
          id,
          shortcut: "",
          color: $("newEventColor").value || "gray",
          group: ($("newEventGroup").value || "Altro").trim() || "Altro",
          preroll: 5,
          duration: 10,
        });
        syncEventMaps();
        $("newEventId").value = "";
        fillSettingsForm();
      };
    }
    $("shortcutList").addEventListener("click", (e) => {
      const btn = e.target.closest("[data-del]");
      if (!btn) return;
      if (EVENT_DEFS.length <= 1) { toast("Serve almeno un evento"); return; }
      readSettingsForm();
      EVENT_DEFS = EVENT_DEFS.filter((d) => d.id !== btn.dataset.del);
      syncEventMaps();
      fillSettingsForm();
    });
    $("btnToggleSync").onclick = () => {
      state.syncOpen = !state.syncOpen;
      persist();
      renderFolds();
    };
    $("btnToggleSource").onclick = () => {
      state.sourceOpen = !state.sourceOpen;
      persist();
      renderFolds();
    };
    $("btnToggleControls").onclick = () => {
      state.controlsOpen = !state.controlsOpen;
      persist();
      renderFolds();
    };
    $("btnTogglePanel").onclick = () => {
      state.panelOpen = state.panelOpen === false;
      persist();
      renderFolds();
    };
    if ($("btnDockPanel")) {
      $("btnDockPanel").onclick = () => {
        state.panelOpen = true;
        persist();
        renderFolds();
      };
    }
    $("btnToggleEvents").onclick = () => {
      state.eventsOpen = state.eventsOpen === false;
      persist();
      renderFolds();
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
    $("btnFilterEvento").onclick = (e) => {
      e.stopPropagation();
      const menu = $("filterEventoMenu");
      const was = !menu.classList.contains("hidden");
      closeMenus();
      if (!was) {
        renderTypeFilter();
        placeTypeMenu();
        menu.classList.remove("hidden");
      }
    };
    $("filterEventoMenu").addEventListener("click", (e) => {
      const all = e.target.closest("[data-types='all']");
      if (!all) return;
      state.filterTypes = [];
      persist();
      renderTable();
    });
    $("filterEventoMenu").addEventListener("change", (e) => {
      const inp = e.target.closest("input[data-type]");
      if (!inp) return;
      const t = inp.dataset.type;
      const set = new Set(state.filterTypes || []);
      if (inp.checked) set.add(t);
      else set.delete(t);
      state.filterTypes = [...set];
      persist();
      renderTable();
    });
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
      state.sourceOpen = true;
      persist();
      renderFolds();
      $("ytUrl").focus();
      $("ytUrl").select();
    };
    $("btnReattach").onclick = () => $("fileVideo").click();

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
    $("btnPopout").onclick = openPopout;
    $("btnFullscreen").onclick = fullscreenHere;
    if ($("btnFocusPopout")) {
      $("btnFocusPopout").onclick = () => {
        if (popoutOpen()) state.popout.win.focus();
        else toast("Nessuna finestra video aperta");
      };
    }

    $("timeline").addEventListener("click", (e) => {
      const mk = e.target.closest(".marker");
      if (mk) { selectRow(mk.dataset.id); return; }
      const dur = getMediaDuration();
      if (!dur) return;
      const rect = $("timeline").getBoundingClientRect();
      mediaSeek(((e.clientX - rect.left) / rect.width) * dur);
    });

    document.addEventListener("keydown", onKey);
    window.addEventListener("beforeunload", () => { persist(); flushDiskSession(); });
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "hidden") flushDiskSession();
    });
    $("video").addEventListener("loadedmetadata", () => renderTimeline());
    if (playerBus) playerBus.onmessage = (e) => onPlayerMsg(e.data);
    window.addEventListener("message", (e) => onPlayerMsg(e.data));
    bindSplitters();
    window.addEventListener("resize", () => applyLayout());
    if (window.visualViewport) {
      window.visualViewport.addEventListener("resize", () => applyLayout());
    }
    $("app").focus();
  }

  function loop() {
    if (state.popout.win && state.popout.win.closed) reclaimPopout();
    updateClocks();
    requestAnimationFrame(loop);
  }

  restore();
  bind();
  applyLayout();
  renderAll();
  resumeVideoSource();
  loop();
  loadDiskConfig().then(() => loadDiskSession()).then(() => renderAll());
})();
