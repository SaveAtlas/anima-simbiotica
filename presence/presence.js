/* ANIMA presence — day stream, invite, share, Ask-me→node (S12) */
(function () {
  "use strict";

  var STORE_KEY = "anima-presence-v13";
  var NODE_KEY = "anima-refnode-base";

  function uid(prefix) {
    return (prefix || "id") + "-" + Math.random().toString(36).slice(2, 10);
  }

  function nowIso() {
    return new Date().toISOString();
  }

  function loadState() {
    try {
      var raw = localStorage.getItem(STORE_KEY);
      if (raw) return JSON.parse(raw);
    } catch (e) {}
    return seedState();
  }

  function saveState(state) {
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify(state));
    } catch (e) {}
  }

  function seedState() {
    var state = {
      version: "0.12.0-sketch",
      you: { label: "Still you", note: "Your keys, memory, and leave path — intact." },
      day: [
        {
          id: "day-place-1",
          kind: "place",
          title: "Watershed garden",
          body: "Moisture steady · flow quiet · resting well",
          tone: "care",
          at: nowIso(),
        },
        {
          id: "day-pet-1",
          kind: "pet",
          title: "Companion in your care",
          body: "Rest ok · gentle day · welfare watched with love",
          tone: "care",
          at: nowIso(),
        },
        {
          id: "day-person-1",
          kind: "person",
          title: "Someone you keep close",
          body: "Check-in open · no rush · present when you are",
          tone: "care",
          at: nowIso(),
        },
        {
          id: "day-helper-1",
          kind: "helper",
          title: "Local care node",
          body: "Offline-first helper · sensing place + companion · invited",
          tone: "helper",
          at: nowIso(),
        },
      ],
      peers: [],
      events: [],
      grants: [],
    };
    saveState(state);
    return state;
  }

  function kindLabel(kind) {
    return (
      {
        person: "Person",
        pet: "Pet",
        place: "Place",
        helper: "Helper",
        twin: "Twin",
        robot: "Robot",
        ai: "AI",
      }[kind] || "Being"
    );
  }

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderDay(state) {
    var root = document.getElementById("dayStream");
    if (!root) return;
    root.innerHTML = "";
    state.day.forEach(function (card) {
      var el = document.createElement("article");
      el.className = "being day-card kind-" + (card.kind || "care");
      el.setAttribute("data-id", card.id);
      el.innerHTML =
        '<div class="row">' +
        "<div>" +
        '<p class="kind">' +
        kindLabel(card.kind) +
        "</p>" +
        "<h3>" +
        escapeHtml(card.title) +
        "</h3>" +
        "<p>" +
        escapeHtml(card.body) +
        "</p>" +
        "</div>" +
        '<span class="pulse" title="present" aria-hidden="true"></span>' +
        "</div>";
      root.appendChild(el);
    });
  }

  function renderPeers(state) {
    var root = document.getElementById("peerList");
    if (!root) return;
    root.innerHTML = "";
    if (!state.peers.length) {
      var empty = document.createElement("div");
      empty.className = "being slot-empty";
      empty.innerHTML =
        "<h3>Twin &amp; helpers slot</h3>" +
        "<p>Invite a continuing self, AI, robot, or care tool as a peer being. Products plug in here — the habitat stays wider than any one of them.</p>";
      root.appendChild(empty);
      return;
    }
    state.peers.forEach(function (peer) {
      var el = document.createElement("article");
      el.className = "being peer-card";
      el.innerHTML =
        '<div class="row">' +
        "<div>" +
        '<p class="kind">' +
        kindLabel(peer.kind) +
        " · invited</p>" +
        "<h3>" +
        escapeHtml(peer.label) +
        "</h3>" +
        "<p>" +
        escapeHtml(peer.note || "Peer under your keys · willing link sketch") +
        "</p>" +
        "</div>" +
        '<span class="pulse" title="invited" aria-hidden="true"></span>' +
        "</div>";
      root.appendChild(el);
    });
  }

  function openSheet(id) {
    var el = document.getElementById(id);
    if (!el) return;
    el.classList.add("open");
    el.setAttribute("aria-hidden", "false");
  }

  function closeSheet(id) {
    var el = document.getElementById(id);
    if (!el) return;
    el.classList.remove("open");
    el.setAttribute("aria-hidden", "true");
  }

  function toast(msg) {
    var el = document.getElementById("toast");
    if (!el) return;
    el.textContent = msg;
    el.classList.add("show");
    clearTimeout(toast._t);
    toast._t = setTimeout(function () {
      el.classList.remove("show");
    }, 2400);
  }

  function getNodeBase() {
    var params = new URLSearchParams(location.search);
    var q = params.get("node");
    if (q) {
      try {
        localStorage.setItem(NODE_KEY, q);
      } catch (e) {}
      return q.replace(/\/$/, "");
    }
    try {
      var stored = localStorage.getItem(NODE_KEY);
      if (stored) return stored.replace(/\/$/, "");
    } catch (e) {}
    var input = document.getElementById("nodeBase");
    if (input && input.value.trim()) return input.value.trim().replace(/\/$/, "");
    return "";
  }

  function updateNodeStatus() {
    var el = document.getElementById("nodeStatus");
    var base = getNodeBase();
    if (!el) return;
    if (!base) {
      el.textContent = "Ask me · demo mode (set a node URL anytime)";
      el.className = "node-status muted";
      return;
    }
    el.textContent = "Node hook: " + base + " · probing…";
    el.className = "node-status";
    fetch(base + "/anima/health", { method: "GET", mode: "cors" })
      .then(function (r) {
        if (!r.ok) throw new Error("health " + r.status);
        el.textContent = "Node reachable · Ask me can post challenge sketches";
        el.className = "node-status ok";
      })
      .catch(function () {
        el.textContent = "Node set but unreachable · Ask me stays demo until it answers";
        el.className = "node-status warn";
      });
  }

  function pushToNodeIfAvailable(payload) {
    var base = getNodeBase();
    if (!base) return Promise.resolve({ mode: "local" });
    var envelope = {
      kind: payload.kind || "presence.share",
      event_id: payload.id || uid("evt"),
      emitted_at: payload.at || nowIso(),
      payload: payload,
      source: "presence-shell",
      mode: "sketch",
    };
    return fetch(base + "/anima/event", {
      method: "POST",
      mode: "cors",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(envelope),
    })
      .then(function (r) {
        return r.json().catch(function () {
          return { ok: r.ok, status: r.status };
        });
      })
      .then(function (body) {
        toast("Posted sketch to node");
        return body;
      })
      .catch(function () {
        return { mode: "local-fallback" };
      });
  }

  function invitePeer(state) {
    var kind = document.getElementById("inviteKind").value;
    var label = (document.getElementById("inviteLabel").value || "").trim();
    var note = (document.getElementById("inviteNote").value || "").trim();
    if (!label) {
      label =
        kind === "twin"
          ? "Your twin"
          : kind === "robot"
          ? "Care robot"
          : kind === "ai"
          ? "AI helper"
          : "Invited peer";
    }
    var peer = {
      id: uid("peer"),
      kind: kind,
      label: label,
      note: note || "Generic peer card · under your invitation",
      invited_at: nowIso(),
    };
    state.peers.unshift(peer);
    state.day.unshift({
      id: uid("day"),
      kind: kind === "twin" ? "twin" : "helper",
      title: label + " arrived",
      body: "Invited into your world · peer card ready · habitat stays open",
      tone: "invite",
      at: nowIso(),
    });
    state.events.unshift({
      id: uid("evt"),
      kind: "presence.invite",
      peer_id: peer.id,
      peer_kind: peer.kind,
      label: peer.label,
      at: nowIso(),
      mode: "local-sketch",
    });
    saveState(state);
    renderAll(state);
    closeSheet("inviteSheet");
    toast("Invited · peer lives in your world now");
  }

  function shareSketch(state) {
    var what = (document.getElementById("shareWhat").value || "").trim() || "A care note from today";
    var scope = document.getElementById("shareScope").value;
    var grant = document.getElementById("shareGrant").checked;
    var evt = {
      id: uid("evt"),
      kind: "presence.share",
      what: what,
      scope: scope,
      at: nowIso(),
      mode: "local-sketch",
    };
    state.events.unshift(evt);
    if (grant) {
      var g = {
        id: uid("grant"),
        kind: "consent.grant.sketch",
        scope: scope,
        action_class: "memory.read." + scope,
        attenuations: ["no_expand", "local_only"],
        what: what,
        at: nowIso(),
        mode: "local-sketch",
      };
      state.grants.unshift(g);
      evt.grant_id = g.id;
    }
    state.day.unshift({
      id: uid("day"),
      kind: "person",
      title: "Shared · " + scope,
      body: what + (grant ? " · grant sketch attached" : " · passed without grant"),
      tone: "share",
      at: nowIso(),
    });
    saveState(state);
    renderAll(state);
    closeSheet("shareSheet");
    toast(grant ? "Share + grant sketch saved locally" : "Share event saved locally");
    pushToNodeIfAvailable(evt);
  }

  function renderAll(state) {
    renderDay(state);
    renderPeers(state);
    var count = document.getElementById("dayCount");
    if (count) count.textContent = String(state.day.length);
  }

  function bind(state) {
    var inviteBtn = document.getElementById("btnInvite");
    var shareBtn = document.getElementById("btnShare");
    var askBtn = document.getElementById("btnAsk");
    if (inviteBtn)
      inviteBtn.addEventListener("click", function () {
        openSheet("inviteSheet");
      });
    if (shareBtn)
      shareBtn.addEventListener("click", function () {
        openSheet("shareSheet");
      });
    if (askBtn)
      askBtn.addEventListener("click", function () {
        var base = getNodeBase();
        var q = new URLSearchParams({
          label: "Serious care",
          prompt: "Allow a serious step in your living place?",
          action: "habitat.irreversible.change",
        });
        if (base) q.set("node", base);
        location.href = "challenge.html?" + q.toString();
      });

    document.querySelectorAll("[data-close]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        closeSheet(btn.getAttribute("data-close"));
      });
    });

    var inviteForm = document.getElementById("inviteForm");
    if (inviteForm)
      inviteForm.addEventListener("submit", function (e) {
        e.preventDefault();
        invitePeer(state);
      });

    var shareForm = document.getElementById("shareForm");
    if (shareForm)
      shareForm.addEventListener("submit", function (e) {
        e.preventDefault();
        shareSketch(state);
      });

    var saveNode = document.getElementById("btnSaveNode");
    if (saveNode)
      saveNode.addEventListener("click", function () {
        var input = document.getElementById("nodeBase");
        var v = (input && input.value.trim()) || "";
        try {
          if (v) localStorage.setItem(NODE_KEY, v);
          else localStorage.removeItem(NODE_KEY);
        } catch (e) {}
        updateNodeStatus();
        toast(v ? "Node URL saved" : "Node URL cleared · demo mode");
      });

    var reset = document.getElementById("btnResetDemo");
    if (reset)
      reset.addEventListener("click", function () {
        try {
          localStorage.removeItem(STORE_KEY);
        } catch (e) {}
        var fresh = seedState();
        renderAll(fresh);
        toast("Day stream reset to seed world");
        location.reload();
      });
  }

  
  function setStatus(id, text) {
    var el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  function runThreeBeingDay() {
    var log = document.getElementById("threeScriptLog");
    if (log) log.innerHTML = "";
    function line(msg) {
      if (!log) return;
      var li = document.createElement("li");
      li.textContent = msg;
      log.appendChild(li);
    }
    setStatus("statusRobot", "Sensing…");
    line("1 · Robot senses the place");
    setTimeout(function () {
      setStatus("statusRobot", "Sensed · moisture ok · path clear");
      setStatus("statusAI", "Remembering under grant…");
      line("2 · AI remembers the reading for later care");
      setTimeout(function () {
        setStatus("statusAI", "Remembered · under your grant");
        setStatus("statusHuman", "Ask me — waiting for your yes");
        line("3 · Human Ask me before the robot acts");
        setTimeout(function () {
          setStatus("statusHuman", "You said yes · water once");
          line("4 · Human allows — water once, then report");
          setStatus("statusRobot", "Acting under your yes…");
          setTimeout(function () {
            setStatus("statusRobot", "Acted · watered · reported");
            setStatus("statusHuman", "Present · day shared");
            line("5 · Robot acts · three beings, one day — PASS");
            toast("Three beings, one day — shared.");
            var state = loadState();
            state.day.unshift({
              id: uid("day-s13"),
              kind: "helper",
              title: "Three beings · one day",
              body: "Robot sensed · AI remembered · you said yes · robot acted",
              tone: "care",
              at: nowIso(),
            });
            saveState(state);
            renderDay(state);
          }, 700);
        }, 700);
      }, 700);
    }, 500);
  }

  function bindThreeDay() {
    var btn = document.getElementById("btnThreeDay");
    if (btn) btn.addEventListener("click", runThreeBeingDay);
  }

  document.addEventListener("DOMContentLoaded", function () {
    bindThreeDay();
    var state = loadState();
    var nodeInput = document.getElementById("nodeBase");
    if (nodeInput) {
      try {
        nodeInput.value = localStorage.getItem(NODE_KEY) || "";
      } catch (e) {}
    }
    renderAll(state);
    bind(state);
    updateNodeStatus();
  });

  window.AnimaPresence = {
    loadState: loadState,
    getNodeBase: getNodeBase,
    pushToNodeIfAvailable: pushToNodeIfAvailable,
  };
})();
