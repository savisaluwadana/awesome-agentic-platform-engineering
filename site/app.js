/* Awesome Agentic — lightweight README-driven directory. No frameworks required. */
(() => {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const els = {
    nav: $("#categoryNav"),
    list: $("#productList"),
    input: $("#projectSearch"),
    sort: $("#projectSort"),
    resultsLabel: $("#resultsLabel"),
    total: $("#directoryTotal"),
    projects: $("#heroProjectCount"),
    categories: $("#heroCategoryCount"),
    empty: $("#emptyState"),
    clear: $("#clearFilters"),
    spotlightName: $("#spotlightName"),
    spotlightDescription: $("#spotlightDescription"),
    spotlightLink: $("#spotlightLink"),
    shortcut: $("#searchShortcut"),
  };
  const state = { catalog: null, category: "All projects", query: "", sort: "curated" };
  const icons = {
    "Agent Frameworks & Orchestration": "✳",
    "Developer Platforms & Control Planes": "⬡",
    "MCP & Tool Infrastructure": "⌘",
    "GitOps & Delivery": "↗",
    "Observability & Evaluation": "◉",
    "Security & Policy": "◇"
  };

  const escapeHTML = (value) => String(value ?? "").replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[ch]);

  const safeURL = (value, fallback = "#") => {
    try {
      const url = new URL(value);
      return url.protocol === "https:" ? url.href : fallback;
    } catch {
      return fallback;
    }
  };
  const formatStars = (value) => Number.isInteger(value) && value >= 0
    ? Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 }).format(value)
    : null;

  function visibleProjects() {
    if (!state.catalog) return [];
    const query = state.query.trim().toLocaleLowerCase();
    const matching = state.catalog.projects.filter((project) => {
      const inCategory = state.category === "All projects" || state.category === project.category;
      const haystack = [project.name, project.description, project.category, project.repo, project.language]
        .filter(Boolean).join(" ").toLocaleLowerCase();
      return inCategory && (!query || query.split(/\s+/).every((part) => haystack.includes(part)));
    });
    if (state.sort === "stars") {
      matching.sort((a, b) => (b.stars ?? -1) - (a.stars ?? -1) || a.order - b.order);
    } else if (state.sort === "name") {
      matching.sort((a, b) => a.name.localeCompare(b.name));
    } else {
      matching.sort((a, b) => a.order - b.order);
    }
    return matching;
  }

  function renderCategories() {
    const { projects, categories } = state.catalog;
    const counts = Object.fromEntries(categories.map((category) => [
      category, projects.filter((project) => project.category === category).length
    ]));
    const options = [["All projects", projects.length], ...categories.map((category) => [category, counts[category]])];
    els.nav.innerHTML = options.map(([category, count]) => {
      const active = state.category === category;
      const icon = category === "All projects" ? "▦" : (icons[category] || "◎");
      return `<button type="button" class="category-button${active ? " active" : ""}"
        data-category="${escapeHTML(category)}" aria-pressed="${active}">
        <span class="category-name"><span class="category-icon" aria-hidden="true">${escapeHTML(icon)}</span><span>${escapeHTML(category)}</span></span>
        <span class="category-number">${count}</span></button>`;
    }).join("");
  }

  function cardMarkup(project, index) {
    const name = escapeHTML(project.name);
    const description = escapeHTML(project.description);
    const repoUrl = safeURL(project.repoUrl);
    const homepage = safeURL(project.homepage, repoUrl);
    const logo = safeURL(project.avatar);
    const stars = formatStars(project.stars);
    const tags = [project.category, project.language].filter(Boolean).slice(0, 2);
    const tagMarkup = tags.map((tag) => `<span class="meta-tag">${escapeHTML(tag)}</span>`).join("");
    const badge = project.category === "Agent Frameworks & Orchestration" || project.category === "MCP & Tool Infrastructure"
      ? '<span class="project-kind">Agent ecosystem</span>' : "";
    const starLabel = stars ? `${stars} GitHub stars` : "View on GitHub";
    const starIcon = '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="m12 2.7 2.9 5.9 6.5.9-4.7 4.6 1.1 6.5-5.8-3.1-5.8 3.1 1.1-6.5-4.7-4.6 6.5-.9L12 2.7Z" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/></svg>';
    return `<article class="product-card" style="animation-delay:${Math.min(index, 9) * 27}ms">
      <span class="product-rank" aria-label="Position ${index + 1}">${String(index + 1).padStart(2, "0")}</span>
      <a class="product-logo" href="${repoUrl}" target="_blank" rel="noopener noreferrer" aria-label="Open ${name} on GitHub">
        <img loading="lazy" src="${logo}" alt="" width="47" height="47" data-fallback="${escapeHTML(project.name.charAt(0).toUpperCase())}">
      </a>
      <div class="product-info">
        <div class="product-title-line"><h3><a href="${repoUrl}" target="_blank" rel="noopener noreferrer">${name}</a></h3>${badge}</div>
        <p class="product-description">${description}</p>
        <div class="card-meta">${tagMarkup}</div>
      </div>
      <div class="product-actions">
        <a class="star-pill${stars === null ? " no-stars" : ""}" href="${repoUrl}/stargazers" target="_blank" rel="noopener noreferrer" aria-label="${escapeHTML(starLabel)} for ${name}" title="${escapeHTML(starLabel)}">${starIcon}<span>${stars ?? "GitHub"}</span></a>
        <a class="visit-link" href="${homepage}" target="_blank" rel="noopener noreferrer" aria-label="Visit ${name} project website">Visit ↗</a>
      </div>
    </article>`;
  }

  function renderList() {
    const filtered = visibleProjects();
    const count = filtered.length;
    els.list.innerHTML = filtered.map(cardMarkup).join("");
    els.list.setAttribute("aria-busy", "false");
    els.empty.hidden = count !== 0;
    if (!count) {
      els.list.innerHTML = "";
    }
    const qualifier = state.category === "All projects" ? "across all categories" : `in ${state.category}`;
    els.resultsLabel.textContent = `Showing ${count} project${count === 1 ? "" : "s"} ${qualifier}`;
    els.total.textContent = `${state.catalog.total} open-source projects`;
    els.list.querySelectorAll("img[data-fallback]").forEach((img) => {
      img.addEventListener("error", () => {
        const text = document.createElement("span");
        text.textContent = img.dataset.fallback || "✳";
        img.replaceWith(text);
      }, { once: true });
    });
  }

  function renderSpotlight() {
    const { catalog } = state;
    const picked = catalog.projects.find((project) => project.id === catalog.featuredId)
      || catalog.projects[0];
    if (!picked) return;
    els.spotlightName.textContent = picked.name;
    els.spotlightDescription.textContent = picked.description;
    els.spotlightLink.href = safeURL(picked.homepage, safeURL(picked.repoUrl));
    els.spotlightLink.setAttribute("aria-label", `Explore ${picked.name}`);
  }

  function syncQueryParams() {
    const params = new URLSearchParams();
    if (state.category !== "All projects") params.set("category", state.category);
    if (state.query.trim()) params.set("q", state.query.trim());
    if (state.sort !== "curated") params.set("sort", state.sort);
    history.replaceState(null, "", location.pathname + (params.size ? "?" + params.toString() : "") + location.hash);
  }

  function update() {
    renderCategories();
    renderList();
    syncQueryParams();
  }

  els.nav.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-category]");
    if (!button || !state.catalog) return;
    state.category = button.dataset.category;
    update();
  });

  els.input.addEventListener("input", () => {
    state.query = els.input.value;
    if (state.catalog) update();
  });

  els.sort.addEventListener("change", () => {
    state.sort = els.sort.value;
    if (state.catalog) update();
  });

  els.clear.addEventListener("click", () => {
    state.query = "";
    state.category = "All projects";
    state.sort = "curated";
    els.input.value = "";
    els.sort.value = "curated";
    update();
    els.input.focus();
  });

  const mac = navigator.platform?.toLowerCase().includes("mac");
  if (!mac) els.shortcut.textContent = "Ctrl K";
  document.addEventListener("keydown", (event) => {
    const active = document.activeElement;
    const editing = active && (active.matches("input, textarea, select") || active.isContentEditable);
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
      event.preventDefault(); els.input.focus(); els.input.select();
    } else if (event.key === "/" && !editing && !event.metaKey && !event.ctrlKey && !event.altKey) {
      event.preventDefault(); els.input.focus();
    } else if (event.key === "Escape" && active === els.input) {
      els.input.blur();
    }
  });

  async function load() {
    try {
      const response = await fetch("./catalog.json", { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      if (!Array.isArray(data.projects) || !Array.isArray(data.categories)) {
        throw new Error("Catalog format is invalid");
      }
      state.catalog = data;
      const url = new URL(location.href);
      const requestedCategory = url.searchParams.get("category");
      state.category = data.categories.includes(requestedCategory) ? requestedCategory : "All projects";
      state.query = url.searchParams.get("q") || "";
      state.sort = ["curated", "stars", "name"].includes(url.searchParams.get("sort"))
        ? url.searchParams.get("sort") : "curated";
      els.input.value = state.query;
      els.sort.value = state.sort;
      els.projects.textContent = data.total.toLocaleString("en");
      els.categories.textContent = data.categories.length.toString();
      renderSpotlight();
      update();
    } catch (error) {
      console.error("Unable to load directory:", error);
      els.list.setAttribute("aria-busy", "false");
      els.list.innerHTML = '<div class="loading-card">Catalog unavailable. Run <code>python3 scripts/build_catalog.py</code> when previewing locally, or check the Pages build.</div>';
      els.resultsLabel.textContent = "Unable to load directory";
      els.total.textContent = "Catalog unavailable";
      els.nav.innerHTML = "";
    }
  }
  load();
})();
