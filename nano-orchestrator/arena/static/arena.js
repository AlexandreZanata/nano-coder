(() => {
  const els = {
    status: document.getElementById("status-pill"),
    refresh: document.getElementById("btn-refresh"),
    auto: document.getElementById("auto-refresh"),
    proposalPath: document.getElementById("proposal-path"),
    fileList: document.getElementById("file-list"),
    runList: document.getElementById("run-list"),
    stageTitle: document.getElementById("stage-title"),
    stageSub: document.getElementById("stage-sub"),
    tabPreview: document.getElementById("tab-preview"),
    tabSource: document.getElementById("tab-source"),
    openSite: document.getElementById("open-site"),
    preview: document.getElementById("preview"),
    source: document.getElementById("source"),
    sourceCode: document.querySelector("#source code"),
    verdictBar: document.getElementById("verdict-bar"),
    packageSummary: document.getElementById("package-summary"),
    runSummary: document.getElementById("run-summary"),
    runJson: document.getElementById("run-json"),
    runJsonCode: document.querySelector("#run-json code"),
  };

  let state = {
    overview: null,
    selectedFile: null,
    selectedRun: null,
    mode: "preview",
    fileCache: {},
  };

  async function fetchJson(url) {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error(`${res.status} ${url}`);
    return res.json();
  }

  function setStatus(ok, text) {
    els.status.textContent = text;
    els.status.classList.toggle("ok", !!ok);
    els.status.classList.toggle("bad", !ok);
  }

  function card(k, v) {
    const div = document.createElement("div");
    div.className = "card";
    div.innerHTML = `<div class="k">${k}</div><div class="v">${v}</div>`;
    return div;
  }

  function fileVerdict(name, packageJson) {
    if (!packageJson || !packageJson.files) return null;
    return packageJson.files.find((f) => f.path === name) || null;
  }

  function siteUrl(name) {
    return `/site/${encodeURIComponent(name)}`;
  }

  function renderFiles(overview) {
    els.fileList.innerHTML = "";
    els.proposalPath.textContent = overview.roots.proposal;
    if (!overview.files.length) {
      els.fileList.innerHTML = `<li class="muted">No proposal files yet. Run make nano-large-site-pro</li>`;
      return;
    }
    for (const file of overview.files) {
      const li = document.createElement("li");
      const btn = document.createElement("button");
      btn.type = "button";
      const verdict = fileVerdict(file.name, overview.package);
      const badge =
        verdict == null
          ? ""
          : `<span class="badge ${verdict.passed ? "pass" : "fail"}">${
              verdict.passed ? "pass" : "fail"
            }</span>`;
      btn.innerHTML = `${file.name}${badge}<span class="meta">${file.bytes} B · ${file.ext}</span>`;
      if (state.selectedFile === file.name) btn.classList.add("active");
      btn.addEventListener("click", () => selectFile(file.name));
      li.appendChild(btn);
      els.fileList.appendChild(li);
    }
  }

  function renderRuns(overview) {
    els.runList.innerHTML = "";
    if (!overview.runs.length) {
      els.runList.innerHTML = `<li class="muted">No run JSON under benchmarks/runs/</li>`;
      return;
    }
    for (const run of overview.runs) {
      const li = document.createElement("li");
      const btn = document.createElement("button");
      btn.type = "button";
      btn.innerHTML = `${run.name}<span class="meta">${new Date(
        run.mtime * 1000
      ).toLocaleString()}</span>`;
      if (state.selectedRun === run.name) btn.classList.add("active");
      btn.addEventListener("click", () => selectRun(run.name));
      li.appendChild(btn);
      els.runList.appendChild(li);
    }
  }

  function renderPackage(overview) {
    els.packageSummary.innerHTML = "";
    const pkg = overview.package;
    if (!pkg || pkg.error) {
      els.packageSummary.appendChild(
        card("status", pkg && pkg.error ? pkg.error : "missing package.json")
      );
      return;
    }
    const passed = (pkg.files || []).filter((f) => f.passed).length;
    const total = (pkg.files || []).length;
    const openable = (pkg.openable && pkg.openable.openable) || [];
    els.packageSummary.append(
      card("passed", `${passed}/${total}`),
      card("openable", openable.length ? openable.join(", ") : "—"),
      card("peak VRAM", pkg.peak_vram_mb == null ? "—" : `${pkg.peak_vram_mb} MB`),
      card("human_gate", String(pkg.human_gate)),
      card("auto_persist", String(pkg.auto_persist))
    );
  }

  function showMode() {
    const isHtml =
      state.selectedFile &&
      (state.selectedFile.endsWith(".html") || state.selectedFile.endsWith(".htm"));
    if (state.mode === "preview" && isHtml) {
      els.preview.classList.remove("hidden");
      els.source.classList.add("hidden");
      els.tabPreview.classList.add("active");
      els.tabSource.classList.remove("active");
    } else {
      els.preview.classList.add("hidden");
      els.source.classList.remove("hidden");
      els.tabPreview.classList.toggle("active", state.mode === "preview" && isHtml);
      els.tabSource.classList.add("active");
    }
  }

  async function selectFile(name) {
    state.selectedFile = name;
    renderFiles(state.overview);
    els.stageTitle.textContent = name;
    const verdict = fileVerdict(name, state.overview.package);
    if (verdict) {
      els.verdictBar.classList.remove("hidden");
      els.verdictBar.innerHTML = `
        <span>task: <strong>${verdict.task_id}</strong></span>
        <span>lang: <strong>${verdict.language}</strong></span>
        <span>score: <strong>${verdict.score}</strong></span>
        <span class="badge ${verdict.passed ? "pass" : "fail"}">${
          verdict.passed ? "passed" : "failed"
        }</span>
        <span>escalate: <strong>${verdict.escalate_to_human}</strong></span>
      `;
      els.stageSub.textContent = "Served from /site/ so CSS + nav resolve";
    } else {
      els.verdictBar.classList.add("hidden");
      els.stageSub.textContent = "";
    }

    let payload = state.fileCache[name];
    if (!payload) {
      payload = await fetchJson(`/api/file?name=${encodeURIComponent(name)}`);
      state.fileCache[name] = payload;
    }
    els.sourceCode.textContent = payload.content || "";
    if (name.endsWith(".html") || name.endsWith(".htm")) {
      els.preview.removeAttribute("srcdoc");
      els.preview.src = siteUrl(name);
      els.openSite.href = siteUrl(name);
      state.mode = "preview";
    } else {
      state.mode = "source";
      els.preview.removeAttribute("src");
      els.preview.removeAttribute("srcdoc");
      els.openSite.href = "/site/index.html";
    }
    showMode();
  }

  function orchLabel(orch) {
    if (!orch || typeof orch !== "object") return "—";
    if (orch.skipped) return "skipped";
    if (orch.ok === true) return `ok (${orch.count || "—"})`;
    if (orch.ok === false) return String(orch.error || "fail");
    return "—";
  }

  async function selectRun(name) {
    state.selectedRun = name;
    renderRuns(state.overview);
    const payload = await fetchJson(`/api/run?name=${encodeURIComponent(name)}`);
    const data = payload.data || {};
    els.runSummary.innerHTML = "";
    const passed = data.passed_count;
    const slots = data.slot_count;
    const peak = data.peak_vram_mb;
    const met = data.pass_bar && data.pass_bar.met;
    const orch = data.orchestrator || {};
    const openable = (data.openable && data.openable.openable) || [];
    els.runSummary.append(
      card("pass bar", met ? "MET" : "not met"),
      card("workers", passed == null ? "—" : `${passed}/${slots}`),
      card("peak VRAM", peak == null ? "—" : `${peak} MB`),
      card("orch", orchLabel(orch)),
      card("quality", data.quality_ok == null ? "—" : String(data.quality_ok)),
      card("openable pages", openable.length ? String(openable.length) : "—")
    );
    els.runJson.classList.remove("hidden");
    els.runJsonCode.textContent = JSON.stringify(data, null, 2);
  }

  async function refresh() {
    try {
      const overview = await fetchJson("/api/overview");
      state.overview = overview;
      state.fileCache = {};
      renderFiles(overview);
      renderRuns(overview);
      renderPackage(overview);
      const anyFail = ((overview.package && overview.package.files) || []).some(
        (f) => !f.passed
      );
      const openable =
        (overview.package &&
          overview.package.openable &&
          overview.package.openable.openable) ||
        [];
      setStatus(
        !anyFail &&
          overview.files.length > 0 &&
          (openable.length > 0 || !overview.package.openable),
        overview.files.length ? "live" : "empty"
      );
      if (state.selectedFile) {
        await selectFile(state.selectedFile);
      } else if (overview.files.length) {
        const preferred =
          overview.files.find((f) => f.name === "index.html") ||
          overview.files.find((f) => f.name.endsWith(".html")) ||
          overview.files[0];
        await selectFile(preferred.name);
      }
      if (!state.selectedRun) {
        const preferredRun =
          overview.runs.find((r) => r.name.includes("large_site_schedule_pro")) ||
          overview.runs.find((r) => r.name.includes("large_site")) ||
          overview.runs[0];
        if (preferredRun) await selectRun(preferredRun.name);
      }
    } catch (err) {
      setStatus(false, "error");
      console.error(err);
    }
  }

  els.refresh.addEventListener("click", refresh);
  els.tabPreview.addEventListener("click", () => {
    state.mode = "preview";
    showMode();
  });
  els.tabSource.addEventListener("click", () => {
    state.mode = "source";
    showMode();
  });

  setInterval(() => {
    if (els.auto.checked) refresh();
  }, 3000);

  refresh();
})();
