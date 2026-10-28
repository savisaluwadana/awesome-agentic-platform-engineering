# Awesome Agentic Platform Engineering

> A community-curated directory of open-source projects at the intersection of **AI agents, Kubernetes, developer platforms, and cloud-native infrastructure**.

[Explore the directory](https://savisaluwadana.github.io/awesome-agentic-platform-engineering/) · [Suggest a project](https://github.com/savisaluwadana/awesome-agentic-platform-engineering/edit/main/README.md) · [Contribution guide](CONTRIBUTING.md)

Agentic platform engineering is about giving developers and AI agents safe, observable, repeatable ways to build, ship, and operate software. This list covers both **agent-native systems** and the **platform foundations** they depend on. Inclusion does not imply endorsement or that every tool is an AI-agent product.

**The README is the catalog.** The companion GitHub Pages website is generated from the entries below, so adding an entry here automatically adds it to the website after the pull request is merged.

## Directory

### Agent Frameworks & Orchestration

- [kagent](https://github.com/kagent-dev/kagent) — Cloud-native framework for building AI agents that help operate Kubernetes and platform infrastructure.
- [LangGraph](https://github.com/langchain-ai/langgraph) — Framework for stateful, long-running, and controllable agent workflows.
- [CrewAI](https://github.com/crewAIInc/crewAI) — Framework for coordinating multiple AI agents across tasks and workflows.
- [Dapr](https://github.com/dapr/dapr) — Distributed application runtime with workflow, messaging, and building blocks useful for agentic systems.

### Developer Platforms & Control Planes

- [OpenChoreo](https://github.com/openchoreo/openchoreo) — Open-source internal developer platform for deploying, managing, and operating applications on Kubernetes.
- [Backstage](https://github.com/backstage/backstage) — Open framework for building developer portals and software catalogs.
- [Crossplane](https://github.com/crossplane/crossplane) — Cloud-native control plane for managing infrastructure and services through Kubernetes APIs.
- [kro](https://github.com/kubernetes-sigs/kro) — Kubernetes Resource Orchestrator for defining and managing collections of Kubernetes resources.

### MCP & Tool Infrastructure

- [ToolHive](https://github.com/stacklok/toolhive) — Platform for running and managing Model Context Protocol servers with operational controls.
- [MCP Servers](https://github.com/modelcontextprotocol/servers) — Reference implementations of servers using the Model Context Protocol.

### GitOps & Delivery

- [Argo CD](https://github.com/argoproj/argo-cd) — Declarative GitOps continuous delivery for Kubernetes.
- [Flux](https://github.com/fluxcd/flux2) — Open and extensible GitOps continuous delivery for Kubernetes.

### Observability & Evaluation

- [Langfuse](https://github.com/langfuse/langfuse) — Open-source tracing, evaluation, and observability for LLM applications and AI agents.
- [Phoenix](https://github.com/Arize-ai/phoenix) — Open-source AI observability and evaluation platform.
- [OpenTelemetry Collector](https://github.com/open-telemetry/opentelemetry-collector) — Vendor-neutral collector for receiving, processing, and exporting telemetry.

### Security & Policy

- [Promptfoo](https://github.com/promptfoo/promptfoo) — Evaluation, red teaming, and security testing for prompts and AI applications.
- [Open Policy Agent](https://github.com/open-policy-agent/opa) — General-purpose policy engine for enforcing declarative authorization and governance.
- [Kyverno](https://github.com/kyverno/kyverno) — Kubernetes-native policy-as-code for validating, mutating, and generating resources.
- [Trivy](https://github.com/aquasecurity/trivy) — Scanner for vulnerabilities, secrets, misconfigurations, and other security issues.

## How to add a project

1. Confirm the project is open source, has a working repository, and is relevant to agentic platform engineering or its foundational infrastructure.
2. Choose the closest **`### Category`** under **`## Directory`** above.
3. Add one Markdown bullet using exactly this shape: **`- [Project name](https://github.com/owner/repo) — A specific, factual one-sentence description.`**
4. Open a pull request. Please do not add duplicates, promotional superlatives, tracking links, or claims that cannot be verified.

See [CONTRIBUTING.md](CONTRIBUTING.md) for editorial criteria, local preview, and build details.

## Website

The website gives the list a searchable, filterable, mobile-friendly discovery interface with category navigation and GitHub star counts where available. **Stars are fetched from GitHub; they are not votes on this directory.** It doesn't require accounts, a database, or a paid hosting provider.

The catalog is parsed from this README by `scripts/build_catalog.py`. GitHub Actions rebuilds and deploys the site when `main` changes, and refreshes project metadata on a schedule. GitHub Pages must be configured once under **Settings → Pages → Build and deployment → Source → GitHub Actions**.

For local preview:

```bash
python3 scripts/build_catalog.py
python3 -m http.server 8000 --directory site
```

Open `http://localhost:8000`. Metadata enrichments are optional: set `GITHUB_TOKEN` to avoid low unauthenticated API limits.

## Community & maintenance

This is an independent, community-maintained resource, not a ranking of quality or a claim that every listed product is agent-native. Help improve descriptions, report broken links, or suggest a missing category via an issue or pull request. Project names and logos belong to their respective maintainers.

## License

Content is shared under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). Contributions are made under the same terms.
