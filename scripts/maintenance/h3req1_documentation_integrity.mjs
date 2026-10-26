#!/usr/bin/env node

// StudIAMatch-Docs: .context/trazabilidad/registro_fuentes_componentes.md#checker
// Read-only by default: no project imports, network, environment reads, or writes.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const registryPath = ".context/trazabilidad/registro_fuentes_componentes.json";
const registryMarkdownPath = ".context/trazabilidad/registro_fuentes_componentes.md";
const historicalIndexStart = "<!-- h3req1:historical-catalog-index:start -->";
const historicalIndexEnd = "<!-- h3req1:historical-catalog-index:end -->";
const requestedMode = process.argv.slice(2);

function readJson(relative) {
  return JSON.parse(fs.readFileSync(path.join(root, relative), "utf8"));
}

function candidateScopeFromArgs(args = requestedMode) {
  const indexes = args.flatMap((value, index) => value === "--candidate-manifest" ? [index] : []);
  if (indexes.length === 0) return null;
  if (indexes.length !== 1 || !args[indexes[0] + 1] || args[indexes[0] + 1].startsWith("--")) {
    throw new Error("--candidate-manifest requires exactly one repository-relative path");
  }
  const manifestPath = args[indexes[0] + 1];
  const absolutePath = path.resolve(root, manifestPath);
  if (!absolutePath.startsWith(`${root}${path.sep}`)) {
    throw new Error("candidate manifest path escapes the checkout");
  }
  const manifest = JSON.parse(fs.readFileSync(absolutePath, "utf8"));
  if (!Array.isArray(manifest.scope?.entries) || typeof manifest.package_artifacts !== "object") {
    throw new Error("candidate manifest is missing scope entries or package artifacts");
  }
  const selectedPaths = new Set(
    manifest.scope.entries
      .filter((entry) => entry && typeof entry.path === "string" && entry.status !== "deleted")
      .map((entry) => entry.path),
  );
  for (const artifact of Object.values(manifest.package_artifacts)) {
    if (artifact?.included === true && typeof artifact.path === "string") selectedPaths.add(artifact.path);
  }
  return { manifestPath, selectedPaths };
}

function candidateManifestOmissionAllowed(relative, exactAllowedPaths, candidateScope) {
  return Boolean(candidateScope && exactAllowedPaths.has(relative) && !candidateScope.selectedPaths.has(relative));
}

function candidateOnlySourceCountForScope(discovered, candidateOnlyPaths, candidateScope) {
  return discovered.filter((relative) => candidateOnlyPaths.has(relative)
    && (!candidateScope || candidateScope.selectedPaths.has(relative))).length;
}

function isAsciiLetter(char) {
  return (char >= "A" && char <= "Z") || (char >= "a" && char <= "z");
}

function findMarkupTagEnd(value, start) {
  let quote = "";
  for (let index = start; index < value.length; index += 1) {
    const char = value[index];
    if (quote) {
      if (char === quote) quote = "";
      continue;
    }
    if (char === "\"" || char === "'") {
      quote = char;
      continue;
    }
    if (char === ">") return index;
  }
  return -1;
}

function stripMarkupForAnchor(value) {
  let output = "";
  let cursor = 0;
  while (cursor < value.length) {
    if (value.startsWith("<!--", cursor)) {
      const commentEnd = value.indexOf("-->", cursor + 4);
      if (commentEnd < 0) {
        output += value.slice(cursor + 1);
        break;
      }
      cursor = commentEnd + 3;
      continue;
    }
    if (value[cursor] !== "<") {
      output += value[cursor];
      cursor += 1;
      continue;
    }
    if (value.startsWith("<!", cursor) || value.startsWith("<?", cursor)) {
      const declarationEnd = findMarkupTagEnd(value, cursor + 2);
      if (declarationEnd < 0) {
        output += value.slice(cursor + 1);
        break;
      }
      cursor = declarationEnd + 1;
      continue;
    }

    let nameStart = cursor + 1;
    if (value[nameStart] === "/") nameStart += 1;
    if (!isAsciiLetter(value[nameStart] ?? "")) {
      output += "<";
      cursor += 1;
      continue;
    }
    let nameEnd = nameStart + 1;
    while (nameEnd < value.length) {
      const char = value[nameEnd];
      if (!isAsciiLetter(char) && !(char >= "0" && char <= "9") && char !== "-" && char !== ":") break;
      nameEnd += 1;
    }
    if (nameEnd < value.length && ![" ", "\t", "\r", "\n", "/", ">"].includes(value[nameEnd])) {
      output += "<";
      cursor += 1;
      continue;
    }
    const tagEnd = findMarkupTagEnd(value, nameEnd);
    if (tagEnd < 0) {
      output += value.slice(nameStart);
      break;
    }
    cursor = tagEnd + 1;
  }
  return output;
}

function normalizeHeading(value) {
  return stripMarkupForAnchor(value)
    .replace(/`([^`]*)`/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
    .replace(/[*_~]/g, "")
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^\p{L}\p{N}\s-]/gu, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-");
}

function anchorsIn(markdown) {
  const anchors = new Set();
  const repeated = new Map();
  for (const line of markdown.split(/\r?\n/)) {
    const match = line.match(/^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$/);
    if (!match) continue;
    const base = normalizeHeading(match[1]);
    if (!base) continue;
    const index = repeated.get(base) ?? 0;
    repeated.set(base, index + 1);
    anchors.add(index === 0 ? base : `${base}-${index}`);
  }
  return anchors;
}

function stripTitle(raw) {
  const value = raw.trim();
  if (value.startsWith("<")) {
    const close = value.indexOf(">");
    return close > 0 ? value.slice(1, close) : value;
  }
  return value.match(/^\S+/)?.[0] ?? "";
}

function isExternal(target) {
  return /^(?:[a-z][a-z0-9+.-]*:|\/\/)/i.test(target);
}

function splitTarget(raw) {
  const cleaned = stripTitle(raw).replace(/\\([()])/g, "$1");
  const hash = cleaned.indexOf("#");
  if (hash < 0) return { filePart: cleaned, fragment: "" };
  return { filePart: cleaned.slice(0, hash), fragment: cleaned.slice(hash + 1) };
}

function resolveTarget(sourcePath, rawTarget) {
  let target = rawTarget.trim();
  if (!target || isExternal(target)) return null;
  try {
    target = decodeURIComponent(target);
  } catch {
    return { error: "invalid URI encoding" };
  }
  const { filePart, fragment } = splitTarget(target);
  const sourceDir = path.dirname(path.join(root, sourcePath));
  const absolute = filePart
    ? path.resolve(sourceDir, filePart.startsWith("/") ? `.${filePart}` : filePart)
    : path.resolve(root, sourcePath);
  const relative = path.relative(root, absolute).split(path.sep).join("/");
  if (relative.startsWith("../") || relative === "..") return { error: "target escapes checkout" };
  return { absolute, relative, fragment };
}

function linksIn(markdown) {
  const links = [];
  for (const match of markdown.matchAll(/!?\[[^\]]*\]\(([^)]*)\)/g)) links.push(match[1]);
  for (const match of markdown.matchAll(/\[\[([^\]]+)\]\]/g)) {
    links.push(match[1].split("|")[0].trim());
  }
  return links;
}

function pathExists(relative) {
  try {
    return fs.statSync(path.join(root, relative)).isFile();
  } catch {
    return false;
  }
}

function markdownAnchorExists(relative, fragment) {
  if (!fragment || path.extname(relative).toLowerCase() !== ".md") return true;
  const contents = fs.readFileSync(path.join(root, relative), "utf8");
  return anchorsIn(contents).has(normalizeHeading(fragment.replace(/^#/, "")));
}

function walkFiles(absolute, found) {
  if (!fs.existsSync(absolute)) return;
  const stat = fs.lstatSync(absolute);
  if (stat.isSymbolicLink()) return;
  if (stat.isFile()) {
    found.push(absolute);
    return;
  }
  if (!stat.isDirectory()) return;
  const ignoredDirectories = new Set([".git", "node_modules", ".next", ".wrangler", ".vercel", ".turbo", "out", "coverage", "__pycache__", ".pytest_cache", ".cache", "test-results", "playwright-report", "storybook-static"]);
  for (const entry of fs.readdirSync(absolute, { withFileTypes: true })) {
    if (entry.isDirectory() && ignoredDirectories.has(entry.name)) continue;
    walkFiles(path.join(absolute, entry.name), found);
  }
}

function sourcePathIsExcluded(relative, exclusions) {
  return exclusions.some((item) => item.paths.includes(relative)
    || (item.allow_family_pattern === true && globMatches(item.pattern, relative)));
}

function globMatches(pattern, relative) {
  let expression = "^";
  for (let index = 0; index < pattern.length; index += 1) {
    const character = pattern[index];
    if (character === "*" && pattern[index + 1] === "*") {
      if (pattern[index + 2] === "/") {
        expression += "(?:.*/)?";
        index += 2;
      } else {
        expression += ".*";
        index += 1;
      }
    } else if (character === "*") {
      expression += "[^/]*";
    } else {
      expression += character.replace(/[|\\{}()[\]^$+?.]/g, "\\$&");
    }
  }
  return new RegExp(`${expression}$`).test(relative);
}

function discoveryFilePaths(registry) {
  const found = [];
  const roots = [...registry.discovery.roots];
  if (registry.discovery.context_source_root) roots.push(registry.discovery.context_source_root);
  for (const entry of roots) {
    walkFiles(path.join(root, typeof entry === "string" ? entry : entry.path), found);
  }
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    if (entry.isFile() && entry.name !== registry.discovery.git_metadata?.name) found.push(path.join(root, entry.name));
  }
  return [...new Set(found.map((absolute) => path.relative(root, absolute).split(path.sep).join("/")))].sort();
}

function isContextDocument(relative, registry) {
  const contextRoot = registry.discovery.context_source_root;
  return Boolean(contextRoot && (relative === contextRoot || relative.startsWith(`${contextRoot}/`))
    && path.extname(relative).toLowerCase() === ".md");
}

function discoverSources(registry) {
  const extensions = new Set(registry.discovery.extensions);
  const exactNames = new Set(registry.discovery.exact_names);
  return discoveryFilePaths(registry)
    .filter((relative) => !isContextDocument(relative, registry))
    .filter((relative) => !sourcePathIsExcluded(relative, registry.exclusions))
    .filter((relative) => {
      const basename = path.basename(relative);
      return exactNames.has(basename) || extensions.has(path.extname(relative).toLowerCase()) || (fs.statSync(path.join(root, relative)).mode & 0o111) !== 0;
    })
    .sort();
}

function configuredNonSourceRoots(registry) {
  return new Map((registry.discovery.non_source_roots ?? []).map((item) => [item.path, item]));
}

function unregisteredRootSources(registry, rootDirectories = null, virtualPaths = []) {
  const directoryNames = rootDirectories ?? fs.readdirSync(root, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && !entry.isSymbolicLink())
    .map((entry) => entry.name);
  const declaredRoots = new Set(registry.discovery.roots.map((entry) => typeof entry === "string" ? entry : entry.path));
  const nonSourceRoots = configuredNonSourceRoots(registry);
  const ignoredDirectories = new Set([".git", "node_modules", ".next", ".wrangler", ".vercel", ".turbo", "out", "coverage", "__pycache__", ".pytest_cache", ".cache", "test-results", "playwright-report", "storybook-static"]);
  const candidates = [...virtualPaths];
  for (const name of directoryNames) {
    if (declaredRoots.has(name) || nonSourceRoots.has(name) || ignoredDirectories.has(name)) continue;
    const found = [];
    walkFiles(path.join(root, name), found);
    for (const absolute of found) {
      const relative = path.relative(root, absolute).split(path.sep).join("/");
      candidates.push(relative);
    }
  }
  return [...new Set(candidates.filter((relative) => {
    const rootName = relative.split("/")[0];
    return !declaredRoots.has(rootName) && !nonSourceRoots.has(rootName) && !ignoredDirectories.has(rootName)
      && !sourcePathIsExcluded(relative, registry.exclusions);
  }))].sort();
}

function unclassifiedSourceExtensions(registry, files = null) {
  const found = files ?? discoveryFilePaths(registry);
  const extensions = new Set(registry.discovery.extensions);
  const exactNames = new Set(registry.discovery.exact_names);
  return found.filter((relative) => {
    if (isContextDocument(relative, registry)) return false;
    if (sourcePathIsExcluded(relative, registry.exclusions)) return false;
    const absolute = path.join(root, relative);
    let executable = false;
    try { executable = (fs.statSync(absolute).mode & 0o111) !== 0; } catch {}
    return !exactNames.has(path.basename(relative)) && !extensions.has(path.extname(relative).toLowerCase()) && !executable;
  }).sort();
}

function discoverContextDocuments() {
  const found = [];
  walkFiles(path.join(root, ".context"), found);
  return [...new Set(found
    .map((absolute) => path.relative(root, absolute).split(path.sep).join("/"))
    .filter((relative) => path.extname(relative).toLowerCase() === ".md"))].sort();
}

function pointerParts(pointer) {
  const hash = pointer.lastIndexOf("#");
  if (hash < 0) return { path: pointer, anchor: "" };
  return { path: pointer.slice(0, hash), anchor: pointer.slice(hash + 1) };
}

function validatePointer(pointer) {
  const { path: relative, anchor } = pointerParts(pointer);
  if (!pathExists(relative)) return `${pointer}: target document missing`;
  if (anchor && !markdownAnchorExists(relative, anchor)) return `${pointer}: target anchor missing`;
  return null;
}

function isCompleteRelation(value) {
  return value && ["verified", "pending", "remote_only", "not_applicable"].includes(value.state)
    && typeof value.note === "string" && value.note.trim().length > 0
    && Array.isArray(value.evidence)
    && (!["pending", "remote_only"].includes(value.state) || (typeof value.resolution === "string" && value.resolution.trim().length > 0))
    && (value.state !== "remote_only" || (Array.isArray(value.remote_checks) && value.remote_checks.length > 0));
}

function shouldScanSourceComments(policy) {
  return policy === "required" || policy === "optional";
}

function sourceCommentMarkers(source) {
  const markers = [];
  for (const line of source.split(/\r?\n/)) {
    let match = line.match(/^\s*(?:\/\/|#)\s*StudIAMatch-Docs:(.*)$/);
    let htmlComment = false;
    if (!match) {
      match = line.match(/^\s*<!--\s*StudIAMatch-Docs:(.*)$/);
      htmlComment = Boolean(match);
    }
    if (!match) continue;

    let value = match[1].trim();
    if (htmlComment) {
      if (!value.endsWith("-->")) {
        markers.push("malformed:html_comment_not_closed");
        continue;
      }
      value = value.slice(0, -3).trim();
    }
    if (!/^[^\s*"'`]+$/.test(value)) markers.push("malformed:extra_comment_text");
    else markers.push(value);
  }
  return markers;
}

function sourceCommentIssues(markers, expected, policy) {
  const failures = [];
  if (policy === "required" && markers.length === 0) failures.push(`missing_or_mismatched:${expected}`);
  if (policy === "none" && markers.length) failures.push(`unexpected:${markers.join(",")}`);
  for (const marker of markers) {
    if (marker.startsWith("malformed:")) {
      failures.push(marker);
      continue;
    }
    if (marker !== expected) failures.push(`registry_mismatch:${marker}!=${expected}`);
  }
  if (markers.length > 1) failures.push(`duplicate:${markers.length}`);
  return failures;
}

function markdownLinksTo(sourcePath, targetPath, targetAnchor = "") {
  if (!pathExists(sourcePath)) return false;
  const markdown = fs.readFileSync(path.join(root, sourcePath), "utf8");
  return markdownContainsLink(markdown, sourcePath, targetPath, targetAnchor);
}

function markdownContainsLink(markdown, sourcePath, targetPath, targetAnchor = "") {
  return linksIn(markdown).some((raw) => {
    const resolved = resolveTarget(sourcePath, raw);
    return resolved && !resolved.error && resolved.relative === targetPath
      && (!targetAnchor || normalizeHeading(resolved.fragment) === normalizeHeading(targetAnchor));
  });
}

function relativeMarkdownTarget(sourcePath, targetPath, anchor = "") {
  const from = path.dirname(path.join(root, sourcePath));
  const target = path.relative(from, path.join(root, targetPath)).split(path.sep).join("/")
    .split("/").map(encodeURIComponent).join("/");
  return target + (anchor ? "#" + anchor : "");
}

function linkedPath(sourcePath, targetPath, label = targetPath, anchor = "") {
  return "[" + escapeMarkdown(label) + "](" + relativeMarkdownTarget(sourcePath, targetPath, anchor) + ")";
}

function historicalPurposeBasis(document) {
  const basis = document.purpose_basis;
  if (basis === "direct_preparation_record_and_result_section") return "Propósito descrito en la preparación y el resultado relacionados.";
  if (basis === "filename_and_directory_only_client_evidence_not_read") return "Propósito limitado a la ruta/nombre; contenido de evidencia de cliente no leído.";
  if (basis === "filename_only_no_h1") return "Resumen tomado del nombre del archivo; no se encontró un H1 que describa propósito.";
  return "Resumen tomado del H1 del documento; no acredita por sí solo aceptación ni ejecución.";
}

function historicalStatusLabel(status) {
  return ({ historical: "histórico", current: "vigente según el documento", superseded: "sustituido" })[status]
    ?? "estado sin clasificar: " + escapeMarkdown(status ?? "missing");
}

function historicalComponentBasis(document) {
  const value = document.component_basis ?? "";
  if (value.startsWith("source paths in document mapped through the canonical source registry")) return "Las rutas de fuente citadas se asignaron con el registro canónico; título/ruta añade solo contexto. No afirma que el componente consuma esta evidencia.";
  if (value.startsWith("title/path subject classification")) return "Clasificación por título/ruta para navegación histórica; no afirma consumidor de producto.";
  if (value.startsWith("directory and filename only")) return "Solo directorio y nombre; el contenido no se leyó y no se atribuye consumidor.";
  return value ? escapeMarkdown(value) : "Base de asignación no registrada.";
}

function historicalRequirementBasis(document) {
  const value = document.requirement_basis ?? "";
  if (value.startsWith("explicit code in title or path")) return "Código explícito en título o ruta; no valida aceptación.";
  if (value.startsWith("no requirement code in title/path")) return "Sin código en título/ruta; no se infiere requerimiento.";
  return escapeMarkdown(value || "Base de requerimiento no registrada.");
}

function historicalContentReview(document) {
  const value = document.content_review ?? "";
  if (value.startsWith("local Markdown and path references scanned")) return "Se escaneó Markdown y referencias de ruta locales; el archivo histórico no se editó.";
  if (value.startsWith("not_read_by_scope")) return "No leído por alcance; se enlaza solo por ruta/nombre sanitizado.";
  return escapeMarkdown(value || "Contenido no revisado.");
}

function historicalRelationSummary(document, key, sourcePath) {
  const relation = document.relations?.[key] ?? {};
  const labels = {
    identified: "referencia identificada localmente",
    not_identified_in_local_search: "no identificada en la búsqueda local declarada; no demuestra que nunca existió",
    not_found_in_local_search: "no encontrada en la búsqueda local declarada",
    not_reviewed: "no revisada por el alcance de preservación",
    not_applicable: "no aplica con justificación registrada",
    unknown: "desconocida; requiere investigación local",
  };
  const paths = (relation.paths ?? []).map((relative) => pathExists(relative)
    ? linkedPath(sourcePath, relative, relative)
    : "FALTA " + escapeMarkdown(relative));
  const note = relation.note ? escapeMarkdown(relation.note) : "sin nota de búsqueda/evidencia";
  return (labels[relation.state] ?? "estado sin clasificar: " + escapeMarkdown(relation.state ?? "missing"))
    + (paths.length ? "; " + paths.join(", ") : "") + "; " + note;
}

function renderHistoricalCatalogMarkdown(registry, catalog) {
  const documents = registry.historical_documents
    .filter((document) => document.catalog_id === catalog.id)
    .sort((left, right) => left.path.localeCompare(right.path));
  const lines = [
    "# " + catalog.title,
    "",
    "> Catálogo de navegación histórica. Sus entradas preservan cortes y resultados; no crean autoridad operativa ni trasladan un resultado al estado actual.",
    "",
    "## Propósito y alcance",
    "",
    catalog.purpose,
    "",
    "Documentos preservados en este catálogo: " + documents.length + ". La asignación se mantiene en el registro JSON canónico. Cada vínculo conduce al archivo histórico sin modificar sus bytes.",
    "",
    "## Componentes relacionados",
    "",
  ];
  for (const module of catalog.module_links) {
    const component = registry.components.find((item) => item.id === module.component_id);
    lines.push("- " + linkedPath(catalog.path, module.path, component?.title ?? module.component_id, module.anchor));
  }
  lines.push(
    "",
    "## Documentos preservados",
    "",
    "La relación anterior/posterior se muestra solo cuando una fuente local la declara. El número de revisión por sí solo no demuestra una secuencia.",
    "",
  );
  for (const document of documents) {
    const requirement = document.requirement_codes?.length
      ? document.requirement_codes.join(", ")
      : "sin código explícito en título/ruta";
    const components = (document.component_ids ?? []).map((id) => {
      const component = registry.components.find((item) => item.id === id);
      return component ? linkedPath(catalog.path, component.document.path, component.title, component.document.anchor) : "componente sin ficha: " + escapeMarkdown(id);
    });
    const sequence = [];
    for (const relative of document.predecessor_paths ?? []) sequence.push("anterior: " + (pathExists(relative) ? linkedPath(catalog.path, relative, relative) : "FALTA " + escapeMarkdown(relative)));
    for (const relative of document.successor_paths ?? []) sequence.push("posterior: " + (pathExists(relative) ? linkedPath(catalog.path, relative, relative) : "FALTA " + escapeMarkdown(relative)));
    lines.push(
      "### " + linkedPath(catalog.path, document.path, document.title),
      "",
      "- **Path:** `" + escapeMarkdown(document.path) + "` · **Estado:** " + historicalStatusLabel(document.status) + " — " + escapeMarkdown(document.status_note),
      "- **Propósito documentado:** " + escapeMarkdown(document.purpose) + " _(" + historicalPurposeBasis(document) + ")_",
      "- **Componente(s):** " + (components.length ? components.join("; ") : "sin componente atribuido") + ". Base: " + historicalComponentBasis(document),
      "- **Requerimiento(s):** " + escapeMarkdown(requirement) + ". " + historicalRequirementBasis(document),
      "- **Fuente(s):** " + historicalRelationSummary(document, "sources", catalog.path),
      "- **Runner:** " + historicalRelationSummary(document, "runner", catalog.path),
      "- **Test(s):** " + historicalRelationSummary(document, "tests", catalog.path),
      "- **Manifiesto(s):** " + historicalRelationSummary(document, "manifests", catalog.path),
      "- **Resultado(s):** " + historicalRelationSummary(document, "results", catalog.path),
      "- **Anterior/posterior:** " + (sequence.length ? sequence.join("; ") : "no se atribuye secuencia con la evidencia local revisada") + ". " + escapeMarkdown(document.sequence_basis ?? "Sin relación anterior/posterior acreditada."),
      "- **Preservación/alcance:** " + escapeMarkdown(document.preservation_reason ?? "Conservado como historia.") + " _(" + historicalContentReview(document) + ")_.",
      "",
    );
  }
  lines.push("---", "", linkedPath(catalog.path, ".context/indice.md", "Índice principal") + " · [Estado operativo](../estado_del_proyecto.md)", "");
  return lines.join("\n");
}

function renderHistoricalCatalogIndexSection(registry) {
  const historicalDocuments = registry.historical_documents ?? [];
  const historicalByCatalog = new Map((registry.historical_catalogs ?? []).map((catalog) => [catalog.id, 0]));
  for (const document of historicalDocuments) {
    historicalByCatalog.set(document.catalog_id, (historicalByCatalog.get(document.catalog_id) ?? 0) + 1);
  }
  const lines = [
    historicalIndexStart,
    "### Catálogos subordinados de evidencia histórica",
    "",
    "Estos catálogos dan navegación individual a documentos preservados. No convierten resultados históricos en estado vigente ni autoridad operativa. Los conteos se generan desde el registro canónico y el checker valida que el bloque visible coincida.",
    "",
    "| Proceso/familia | Catálogo | Documentos catalogados |",
    "|---|---|---:|",
  ];
  for (const catalog of registry.historical_catalogs ?? []) {
    lines.push(`| ${escapeMarkdown(catalog.title)} | [${escapeMarkdown(catalog.title)}](${catalog.path.slice(".context/".length)}#${escapeMarkdown(catalog.anchor)}) | ${historicalByCatalog.get(catalog.id) ?? 0} |`);
  }
  lines.push(historicalIndexEnd);
  return lines.join("\n");
}

function replaceHistoricalCatalogIndexSection(contents, registry) {
  const start = contents.indexOf(historicalIndexStart);
  const end = contents.indexOf(historicalIndexEnd);
  if (start < 0 || end < start || contents.indexOf(historicalIndexStart, start + historicalIndexStart.length) >= 0
    || contents.indexOf(historicalIndexEnd, end + historicalIndexEnd.length) >= 0) return contents;
  return contents.slice(0, start) + renderHistoricalCatalogIndexSection(registry) + contents.slice(end + historicalIndexEnd.length);
}

function historicalCatalogIndexFailures(registry, contents = fs.readFileSync(path.join(root, ".context/indice.md"), "utf8")) {
  const expected = renderHistoricalCatalogIndexSection(registry);
  const startCount = contents.split(historicalIndexStart).length - 1;
  const endCount = contents.split(historicalIndexEnd).length - 1;
  if (startCount !== 1 || endCount !== 1) return ["HISTORICAL_CATALOG_INDEX_BLOCK_MISSING_OR_DUPLICATE .context/indice.md"];
  const start = contents.indexOf(historicalIndexStart);
  const end = contents.indexOf(historicalIndexEnd);
  const actual = contents.slice(start, end + historicalIndexEnd.length);
  return actual === expected
    ? []
    : ["HISTORICAL_CATALOG_INDEX_DRIFT .context/indice.md; regenerate the catalog summary from the canonical JSON"];
}

function groupForPath(registry) {
  const assigned = new Map();
  const duplicate = [];
  for (const group of registry.groups) {
    for (const relative of group.paths) {
      if (assigned.has(relative)) duplicate.push(relative);
      assigned.set(relative, group);
    }
  }
  return { assigned, duplicate };
}

function unassignedSources(sources, assigned) {
  return sources.filter((relative) => !assigned.has(relative));
}

function unassignedSourceFailures(sources, assigned) {
  return unassignedSources(sources, assigned).map((relative) => `SOURCE_UNASSIGNED ${relative}`);
}

function escapeMarkdown(value) {
  return String(value).replaceAll("|", "\\|").replaceAll("\n", " ");
}

function renderRegistryMarkdown(registry) {
  const { assigned } = groupForPath(registry);
  const from = path.dirname(path.join(root, registryMarkdownPath));
  const mainIndex = registry.navigation?.main_index ?? "(missing)";
  const mainIndexTarget = path.relative(from, path.join(root, mainIndex)).split(path.sep).join("/");
  const lines = [
    "# Registro verificable de fuentes y componentes",
    "",
    `> Corte: ${registry.cutoff.date}; checkout candidato local \`${registry.cutoff.candidate_head}\`. Este registro es la única autoridad de asignación fuente→componente. El Markdown se genera desde el JSON; edita el JSON y vuelve a renderizarlo.`,
    "",
    "## Cómo leer y mantener el registro",
    "",
    "Cada ruta listada tiene una asignación exacta a un grupo y componente. Las propiedades del grupo se aplican a cada ruta; los consumidores no encontrados se declaran como desconocidos con método de resolución. El estado de una implementación, una prueba, un artefacto y una adopción remota son campos distintos.",
    "",
    "Crear, mover, eliminar o cambiar el contrato de una fuente requiere actualizar el JSON, esta vista generada, su ficha/anchor de dominio, consumidores, datos, pruebas, permisos, evidencia y manifiestos por impacto. Una ruta nueva no se asigna por convención de carpeta: el checker debe fallar hasta que se registre y se documente.",
    "",
    "## Navegación principal y documentos retirados",
    "",
    `Entrada única de Obsidian: [índice principal](${mainIndexTarget}). README raíz: \`${escapeMarkdown(registry.navigation?.root_readme ?? "(missing)" )}\`; los índices subordinados organizan solo sus propios registros.`,
    "",
    "| Path retirado | Clase | Sustitución vigente | Backup externo verificado | SHA-256 |",
    "|---|---|---|---|---|",
  ];
  const docLink = (document) => {
    const to = path.join(root, document.path);
    return `${path.relative(from, to).split(path.sep).join("/")}#${document.anchor}`;
  };
  const sourceLink = (relative) => {
    const from = path.dirname(path.join(root, registryMarkdownPath));
    const to = path.join(root, relative);
    const target = path.relative(from, to).split(path.sep).join("/").split("/").map(encodeURIComponent).join("/");
    return `[abrir](${target}) \`${escapeMarkdown(relative)}\``;
  };
  for (const item of registry.retired_documents ?? []) {
    const replacements = (item.replacement ?? []).map((target) => `[${escapeMarkdown(target.path)}#${escapeMarkdown(target.anchor)}](${docLink(target)})`).join(", ");
    lines.push(`| \`${escapeMarkdown(item.path)}\` | ${escapeMarkdown(item.kind)} | ${replacements} | \`${escapeMarkdown(item.backup_location)}\` | \`${escapeMarkdown(item.backup_sha256)}\` |`);
  }
  lines.push(
    "",
    "## Descubrimiento y exclusiones",
    "",
    `El descubrimiento local inspecciona ${registry.discovery.roots.length} raíces declaradas más la raíz documental no Markdown \`${escapeMarkdown(registry.discovery.context_source_root)}\` y reconoce ${registry.discovery.extensions.length} extensiones más nombres exactos. Actualmente descubre rutas fuente en el checkout candidato; no consulta secretos ni servicios.`,
    "",
    "Los directorios raíz nuevos con archivos fuera de exclusiones justificadas y las extensiones no clasificadas dentro de raíces conocidas hacen fallar el gate. `.context/` se recorre por separado: sus Markdown pertenecen al grafo de documentos y sus archivos no Markdown se inspeccionan como fuentes/configuración salvo exclusión justificada; las copias selladas se clasifican por familia.",
    "",
    `Proyección documental: ${escapeMarkdown(registry.discovery.integration_projection?.projected_relevant_source_paths_at_cut)} paths pertenecen al conjunto R8/R9 previsto; ${escapeMarkdown(registry.discovery.integration_projection?.candidate_only_path_count_at_cut)} quedan identificados como WIP por grupo. En el snapshot de integración se enlazan solo los paths disponibles; el resto se conserva como texto y su ausencia solo se tolera con manifiesto exacto.`,
    "",
    "| Familia excluida | Paths observados | Clase | Motivo y tratamiento | Retención / valor probatorio |",
    "|---|---|---|---|---|",
  );
  if (registry.discovery.non_source_roots?.length) {
    lines.push("", "### Raíces clasificadas fuera de fuentes mantenidas", "", "| Ruta | Motivo de clasificación | Navegación |", "|---|---|---|");
    for (const entry of registry.discovery.non_source_roots) {
      lines.push(`| \`${escapeMarkdown(entry.path)}\` | ${escapeMarkdown(entry.reason)} | [${escapeMarkdown(entry.document.path)}#${escapeMarkdown(entry.document.anchor)}](${docLink(entry.document)}) |`);
    }
  }
  if (registry.discovery.git_metadata) {
    const entry = registry.discovery.git_metadata;
    lines.push("", "### Metadato del checkout", "", `Se omite la entrada administrativa \`${escapeMarkdown(entry.name)}\` (archivo de worktree o directorio Git) como metadato de control de versiones: ${escapeMarkdown(entry.reason)} [${escapeMarkdown(entry.document.path)}#${escapeMarkdown(entry.document.anchor)}](${docLink(entry.document)}).`);
  }
  for (const item of registry.exclusions) {
    const observedPaths = item.paths.length
      ? item.paths.map((relative) => `\`${escapeMarkdown(relative)}\``).join("<br>")
      : item.allow_family_pattern ? "familia dinámica declarada" : "sin archivo observado";
    lines.push(`| \`${escapeMarkdown(item.pattern)}\` | ${observedPaths} | ${escapeMarkdown(item.kind)} | ${escapeMarkdown(item.reason)} [${escapeMarkdown(item.document.label)}](${docLink(item.document)}) | ${escapeMarkdown(item.retention)} / ${escapeMarkdown(item.evidence)} |`);
  }
  lines.push("", "## Navegación por componente", "");
  for (const component of registry.components) {
    const anchor = component.registry_anchor ?? component.id;
    lines.push(`### ${anchor}`, "", `[${escapeMarkdown(component.title)}](${docLink(component.document)}) · ${component.domain_documents.map((item) => `[${escapeMarkdown(item.path)}#${escapeMarkdown(item.anchor)}](${docLink(item)})`).join(" · ")}`, "");
  }
  lines.push("## Checker", "", "Validación local: `bash scripts/security/run_documentation_integrity.sh --self-test`. El modo normal es de solo lectura; `--render` regenera esta vista desde el JSON. El self-test simula una fuente nueva sin registro, exige su rechazo, permite omisiones exactas solo si están registradas y el manifiesto no las selecciona, rechaza rutas no registradas/seleccionadas o ausencia de manifiesto, comprueba que `unknown` no se acepte como estado relacional, valida la forma de `remote_only`, confirma las dos rutas YAML Docker del inventario y rechaza marcadores documentales con sufijo o duplicados. Los grupos `inline_comment: none` se validan por el registro externo y no leen el contenido para buscar marcadores.", "", "## Componentes", "", "| Componente | Página de componente | Dominio | Propósito |", "|---|---|---|---|");
  for (const component of registry.components) {
    lines.push(`| ${escapeMarkdown(component.title)} | [${escapeMarkdown(component.document.path)}](${docLink(component.document)}) | ${component.domain_documents.map((item) => `[${escapeMarkdown(item.path)}](${docLink(item)})`).join(", ")} | ${escapeMarkdown(component.purpose)} |`);
  }
  lines.push("", "## Asignaciones por fuente", "", "Cada path aparece de forma explícita. La fila enlaza el componente, su ficha, un documento/anchor de fuente y sus páginas de dominio. Las rutas marcadas `candidate-only` pertenecen al WIP local y no al conjunto previsto R8/R9; se conservan para el corte local y deben reconciliarse antes del paquete combinado. Las dimensiones de relación se heredan a nivel de grupo y el resumen las pondera por path; no equivale a evidencia individual por archivo.", "", "| Path fuente | Componente | Ficha de componente | Documento/anchor de fuente | Páginas de dominio | Propósito | Estado |", "|---|---|---|---|---|---|---|");
  for (const relative of [...assigned.keys()].sort()) {
    const group = assigned.get(relative);
    const component = registry.components.find((item) => item.id === group.component);
    const domainLinks = component.domain_documents.map((item) => `[${escapeMarkdown(item.path)}#${escapeMarkdown(item.anchor)}](${docLink(item)})`).join(", ");
    const sourceDocument = group.source_document ?? component.document;
    const isCandidateOnly = group.candidate_only_paths?.includes(relative) === true;
    const candidateOnly = isCandidateOnly ? " · candidate-only; exact inclusion or omission is controlled by the selected manifest" : "";
    const sourceReference = isCandidateOnly ? `\`${escapeMarkdown(relative)}\`` : sourceLink(relative);
    lines.push(`| ${sourceReference} | ${escapeMarkdown(component.title)} | [${escapeMarkdown(component.document.anchor)}](${docLink(component.document)}) | [${escapeMarkdown(sourceDocument.path)}#${escapeMarkdown(sourceDocument.anchor)}](${docLink(sourceDocument)}) | ${domainLinks} | ${escapeMarkdown(group.purpose)}${candidateOnly} | ${escapeMarkdown(group.status)} |`);
  }
  lines.push("", "## Relaciones, pruebas y evidencia por grupo", "", "Los seis estados se registran en el grupo que comparte responsabilidad y se aplican a sus paths; grupos heterogéneos deben dividirse antes de heredar relaciones. `pending` significa que falta una comprobación local con resolución concreta. `remote_only` significa que la afirmación requiere una lectura remota futura identificada; nunca cuenta como adopción verificada. `verified` acredita el vínculo descrito a partir de paths/símbolos o evidencia local, no un resultado de runtime si el note no lo declara. `not_applicable` requiere motivo. El resumen pondera relaciones por paths asignados, no por pruebas ejecutadas.", "");
  for (const group of registry.groups) {
    const component = registry.components.find((item) => item.id === group.component);
    const format = (relation) => `${relation.state}: ${escapeMarkdown(relation.note)}${relation.evidence.length ? `; evidencia: ${escapeMarkdown(relation.evidence.join(", "))}` : ""}${relation.resolution ? `; resolver: ${escapeMarkdown(relation.resolution)}` : ""}${relation.remote_checks?.length ? `; remote checks: ${escapeMarkdown(relation.remote_checks.join(", "))}` : ""}`;
    const sourceDocument = group.source_document ?? component.document;
    lines.push(`### ${group.id}`, "", `Componente: [${escapeMarkdown(component.title)}](${docLink(component.document)}) · ficha de fuente: [${escapeMarkdown(sourceDocument.path)}#${escapeMarkdown(sourceDocument.anchor)}](${docLink(sourceDocument)}) · ${group.paths.length} fuente(s) asignada(s).`, "", "| Contratos | Consumidores/dependencias | Datos | Pruebas/evidencia | Permisos y operación | Procedencia |", "|---|---|---|---|---|---|");
    lines.push(`| ${format(group.contracts)} | ${format(group.consumers)} | ${format(group.data)} | ${format(group.tests_evidence)} | ${format(group.operations)} | ${format(group.provenance)} |`, "");
  }
  lines.push("", "## Verificaciones exclusivamente remotas", "", "Estos checks no se ejecutaron ni se sustituyen por código, commits, configuración local o salidas históricas. Se cuentan por check único; las relaciones `remote_only` los referencian por ID.", "", "| ID | Componente | Fuentes relacionadas | Pregunta y método futuro | Owner | Estado |", "|---|---|---|---|---|---|");
  for (const check of registry.remote_checks ?? []) {
    const sourceLinks = (check.sources ?? []).map((source) => sourceLink(source)).join(", ");
    lines.push(`| ${escapeMarkdown(check.id)} | ${escapeMarkdown(check.component)} | ${sourceLinks} | ${escapeMarkdown(check.question)}; ${escapeMarkdown(check.method)} | ${escapeMarkdown(check.owner)} | ${escapeMarkdown(check.status)} |`);
  }
  lines.push("", "## Artefactos generados, fixtures y evidencia", "", "No son componentes fuente independientes. Se clasifican por familia con productor, inputs, propósito, ubicación, retención y límite probatorio.", "", "| Familia / ubicación | Productor | Inputs | Propósito | Retención | Valor probatorio |", "|---|---|---|---|---|---|");
  for (const item of registry.artifact_families) {
    lines.push(`| \`${escapeMarkdown(item.pattern)}\` | ${escapeMarkdown(item.producer)} | ${escapeMarkdown(item.inputs)} | ${escapeMarkdown(item.purpose)} | ${escapeMarkdown(item.retention)} | ${escapeMarkdown(item.evidence)} |`);
  }
  const documentExclusions = registry.document_exclusions ?? [];
  const historicalDocuments = registry.historical_documents ?? [];
  const historicalByCatalog = new Map(registry.historical_catalogs.map((catalog) => [catalog.id, 0]));
  for (const document of historicalDocuments) historicalByCatalog.set(document.catalog_id, (historicalByCatalog.get(document.catalog_id) ?? 0) + 1);
  lines.push("", "## Catálogos de evidencia histórica", "", `El corte contiene ${registry.active_documents.length} documentos activos declarados, ${historicalDocuments.length} documentos históricos catalogados y ${documentExclusions.reduce((sum, family) => sum + family.paths.length, 0)} documentos excluidos con motivo. Clasificación JSON no equivale a navegación: el checker exige un enlace Markdown desde el catálogo para cada histórico.`, "", "| Proceso/familia | Catálogo navegable | Históricos catalogados | Estado |", "|---|---|---:|---|");
  for (const catalog of registry.historical_catalogs) {
    lines.push(`| ${escapeMarkdown(catalog.title)} | [abrir catálogo](${docLink({ path: catalog.path, anchor: catalog.anchor })}) | ${historicalByCatalog.get(catalog.id) ?? 0} | navegación histórica; no autoridad operativa |`);
  }
  lines.push("", "### Documentos excluidos del grafo", "", "La exclusión no es una forma de archivar evidencia: cada ruta requiere patrón, razón, retención y documento justificativo. El gate cuenta estas rutas por separado de páginas activas e históricas catalogadas.", "", "| Familia excluida | Motivo | Rutas |", "|---|---|---:|");
  for (const family of documentExclusions) lines.push(`| \`${escapeMarkdown(family.pattern)}\` | ${escapeMarkdown(family.reason)} | ${family.paths.length} |`);
  if (documentExclusions.length === 0) lines.push("| — | No hay Markdown de .context excluido en este corte | 0 |\n");
  lines.push("", "## Lecturas históricas y límites", "", "El historial de ambos checkouts es local y de solo lectura. Un commit acredita que el cambio existió; no prueba que sus tests pasaran, que se desplegara o que siga activo. Pro sigue como baseline autoritativo de schema según reglas existentes; SQL local no demuestra aplicación remota. R8 y los cierres R178/R181/R182 se conservan sin alteración.", "", "[Índice Obsidian](../indice.md) · [Estado operativo](../estado_del_proyecto.md) · [Consolidación documental R11](../evidencia/h3req1_documentacion_consolidacion_trazabilidad_2026-10-13_r11.md)", "");
  return lines.join("\n");
}

function generatedDocumentation(registry) {
  const files = new Map([[registryMarkdownPath, renderRegistryMarkdown(registry)]]);
  const indexPath = registry.navigation?.main_index ?? ".context/indice.md";
  if (pathExists(indexPath)) {
    files.set(indexPath, replaceHistoricalCatalogIndexSection(fs.readFileSync(path.join(root, indexPath), "utf8"), registry));
  }
  for (const catalog of registry.historical_catalogs ?? []) {
    files.set(catalog.path, renderHistoricalCatalogMarkdown(registry, catalog));
  }
  return files;
}

function runSelfTest(registry, discovered, assigned, candidateScope, candidateOnlyPaths) {
  const incompleteTagHeading = normalizeHeading("<script");
  const inlineMarkupHeading = normalizeHeading('<em title="x > y">Course</em>');
  if (incompleteTagHeading !== "script"
    || incompleteTagHeading.includes("<")
    || incompleteTagHeading.includes(">")
    || inlineMarkupHeading !== "course") {
    process.stderr.write("DOC_SELF_TEST_FAIL heading normalization must remove markup delimiters from incomplete tags\n");
    return false;
  }
  const syntheticCandidateOnly = "scripts/core/__h3req1_candidate_only_source_self_test__.mjs";
  const syntheticExactOmissionPaths = new Set([syntheticCandidateOnly]);
  const syntheticCandidateScope = { selectedPaths: new Set() };
  if (!candidateManifestOmissionAllowed(syntheticCandidateOnly, syntheticExactOmissionPaths, syntheticCandidateScope)
    || candidateManifestOmissionAllowed("scripts/core/__h3req1_unlisted_source_self_test__.mjs", syntheticExactOmissionPaths, syntheticCandidateScope)
    || candidateManifestOmissionAllowed(syntheticCandidateOnly, syntheticExactOmissionPaths, { selectedPaths: new Set([syntheticCandidateOnly]) })
    || candidateManifestOmissionAllowed(syntheticCandidateOnly, syntheticExactOmissionPaths, null)) {
    process.stderr.write("DOC_SELF_TEST_FAIL candidate omissions must be exact, registered, unselected, and manifest-scoped\n");
    return false;
  }
  const syntheticSelectedCandidateOnly = "tests/__h3req1_selected_candidate_only_self_test__.mjs";
  const syntheticUnselectedCandidateOnly = "tests/__h3req1_unselected_candidate_only_self_test__.mjs";
  const syntheticCandidateOnlyPaths = new Set([syntheticSelectedCandidateOnly, syntheticUnselectedCandidateOnly]);
  if (candidateOnlySourceCountForScope(
    [syntheticSelectedCandidateOnly, syntheticUnselectedCandidateOnly],
    syntheticCandidateOnlyPaths,
    { selectedPaths: new Set([syntheticSelectedCandidateOnly]) },
  ) !== 1
    || candidateOnlySourceCountForScope(
      [syntheticSelectedCandidateOnly, syntheticUnselectedCandidateOnly],
      syntheticCandidateOnlyPaths,
      null,
    ) !== 2) {
    process.stderr.write("DOC_SELF_TEST_FAIL candidate-only counts must match the manifest selection when scoped and the checkout when unscoped\n");
    return false;
  }
  const synthetic = "scripts/core/__h3req1_undocumented_source_self_test__.mjs";
  const simulatedDiscovery = [...discovered, synthetic];
  const assignmentFailures = unassignedSourceFailures(simulatedDiscovery, assigned);
  if (!assignmentFailures.includes(`SOURCE_UNASSIGNED ${synthetic}`)) {
    process.stderr.write("DOC_SELF_TEST_FAIL new synthetic source did not trigger the gate failure\n");
    return false;
  }
  if (shouldScanSourceComments("none") || !shouldScanSourceComments("required") || !shouldScanSourceComments("optional")) {
    process.stderr.write("DOC_SELF_TEST_FAIL comment scan did not honor registry-only policy\n");
    return false;
  }
  const dockerOverrideSources = [
    ".context/operaciones/h3req1_docker_candidate_cutover_v4_override_2026-10-09.yml",
    ".context/operaciones/h3req1_docker_candidate_override_2026-10-09.yml",
  ];
  for (const relative of dockerOverrideSources) {
    if ((!discovered.includes(relative) && !candidateManifestOmissionAllowed(relative, candidateOnlyPaths, candidateScope))
      || !assigned.has(relative)) {
      process.stderr.write(`DOC_SELF_TEST_FAIL registered context source missing from discovery or assignment: ${relative}\n`);
      return false;
    }
  }
  const rootDirectories = fs.readdirSync(root, { withFileTypes: true }).filter((entry) => entry.isDirectory()).map((entry) => entry.name);
  const syntheticRootSource = "__h3req1_undocumented_root_self_test__/source.mjs";
  if (!unregisteredRootSources(registry, rootDirectories, [syntheticRootSource]).includes(syntheticRootSource)) {
    process.stderr.write("DOC_SELF_TEST_FAIL new root source was not rejected\n");
    return false;
  }
  const syntheticExtension = "scripts/core/__h3req1_unclassified_extension_self_test__.h3x";
  if (!unclassifiedSourceExtensions(registry, [syntheticExtension]).includes(syntheticExtension)) {
    process.stderr.write("DOC_SELF_TEST_FAIL new source extension was not rejected\n");
    return false;
  }
  const syntheticTopLevelExtension = "__h3req1_unclassified_top_level_self_test__.h3x";
  if (!unclassifiedSourceExtensions(registry, [syntheticTopLevelExtension]).includes(syntheticTopLevelExtension)) {
    process.stderr.write("DOC_SELF_TEST_FAIL unknown top-level source extension was not rejected\n");
    return false;
  }
  const syntheticExpectedComment = ".context/componentes/seguridad_tooling.md#registro-de-fuentes-y-gate";
  if (!sourceCommentIssues([".context/componentes/legacy.md#fuentes-y-relaciones"], syntheticExpectedComment, "required").some((issue) => issue.startsWith("registry_mismatch:"))) {
    process.stderr.write("DOC_SELF_TEST_FAIL comment/registry mismatch was not detected\n");
    return false;
  }
  const suffixedMarker = `// StudIAMatch-Docs: ${syntheticExpectedComment} documentation text`;
  const suffixRejected = sourceCommentIssues(sourceCommentMarkers(suffixedMarker), syntheticExpectedComment, "required")
    .some((issue) => issue.startsWith("malformed:"));
  const duplicateMarkers = sourceCommentMarkers(`// StudIAMatch-Docs: ${syntheticExpectedComment}\n// StudIAMatch-Docs: ${syntheticExpectedComment}`);
  const duplicateRejected = sourceCommentIssues(duplicateMarkers, syntheticExpectedComment, "required")
    .some((issue) => issue.startsWith("duplicate:"));
  const exactMarkerAccepted = sourceCommentIssues(sourceCommentMarkers(`// StudIAMatch-Docs: ${syntheticExpectedComment}`), syntheticExpectedComment, "required").length === 0;
  const htmlMarkerAccepted = sourceCommentIssues(sourceCommentMarkers(`<!-- StudIAMatch-Docs: ${syntheticExpectedComment} -->`), syntheticExpectedComment, "required").length === 0;
  if (!suffixRejected || !duplicateRejected || !exactMarkerAccepted || !htmlMarkerAccepted) {
    process.stderr.write(`DOC_SELF_TEST_FAIL comment marker must be brief and unique (suffix_rejected=${suffixRejected}, duplicate_rejected=${duplicateRejected})\n`);
    return false;
  }
  if (isCompleteRelation({ state: "unknown", note: "unclassified", evidence: [], resolution: "investigate" })) {
    process.stderr.write("DOC_SELF_TEST_FAIL generic unknown relation state was accepted\n");
    return false;
  }
  if (isCompleteRelation({ state: "remote_only", note: "requires separate remote read", evidence: [], resolution: "Read the approved target in a later session", remote_checks: [] })
    || !isCompleteRelation({ state: "remote_only", note: "requires separate remote read", evidence: [], resolution: "Read the approved target in a later session", remote_checks: ["remote-check-self-test"] })) {
    process.stderr.write("DOC_SELF_TEST_FAIL remote-only relation did not require and accept a named remote check\n");
    return false;
  }
  if (!validatePointer("scripts/__h3req1_missing_source_document__.md#missing")) {
    process.stderr.write("DOC_SELF_TEST_FAIL missing source document path was not detected\n");
    return false;
  }
  if (!validatePointer(".context/indice.md#__h3req1_missing_anchor")) {
    process.stderr.write("DOC_SELF_TEST_FAIL missing document anchor was not detected\n");
    return false;
  }
  const invalidNavigation = { ...registry, navigation: { ...registry.navigation, main_index: ".context/00_INDICE.md" } };
  if (!navigationContractFailures(invalidNavigation, registry.active_documents).some((issue) => issue.startsWith("NAVIGATION_MAIN_INDEX_INVALID"))) {
    process.stderr.write("DOC_SELF_TEST_FAIL a duplicate/retired main index was accepted\n");
    return false;
  }
  const retiredPresent = retiredDocumentFailures({ retired_documents: [{
    path: "README.md", kind: "self-test", reason: "synthetic retired-path check", replacement: [{ path: ".context/indice.md", anchor: "recorrido-por-el-sistema" }],
    backup_location: "/home/romel/backups/self-test/README.md", backup_sha256: "a".repeat(64), backup_verified_local: true, historical_snapshots_unchanged: true,
  }] }, [], new Map()).some((issue) => issue.startsWith("RETIRED_DOCUMENT_STILL_PRESENT"));
  if (!retiredPresent) {
    process.stderr.write("DOC_SELF_TEST_FAIL a retained retired document path was accepted\n");
    return false;
  }
  const syntheticCatalog = ".context/catalogos_historicos/__self_test__.md";
  const syntheticHistoricalPath = ".context/evidencia/__self_test__.md";
  const missingHistoricalLink = !markdownContainsLink("Clasificado en JSON, pero no enlazado.", syntheticCatalog, syntheticHistoricalPath);
  const presentHistoricalLink = markdownContainsLink("[evidencia](../evidencia/__self_test__.md)", syntheticCatalog, syntheticHistoricalPath);
  if (!missingHistoricalLink || !presentHistoricalLink) {
    process.stderr.write("DOC_SELF_TEST_FAIL historical classification must require an actual Markdown catalog link\n");
    return false;
  }
  const index = fs.readFileSync(path.join(root, ".context/indice.md"), "utf8");
  const staleIndex = index.replace(/(\| [^\n]+ \| \[[^\n]+\]\([^\n]+\) \| )(\d+)( \|)/,
    (_match, prefix, count, suffix) => `${prefix}${Number(count) + 1}${suffix}`);
  if (!historicalCatalogIndexFailures(registry, staleIndex).some((issue) => issue.startsWith("HISTORICAL_CATALOG_INDEX_DRIFT"))) {
    process.stderr.write("DOC_SELF_TEST_FAIL stale historical catalog count was accepted in the Obsidian index\n");
    return false;
  }
  process.stdout.write("DOC_SELF_TEST_PASS shared gate rejects unassigned sources, allows only exact registered unselected omissions under a manifest, rejects unlisted/selected/default-mode omissions, generic unknown relations, incomplete remote-only relations, unlinked historical documents, stale index catalog counts, confirms Docker override assignments, skips content reads for comment policy none, rejects unregistered roots/extensions, comment/registry mismatch, malformed/duplicate markers, missing path/anchor, a duplicate main index and a retired document that remains in the tree\n");
  return true;
}

function linkCheck(activeDocuments, failures) {
  const contents = new Map();
  for (const relative of activeDocuments) {
    if (!pathExists(relative)) {
      failures.push(`DOC_MISSING ${relative}`);
      continue;
    }
    contents.set(relative, fs.readFileSync(path.join(root, relative), "utf8"));
  }
  if (!contents.has(".context/trazabilidad/registro_fuentes_componentes.md") && pathExists(registryMarkdownPath)) {
    contents.set(registryMarkdownPath, fs.readFileSync(path.join(root, registryMarkdownPath), "utf8"));
  }
  const adjacency = new Map();
  let checkedLinks = 0;
  let checkedAnchors = 0;
  for (const [source, markdown] of contents) {
    const localTargets = [];
    for (const raw of linksIn(markdown)) {
      const resolved = resolveTarget(source, raw);
      if (!resolved) continue;
      checkedLinks += 1;
      if (resolved.error) {
        failures.push(`DOC_LINK_ERROR ${source}: ${raw} (${resolved.error})`);
        continue;
      }
      if (!pathExists(resolved.relative)) {
        failures.push(`DOC_LINK_ERROR ${source}: ${raw} (target missing)`);
        continue;
      }
      if (resolved.fragment && path.extname(resolved.relative).toLowerCase() === ".md") {
        checkedAnchors += 1;
        if (!markdownAnchorExists(resolved.relative, resolved.fragment)) {
          failures.push(`DOC_ANCHOR_ERROR ${source}: ${raw}`);
        }
      }
      if (contents.has(resolved.relative)) localTargets.push(resolved.relative);
    }
    adjacency.set(source, localTargets);
  }
  const entry = ".context/indice.md";
  const reachable = new Set([entry]);
  const queue = [entry];
  while (queue.length) {
    const current = queue.shift();
    for (const target of adjacency.get(current) ?? []) {
      if (reachable.has(target)) continue;
      reachable.add(target);
      queue.push(target);
    }
  }
  for (const relative of activeDocuments) {
    if (!reachable.has(relative)) failures.push(`DOC_ORPHAN ${relative} is not reachable from .context/indice.md`);
  }
  return { checkedLinks, checkedAnchors, reachable: reachable.size };
}

function historicalDocumentFailures(registry, discoveredDocuments, activeDocuments, excludedDocumentPaths, candidateScope, exactDocumentExclusionPaths) {
  const failures = [];
  const catalogs = new Map();
  const catalogPaths = new Set();
  const historicalPaths = new Set();
  const documentCounts = new Map();
  const relationNames = ["sources", "runner", "tests", "manifests", "results"];
  const validRelationStates = new Set(["identified", "not_identified_in_local_search", "not_found_in_local_search", "not_reviewed", "not_applicable", "unknown"]);
  const validDocumentStatuses = new Set(["historical", "current", "superseded"]);

  for (const catalog of registry.historical_catalogs ?? []) {
    if (!catalog.id || catalogs.has(catalog.id)) failures.push("HISTORICAL_CATALOG_ID_INVALID_OR_DUPLICATE " + (catalog.id ?? "(missing)"));
    catalogs.set(catalog.id, catalog);
    if (!catalog.path || catalogPaths.has(catalog.path)) failures.push("HISTORICAL_CATALOG_PATH_INVALID_OR_DUPLICATE " + (catalog.path ?? "(missing)"));
    catalogPaths.add(catalog.path);
    if (!catalog.title || !catalog.purpose || !Array.isArray(catalog.component_ids) || !Array.isArray(catalog.module_links)) {
      failures.push("HISTORICAL_CATALOG_METADATA_INCOMPLETE " + (catalog.id ?? "(missing)"));
    }
    const pointerError = validatePointer((catalog.path ?? "") + "#" + (catalog.anchor ?? ""));
    if (pointerError) failures.push("HISTORICAL_CATALOG_POINTER_INVALID " + catalog.id + ": " + pointerError);
    if (!activeDocuments.has(catalog.path)) failures.push("HISTORICAL_CATALOG_NOT_ACTIVE " + catalog.path);
    const rendered = renderHistoricalCatalogMarkdown(registry, catalog);
    if (pathExists(catalog.path) && fs.readFileSync(path.join(root, catalog.path), "utf8") !== rendered) {
      failures.push("HISTORICAL_CATALOG_MARKDOWN_DRIFT " + catalog.path + "; run --render after editing the canonical JSON");
    }
    const moduleIds = new Set();
    for (const module of catalog.module_links ?? []) {
      if (moduleIds.has(module.component_id)) failures.push("HISTORICAL_CATALOG_MODULE_DUPLICATE " + catalog.id + ": " + module.component_id);
      moduleIds.add(module.component_id);
      const component = registry.components.find((item) => item.id === module.component_id);
      const moduleError = validatePointer((module.path ?? "") + "#" + (module.anchor ?? ""));
      if (!component || component.document.path !== module.path) failures.push("HISTORICAL_CATALOG_MODULE_INVALID " + catalog.id + ": " + (module.component_id ?? "(missing)"));
      if (moduleError) failures.push("HISTORICAL_CATALOG_MODULE_POINTER_INVALID " + catalog.id + ": " + moduleError);
      if (pathExists(module.path) && !markdownLinksTo(module.path, catalog.path, catalog.anchor)) {
        failures.push("HISTORICAL_CATALOG_MODULE_BACKLINK_MISSING " + module.path + " -> " + catalog.path + "#" + catalog.anchor);
      }
      if (pathExists(catalog.path) && !markdownLinksTo(catalog.path, module.path, module.anchor)) {
        failures.push("HISTORICAL_CATALOG_BACKLINK_MISSING " + catalog.path + " -> " + module.path + "#" + module.anchor);
      }
      if (!catalog.component_ids.includes(module.component_id)) failures.push("HISTORICAL_CATALOG_COMPONENT_SET_MISMATCH " + catalog.id + ": " + module.component_id);
    }
    if (moduleIds.size === 0) failures.push("HISTORICAL_CATALOG_WITHOUT_MODULE_LINK " + catalog.id);
    if (pathExists(registry.navigation?.main_index) && !markdownLinksTo(registry.navigation.main_index, catalog.path, catalog.anchor)) {
      failures.push("HISTORICAL_CATALOG_NOT_LINKED_FROM_MAIN_INDEX " + catalog.path);
    }
  }

  const navigationCatalogs = registry.navigation?.historical_catalogs ?? [];
  if (navigationCatalogs.length !== catalogs.size) failures.push("HISTORICAL_NAVIGATION_CATALOG_COUNT_MISMATCH " + navigationCatalogs.length + " != " + catalogs.size);
  const navigationPointers = new Set();
  for (const pointer of navigationCatalogs) {
    const key = pointer.path + "#" + pointer.anchor;
    if (navigationPointers.has(key)) failures.push("HISTORICAL_NAVIGATION_CATALOG_DUPLICATE " + key);
    navigationPointers.add(key);
    if (!catalogPaths.has(pointer.path)) failures.push("HISTORICAL_NAVIGATION_CATALOG_UNKNOWN " + key);
  }

  for (const document of registry.historical_documents ?? []) {
    const relative = document.path;
    if (!relative || historicalPaths.has(relative)) failures.push("HISTORICAL_DOCUMENT_PATH_INVALID_OR_DUPLICATE " + (relative ?? "(missing)"));
    historicalPaths.add(relative);
    documentCounts.set(document.catalog_id, (documentCounts.get(document.catalog_id) ?? 0) + 1);
    if (!discoveredDocuments.includes(relative) || !pathExists(relative)) failures.push("HISTORICAL_DOCUMENT_PATH_MISSING " + (relative ?? "(missing)"));
    if (activeDocuments.has(relative)) failures.push("DOCUMENT_ACTIVE_AND_HISTORICAL " + relative);
    if (excludedDocumentPaths.has(relative)) failures.push("DOCUMENT_HISTORICAL_AND_EXCLUDED " + relative);
    const catalog = catalogs.get(document.catalog_id);
    if (!catalog) {
      failures.push("HISTORICAL_DOCUMENT_CATALOG_MISSING " + relative + ": " + document.catalog_id);
      continue;
    }
    if (document.catalog?.path !== catalog.path || document.catalog?.anchor !== catalog.anchor) {
      failures.push("HISTORICAL_DOCUMENT_CATALOG_POINTER_MISMATCH " + relative);
    }
    if (pathExists(catalog.path)) {
      const catalogContents = fs.readFileSync(path.join(root, catalog.path), "utf8");
      if (!markdownContainsLink(catalogContents, catalog.path, relative)) failures.push("HISTORICAL_DOCUMENT_NOT_LINKED_FROM_CATALOG " + relative + " via " + catalog.path);
    }
    if (!validDocumentStatuses.has(document.status)) failures.push("HISTORICAL_DOCUMENT_STATUS_INVALID " + relative + ": " + document.status);
    for (const key of ["title", "purpose", "purpose_basis", "component_basis", "requirement_basis", "status_note", "preservation_reason", "content_review", "sequence_basis"]) {
      if (typeof document[key] !== "string" || !document[key].trim()) failures.push("HISTORICAL_DOCUMENT_METADATA_INCOMPLETE " + relative + ": " + key);
    }
    if (!Array.isArray(document.component_ids) || document.component_ids.length === 0) failures.push("HISTORICAL_DOCUMENT_COMPONENT_MISSING " + relative);
    for (const componentId of document.component_ids ?? []) {
      if (!registry.components.some((component) => component.id === componentId)) failures.push("HISTORICAL_DOCUMENT_COMPONENT_UNKNOWN " + relative + ": " + componentId);
      if (!catalog.component_ids.includes(componentId)) failures.push("HISTORICAL_DOCUMENT_COMPONENT_NOT_IN_CATALOG " + relative + ": " + componentId);
    }
    for (const key of relationNames) {
      const relation = document.relations?.[key];
      if (!relation || !validRelationStates.has(relation.state) || typeof relation.note !== "string" || !relation.note.trim() || !Array.isArray(relation.paths)) {
        failures.push("HISTORICAL_RELATION_INCOMPLETE " + relative + ": " + key);
        continue;
      }
      const pathField = { sources: "source_paths", runner: "runner_paths", tests: "test_paths", manifests: "manifest_paths", results: "result_paths" }[key];
      const declared = [...new Set(document[pathField] ?? [])].sort();
      const relationPaths = [...new Set(relation.paths)].sort();
      if (JSON.stringify(declared) !== JSON.stringify(relationPaths)) failures.push("HISTORICAL_RELATION_PATHS_DISAGREE " + relative + ": " + key);
      if (relation.state === "identified" && relation.paths.length === 0) failures.push("HISTORICAL_RELATION_IDENTIFIED_WITHOUT_PATH " + relative + ": " + key);
      if (["not_identified_in_local_search", "not_found_in_local_search"].includes(relation.state)
        && !/(scope|b[uú]squ|searched|rg --files|no demuestra|no demuestra)/i.test(relation.note)) {
        failures.push("HISTORICAL_RELATION_SEARCH_SCOPE_MISSING " + relative + ": " + key);
      }
      for (const relatedPath of relation.paths) {
        if (!pathExists(relatedPath)) failures.push("HISTORICAL_RELATION_PATH_MISSING " + relative + ": " + relatedPath);
        else if (pathExists(catalog.path) && !markdownLinksTo(catalog.path, relatedPath)) failures.push("HISTORICAL_RELATION_PATH_NOT_LINKED " + relative + ": " + relatedPath);
      }
    }
    for (const relatedPath of [...(document.predecessor_paths ?? []), ...(document.successor_paths ?? [])]) {
      if (!pathExists(relatedPath)) failures.push("HISTORICAL_SEQUENCE_PATH_MISSING " + relative + ": " + relatedPath);
      else if (pathExists(catalog.path) && !markdownLinksTo(catalog.path, relatedPath)) failures.push("HISTORICAL_SEQUENCE_PATH_NOT_LINKED " + relative + ": " + relatedPath);
    }
  }

  const origins = registry.historical_document_origins ?? [];
  const originSpecificity = (origin) => origin.pattern.replace(/\*/g, "").length;
  const selectedOrigin = (relative) => origins
    .filter((origin) => globMatches(origin.pattern, relative))
    .sort((left, right) => originSpecificity(right) - originSpecificity(left))[0];
  for (const origin of origins) {
    if (!origin.pattern || !origin.reason || !origin.retention || !Number.isInteger(origin.paths) || origin.paths < 0) {
      failures.push("HISTORICAL_ORIGIN_UNJUSTIFIED " + (origin.pattern ?? "(missing)"));
      continue;
    }
    // More specific exact/child families take precedence over broad directory families.
    const actualMatches = [...historicalPaths].filter((relative) => selectedOrigin(relative) === origin);
    if (actualMatches.length !== origin.paths) failures.push("HISTORICAL_ORIGIN_COUNT_MISMATCH " + origin.pattern + ": " + actualMatches.length + " != " + origin.paths);
    for (const relative of actualMatches) if (!pathExists(relative)) failures.push("HISTORICAL_ORIGIN_PATH_MISSING " + relative);
  }
  for (const relative of historicalPaths) {
    const matchingOrigins = origins.filter((origin) => globMatches(origin.pattern, relative));
    const bestSpecificity = Math.max(-1, ...matchingOrigins.map(originSpecificity));
    const bestCount = matchingOrigins.filter((origin) => originSpecificity(origin) === bestSpecificity).length;
    if (bestCount !== 1) failures.push("HISTORICAL_ORIGIN_COUNT_INVALID " + relative + ": " + bestCount);
    if (!discoveredDocuments.includes(relative)) failures.push("HISTORICAL_DOCUMENT_STALE " + relative);
  }
  for (const relative of discoveredDocuments) {
    if (!activeDocuments.has(relative) && !historicalPaths.has(relative) && !excludedDocumentPaths.has(relative)) {
      failures.push("DOC_UNCLASSIFIED " + relative + "; classify as active, historical-cataloged, or excluded with reason");
    }
  }
  for (const relative of activeDocuments) if (!discoveredDocuments.includes(relative)) failures.push("ACTIVE_DOC_NOT_DISCOVERED " + relative);
  for (const relative of excludedDocumentPaths) {
    if (!discoveredDocuments.includes(relative)
      && !candidateManifestOmissionAllowed(relative, exactDocumentExclusionPaths, candidateScope)) failures.push("DOC_EXCLUSION_STALE " + relative);
    if (historicalPaths.has(relative)) failures.push("DOC_EXCLUSION_OVERLAPS_HISTORICAL " + relative);
  }
  const catalogedCount = historicalPaths.size;
  const linkedCount = [...historicalPaths].filter((relative) => {
    const document = (registry.historical_documents ?? []).find((item) => item.path === relative);
    const catalog = catalogs.get(document?.catalog_id);
    return catalog && pathExists(catalog.path) && markdownLinksTo(catalog.path, relative);
  }).length;
  return { failures, historicalCount: historicalPaths.size, catalogedCount, linkedCount, catalogCount: catalogs.size, documentCounts };
}

function navigationContractFailures(registry, activeDocuments) {
  const failures = [];
  const navigation = registry.navigation ?? {};
  const entry = navigation.main_index;
  const rootReadme = navigation.root_readme;
  if (entry !== ".context/indice.md") failures.push(`NAVIGATION_MAIN_INDEX_INVALID ${entry ?? "(missing)"}`);
  if (!entry || !pathExists(entry)) failures.push(`NAVIGATION_MAIN_INDEX_MISSING ${entry ?? "(missing)"}`);
  if (entry && !activeDocuments.includes(entry)) failures.push(`NAVIGATION_MAIN_INDEX_NOT_ACTIVE ${entry}`);
  if (entry === ".context/indice.md" && pathExists(entry)) {
    failures.push(...historicalCatalogIndexFailures(registry, fs.readFileSync(path.join(root, entry), "utf8")));
  }
  if (!rootReadme || !pathExists(rootReadme)) failures.push(`NAVIGATION_ROOT_README_MISSING ${rootReadme ?? "(missing)"}`);
  if (rootReadme && pathExists(rootReadme)) {
    const targets = linksIn(fs.readFileSync(path.join(root, rootReadme), "utf8"))
      .map((raw) => resolveTarget(rootReadme, raw))
      .filter((resolved) => resolved && !resolved.error);
    const contextTargets = targets.filter((resolved) => resolved.relative.startsWith(".context/"));
    const entryLinks = contextTargets.filter((resolved) => resolved.relative === entry);
    if (entryLinks.length !== 1 || contextTargets.length !== 1) {
      failures.push(`NAVIGATION_ROOT_README_ENTRY_INVALID ${rootReadme} must link only once to ${entry}`);
    }
  }
  const subordinate = navigation.subordinate_indexes ?? [];
  if (new Set(subordinate).size !== subordinate.length) failures.push("NAVIGATION_SUBORDINATE_INDEX_DUPLICATE");
  for (const relative of subordinate) {
    if (relative === entry) failures.push(`NAVIGATION_SUBORDINATE_IS_MAIN ${relative}`);
    if (!pathExists(relative)) failures.push(`NAVIGATION_SUBORDINATE_MISSING ${relative}`);
    if (!activeDocuments.includes(relative)) failures.push(`NAVIGATION_SUBORDINATE_NOT_ACTIVE ${relative}`);
  }
  return failures;
}

function retiredDocumentFailures(registry, activeDocuments, assigned) {
  const failures = [];
  const retired = registry.retired_documents ?? [];
  const seen = new Set();
  for (const item of retired) {
    const relative = item.path;
    if (!relative || seen.has(relative)) {
      failures.push(`RETIRED_DOCUMENT_PATH_MISSING_OR_DUPLICATE ${relative ?? "(missing)"}`);
      continue;
    }
    seen.add(relative);
    if (pathExists(relative)) failures.push(`RETIRED_DOCUMENT_STILL_PRESENT ${relative}`);
    if (assigned.has(relative)) failures.push(`RETIRED_DOCUMENT_STILL_ASSIGNED ${relative}`);
    if (activeDocuments.includes(relative)) failures.push(`RETIRED_DOCUMENT_STILL_ACTIVE ${relative}`);
    if (!item.kind || !item.reason || !item.historical_snapshots_unchanged) failures.push(`RETIRED_DOCUMENT_UNJUSTIFIED ${relative}`);
    if (item.backup_verified_local !== true || !path.isAbsolute(item.backup_location ?? "")
      || path.resolve(item.backup_location).startsWith(`${root}${path.sep}`)
      || !/^[0-9a-f]{64}$/i.test(item.backup_sha256 ?? "")) {
      failures.push(`RETIRED_DOCUMENT_BACKUP_UNVERIFIED ${relative}`);
    }
    if (!Array.isArray(item.replacement) || item.replacement.length === 0) {
      failures.push(`RETIRED_DOCUMENT_REPLACEMENT_MISSING ${relative}`);
      continue;
    }
    for (const replacement of item.replacement) {
      const error = validatePointer(`${replacement.path ?? ""}#${replacement.anchor ?? ""}`);
      if (error) failures.push(`RETIRED_DOCUMENT_REPLACEMENT_INVALID ${relative}: ${error}`);
    }
    for (const source of activeDocuments) {
      if (!pathExists(source)) continue;
      const markdown = fs.readFileSync(path.join(root, source), "utf8");
      for (const raw of linksIn(markdown)) {
        const target = resolveTarget(source, raw);
        if (target && !target.error && target.relative === relative) {
          failures.push(`RETIRED_DOCUMENT_LINK_REMAINS ${source}: ${relative}`);
        }
      }
    }
  }
  return failures;
}

function main() {
  const registry = readJson(registryPath);
  let candidateScope;
  try {
    candidateScope = candidateScopeFromArgs();
  } catch (error) {
    process.stderr.write(`DOC_GATE_FAIL CANDIDATE_MANIFEST_INVALID ${String(error.message).replace(/[\r\n\t]/g, " ")}\n`);
    return 1;
  }
  if (requestedMode.includes("--render")) {
    if (candidateScope) {
      process.stderr.write("DOC_GATE_FAIL CANDIDATE_MANIFEST_RENDER_FORBIDDEN use the default --render mode\n");
      return 1;
    }
    for (const [relative, contents] of generatedDocumentation(registry)) {
      fs.mkdirSync(path.dirname(path.join(root, relative)), { recursive: true });
      fs.writeFileSync(path.join(root, relative), contents, "utf8");
      process.stdout.write(`DOC_MARKDOWN_RENDERED ${relative}\n`);
    }
    return 0;
  }

  const failures = [];
  const discovered = discoverSources(registry);
  const { assigned, duplicate } = groupForPath(registry);
  const candidateOnlyPaths = new Set(registry.groups.flatMap((group) => group.candidate_only_paths ?? []));
  const exactSourceExclusionPaths = new Set(registry.exclusions.flatMap((item) => item.paths ?? []));
  const exactDocumentExclusionPaths = new Set((registry.document_exclusions ?? []).flatMap((item) => item.paths ?? []));
  if (candidateScope) {
    for (const relative of candidateScope.selectedPaths) {
      if (!pathExists(relative)) failures.push(`CANDIDATE_MANIFEST_PATH_MISSING ${relative}`);
    }
  }
  for (const relative of unregisteredRootSources(registry)) failures.push(`SOURCE_ROOT_UNREGISTERED ${relative}; register the root or justify its exclusion`);
  for (const relative of unclassifiedSourceExtensions(registry)) failures.push(`SOURCE_EXTENSION_UNCLASSIFIED ${relative}; register its extension/exact name or justify its exclusion`);
  for (const relative of duplicate) failures.push(`SOURCE_DUPLICATE_ASSIGNMENT ${relative}`);
  const stale = [...assigned.keys()].filter((relative) => !discovered.includes(relative)
    && !candidateManifestOmissionAllowed(relative, candidateOnlyPaths, candidateScope));
  failures.push(...unassignedSourceFailures(discovered, assigned));
  for (const relative of stale) failures.push(`SOURCE_PATH_MISSING_OR_OUT_OF_SCOPE ${relative}`);

  const validStatuses = new Set(["current", "legacy", "diagnostic-wip", "unknown"]);
  const validRelationStates = new Set(["verified", "pending", "remote_only", "not_applicable"]);
  const relationKeys = ["contracts", "consumers", "data", "tests_evidence", "operations", "provenance"];
  const components = new Map(registry.components.map((item) => [item.id, item]));
  const groupsByComponent = new Map();
  let relationTotal = 0;
  let verifiedRelations = 0;
  let pendingRelations = 0;
  let unknownRelations = 0;
  let invalidRelations = 0;
  let remoteOnlyRelations = 0;
  let notApplicableRelations = 0;
  let structurallyVerifiedSources = 0;
  let fullyVerifiedSources = 0;
  const seenCandidateOnlyPaths = new Set();
  for (const group of registry.groups) {
    const component = components.get(group.component);
    if (!component) {
      failures.push(`COMPONENT_MISSING ${group.id} -> ${group.component}`);
      relationTotal += group.paths.length * relationKeys.length;
      invalidRelations += group.paths.length * relationKeys.length;
      continue;
    }
    groupsByComponent.set(group.component, (groupsByComponent.get(group.component) ?? 0) + group.paths.length);
    if (typeof group.purpose !== "string" || !group.purpose.trim()) failures.push(`COMPONENT_PURPOSE_MISSING ${group.id}`);
    if (!["required", "optional", "none"].includes(group.inline_comment)) failures.push(`COMMENT_POLICY_INVALID ${group.id}`);
    if (!Array.isArray(group.candidate_only_paths)) failures.push(`CANDIDATE_ONLY_PATHS_MISSING ${group.id}`);
    for (const relative of group.candidate_only_paths ?? []) {
      if (!group.paths.includes(relative)) failures.push(`CANDIDATE_ONLY_PATH_NOT_ASSIGNED ${group.id}: ${relative}`);
      if (seenCandidateOnlyPaths.has(relative)) failures.push(`CANDIDATE_ONLY_PATH_DUPLICATE ${relative}`);
      seenCandidateOnlyPaths.add(relative);
      if (!discovered.includes(relative) && !candidateManifestOmissionAllowed(relative, candidateOnlyPaths, candidateScope)) {
        failures.push(`CANDIDATE_ONLY_PATH_MISSING ${relative}`);
      }
    }
    const sourceDocument = group.source_document;
    if (!sourceDocument?.path || !sourceDocument?.anchor) {
      failures.push(`SOURCE_DOCUMENT_POINTER_MISSING ${group.id}`);
    } else {
      const sourceDocumentError = validatePointer(`${sourceDocument.path}#${sourceDocument.anchor}`);
      if (sourceDocumentError) failures.push(`SOURCE_DOCUMENT_POINTER_INVALID ${group.id}: ${sourceDocumentError}`);
      if (!registry.active_documents.includes(sourceDocument.path)) failures.push(`SOURCE_DOCUMENT_NOT_ACTIVE ${group.id}: ${sourceDocument.path}`);
    }
    for (const relative of group.paths) {
      if (!discovered.includes(relative) && !candidateManifestOmissionAllowed(relative, candidateOnlyPaths, candidateScope)) {
        failures.push(`SOURCE_PATH_MISSING ${relative}`);
      }
      if (!validStatuses.has(group.status)) failures.push(`SOURCE_STATUS_INVALID ${relative}: ${group.status}`);
      const binaryAsset = new Set([".png", ".jpg", ".jpeg", ".webp", ".ico", ".woff", ".woff2", ".ttf", ".otf"])
        .has(path.extname(relative).toLowerCase());
      if (pathExists(relative) && !binaryAsset && shouldScanSourceComments(group.inline_comment)) {
        const source = fs.readFileSync(path.join(root, relative), "utf8");
        const markerMatches = sourceCommentMarkers(source);
        const expected = group.comment_target ?? `${sourceDocument?.path ?? component.document.path}#${sourceDocument?.anchor ?? component.document.anchor}`;
        if (group.comment_target) {
          const commentPointerError = validatePointer(group.comment_target);
          if (commentPointerError) failures.push(`SOURCE_COMMENT_TARGET_INVALID ${group.id}: ${commentPointerError}`);
          const commentTargetPath = pointerParts(group.comment_target).path;
          if (!registry.active_documents.includes(commentTargetPath)) failures.push(`SOURCE_COMMENT_TARGET_NOT_ACTIVE ${group.id}: ${commentTargetPath}`);
        }
        for (const issue of sourceCommentIssues(markerMatches, expected, group.inline_comment)) {
          if (issue.startsWith("missing_or_mismatched:")) failures.push(`SOURCE_COMMENT_MISSING_OR_MISMATCHED ${relative}: expected ${expected}`);
          else if (issue.startsWith("unexpected:")) failures.push(`SOURCE_COMMENT_UNEXPECTED ${relative}: policy=none found=${issue.slice("unexpected:".length)}`);
          else if (issue.startsWith("malformed:")) failures.push(`SOURCE_COMMENT_NOT_BRIEF ${relative}: marker must contain one route only`);
          else if (issue.startsWith("duplicate:")) failures.push(`SOURCE_COMMENT_DUPLICATE ${relative}: expected exactly one marker`);
          else failures.push(`SOURCE_COMMENT_REGISTRY_MISMATCH ${relative}: ${issue.slice("registry_mismatch:".length).replace("!=", " != ")}`);
        }
      }
    }
    for (const relationKey of relationKeys) {
      const relation = group[relationKey];
      if (!isCompleteRelation(relation) || !validRelationStates.has(relation.state)) {
        failures.push(`RELATION_INCOMPLETE ${group.id}.${relationKey}`);
        if (relation?.state === "unknown") {
          failures.push(`RELATION_UNKNOWN_STATE_FORBIDDEN ${group.id}.${relationKey}`);
          unknownRelations += group.paths.length;
        } else if (relation?.state === "pending") {
          pendingRelations += group.paths.length;
        } else {
          invalidRelations += group.paths.length;
        }
        relationTotal += group.paths.length;
        continue;
      }
      relationTotal += group.paths.length;
      if (relation.state === "verified") verifiedRelations += group.paths.length;
      else if (relation.state === "pending") pendingRelations += group.paths.length;
      else if (relation.state === "remote_only") remoteOnlyRelations += group.paths.length;
      else if (relation.state === "not_applicable") notApplicableRelations += group.paths.length;
      if (relation.state === "verified" && relation.evidence.length === 0) {
        failures.push(`RELATION_VERIFIED_WITHOUT_EVIDENCE ${group.id}.${relationKey}`);
      }
      for (const item of relation.evidence) {
        if (typeof item === "string" && item.startsWith("path:")) {
          const evidencePath = item.slice("path:".length);
          if (!pathExists(evidencePath) && !candidateManifestOmissionAllowed(evidencePath, candidateOnlyPaths, candidateScope)) {
            failures.push(`RELATION_PATH_MISSING ${group.id}.${relationKey}: ${evidencePath}`);
          }
        }
        if (typeof item === "string" && item.startsWith("commit:")) {
          const commit = item.slice("commit:".length);
          if (!/^[0-9a-f]{7,40}$/i.test(commit)) failures.push(`RELATION_COMMIT_FORMAT_INVALID ${group.id}.${relationKey}: ${commit}`);
        }
      }
      for (const remoteId of relation.remote_checks ?? []) {
        if (!registry.remote_checks?.some((item) => item.id === remoteId)) failures.push(`REMOTE_CHECK_REFERENCE_MISSING ${group.id}.${relationKey}: ${remoteId}`);
      }
    }
    const docOkay = !validatePointer(`${component.document.path}#${component.document.anchor}`)
      && component.domain_documents.length > 0
      && component.domain_documents.every((item) => !validatePointer(`${item.path}#${item.anchor}`)
        && (markdownLinksTo(item.path, component.document.path, component.document.anchor)
          || markdownLinksTo(item.path, registryMarkdownPath)));
    const relationsOkay = relationKeys.every((key) => ["verified", "not_applicable"].includes(group[key]?.state));
    for (const relative of group.paths) {
      if (discovered.includes(relative) && assigned.get(relative) === group && docOkay) structurallyVerifiedSources += 1;
      if (discovered.includes(relative) && assigned.get(relative) === group && docOkay && relationsOkay) fullyVerifiedSources += 1;
    }
  }

  const remoteChecks = registry.remote_checks ?? [];
  const remoteCheckIds = new Set();
  let remoteChecksVerified = 0;
  for (const check of remoteChecks) {
    if (!check.id || remoteCheckIds.has(check.id)) failures.push(`REMOTE_CHECK_ID_INVALID_OR_DUPLICATE ${check.id ?? "(missing)"}`);
    remoteCheckIds.add(check.id);
    if (!components.has(check.component)) failures.push(`REMOTE_CHECK_COMPONENT_MISSING ${check.id}: ${check.component}`);
    if (typeof check.question !== "string" || !check.question.trim() || typeof check.method !== "string" || !check.method.trim()
      || typeof check.owner !== "string" || !check.owner.trim() || !Array.isArray(check.sources) || check.sources.length === 0) {
      failures.push(`REMOTE_CHECK_INCOMPLETE ${check.id}`);
    }
    if (!["pending_separate_session", "verified"].includes(check.status)) failures.push(`REMOTE_CHECK_STATUS_INVALID ${check.id}: ${check.status}`);
    if (check.status === "verified") {
      remoteChecksVerified += 1;
      if (!Array.isArray(check.evidence) || check.evidence.length === 0 || !check.verified_at) failures.push(`REMOTE_CHECK_VERIFIED_WITHOUT_EVIDENCE ${check.id}`);
    }
    for (const source of check.sources ?? []) {
      if (!pathExists(source)) failures.push(`REMOTE_CHECK_SOURCE_MISSING ${check.id}: ${source}`);
    }
  }
  for (const group of registry.groups) {
    for (const key of relationKeys) {
      const relation = group[key];
      for (const remoteId of relation?.remote_checks ?? []) {
        if (!remoteCheckIds.has(remoteId)) failures.push(`REMOTE_CHECK_REFERENCE_MISSING ${group.id}.${key}: ${remoteId}`);
      }
    }
  }

  for (const component of registry.components) {
    if (!groupsByComponent.has(component.id)) failures.push(`COMPONENT_WITHOUT_SOURCE ${component.id}`);
    const componentPointer = `${component.document.path}#${component.document.anchor}`;
    const pointerError = validatePointer(componentPointer);
    if (pointerError) failures.push(`COMPONENT_DOCUMENT_INVALID ${component.id}: ${pointerError}`);
    for (const domain of component.domain_documents) {
      const domainError = validatePointer(`${domain.path}#${domain.anchor}`);
      if (domainError) failures.push(`DOMAIN_DOCUMENT_INVALID ${component.id}: ${domainError}`);
      if (pathExists(domain.path) && !markdownLinksTo(domain.path, component.document.path, component.document.anchor)
        && !markdownLinksTo(domain.path, registryMarkdownPath)) {
        failures.push(`DOMAIN_BACKLINK_MISSING ${component.id}: ${domain.path} must link to component doc or source registry`);
      }
    }
    if (pathExists(component.document.path)) {
      if (!markdownLinksTo(component.document.path, registryMarkdownPath)) failures.push(`COMPONENT_BACKLINK_MISSING ${component.id} -> ${registryMarkdownPath}`);
    }
  }

  for (const exclusion of registry.exclusions) {
    if (!exclusion.pattern || !exclusion.kind || !exclusion.reason || !exclusion.document?.path || !exclusion.document?.anchor || !exclusion.retention || !exclusion.evidence) {
      failures.push(`EXCLUSION_UNJUSTIFIED ${exclusion.pattern ?? "<missing pattern>"}`);
      continue;
    }
    if (exclusion.allow_family_pattern === true && !/(cache|dependencia|generad|captura|log|artefact|estado|runtime|evidencia)/i.test(exclusion.kind)) {
      failures.push(`EXCLUSION_FAMILY_PATTERN_UNJUSTIFIED ${exclusion.pattern}: ${exclusion.kind}`);
    }
    const error = validatePointer(`${exclusion.document.path}#${exclusion.document.anchor}`);
    if (error) failures.push(`EXCLUSION_DOCUMENT_INVALID ${exclusion.pattern}: ${error}`);
    if (!Array.isArray(exclusion.paths)) failures.push(`EXCLUSION_PATHS_MISSING ${exclusion.pattern}`);
    for (const relative of exclusion.paths ?? []) {
      if (!pathExists(relative)
        && !candidateManifestOmissionAllowed(relative, exactSourceExclusionPaths, candidateScope)) failures.push(`EXCLUSION_PATH_MISSING ${exclusion.pattern}: ${relative}`);
      if (assigned.has(relative)) failures.push(`EXCLUSION_SOURCE_OVERLAP ${relative}`);
      if (!globMatches(exclusion.pattern, relative) && !exclusion.exact_path) failures.push(`EXCLUSION_PATTERN_MISMATCH ${exclusion.pattern}: ${relative}`);
    }
  }
  for (const entry of registry.discovery.non_source_roots ?? []) {
    if (!entry.path || !entry.reason || !entry.document?.path || !entry.document?.anchor) {
      failures.push(`NON_SOURCE_ROOT_UNJUSTIFIED ${entry.path ?? "<missing path>"}`);
      continue;
    }
    try {
      if (!fs.statSync(path.join(root, entry.path)).isDirectory()) failures.push(`NON_SOURCE_ROOT_NOT_DIRECTORY ${entry.path}`);
    } catch {
      failures.push(`NON_SOURCE_ROOT_MISSING ${entry.path}`);
    }
    const error = validatePointer(`${entry.document.path}#${entry.document.anchor}`);
    if (error) failures.push(`NON_SOURCE_ROOT_DOCUMENT_INVALID ${entry.path}: ${error}`);
  }
  const gitMetadata = registry.discovery.git_metadata;
  if (!gitMetadata?.name || !gitMetadata.reason || !gitMetadata.document?.path || !gitMetadata.document?.anchor) {
    failures.push("GIT_METADATA_EXCLUSION_UNJUSTIFIED");
  } else {
    const error = validatePointer(`${gitMetadata.document.path}#${gitMetadata.document.anchor}`);
    if (error) failures.push(`GIT_METADATA_DOCUMENT_INVALID ${gitMetadata.name}: ${error}`);
  }
  for (const family of registry.artifact_families) {
    for (const key of ["pattern", "producer", "inputs", "purpose", "location", "retention", "evidence"]) {
      if (!family[key]) failures.push(`ARTIFACT_FAMILY_INCOMPLETE ${family.pattern ?? "<missing pattern>"}.${key}`);
    }
  }

  for (const [relative, rendered] of generatedDocumentation(registry)) {
    if (!pathExists(relative) || fs.readFileSync(path.join(root, relative), "utf8") !== rendered) {
      failures.push(`${relative === registryMarkdownPath ? "REGISTRY_MARKDOWN_DRIFT" : "HISTORICAL_CATALOG_MARKDOWN_DRIFT"} ${relative}; run --render after editing JSON`);
    }
  }

  const activeDocuments = [...new Set([...registry.active_documents, registryMarkdownPath])];
  failures.push(...navigationContractFailures(registry, activeDocuments));
  failures.push(...retiredDocumentFailures(registry, activeDocuments, assigned));
  const discoveredDocuments = discoverContextDocuments();
  const activeDocumentSet = new Set(activeDocuments);
  const excludedDocumentPaths = new Set();
  for (const family of registry.document_exclusions ?? []) {
    if (!family.pattern || !family.reason || !family.retention || !family.document?.path || !family.document?.anchor || !Array.isArray(family.paths)) {
      failures.push(`DOCUMENT_EXCLUSION_UNJUSTIFIED ${family.pattern ?? "<missing pattern>"}`);
      continue;
    }
    const error = validatePointer(`${family.document.path}#${family.document.anchor}`);
    if (error) failures.push(`DOCUMENT_EXCLUSION_DOCUMENT_INVALID ${family.pattern}: ${error}`);
    for (const relative of family.paths) {
      if (!pathExists(relative) && !candidateManifestOmissionAllowed(relative, exactDocumentExclusionPaths, candidateScope)) failures.push(`DOCUMENT_EXCLUSION_PATH_MISSING ${relative}`);
      if (activeDocumentSet.has(relative)) failures.push(`DOCUMENT_ACTIVE_AND_EXCLUDED ${relative}`);
      if (excludedDocumentPaths.has(relative)) failures.push(`DOCUMENT_EXCLUSION_DUPLICATE ${relative}`);
      if (!globMatches(family.pattern, relative)) failures.push(`DOCUMENT_EXCLUSION_PATTERN_MISMATCH ${family.pattern}: ${relative}`);
      excludedDocumentPaths.add(relative);
    }
  }
  const documentSummary = historicalDocumentFailures(
    registry, discoveredDocuments, activeDocumentSet, excludedDocumentPaths, candidateScope, exactDocumentExclusionPaths,
  );
  failures.push(...documentSummary.failures);
  const linkSummary = linkCheck(activeDocuments, failures);
  const attestationIndex = fs.readFileSync(path.join(root, ".context/requerimientos/README.md"), "utf8");
  if (!attestationIndex.includes("atestado_aceptacion_plan_ingesta_editorial_auditoria_2026-10-01.md")) {
    failures.push("CLIENT_ATTESTATION_LINK_MISSING .context/requerimientos/README.md");
  }
  const mainIndex = fs.readFileSync(path.join(root, ".context/indice.md"), "utf8");
  if (!mainIndex.includes("estado_del_proyecto.md")) failures.push("OPERATIONAL_AUTHORITY_LINK_MISSING .context/indice.md");

  if (requestedMode.includes("--self-test") && !runSelfTest(registry, discovered, assigned, candidateScope, candidateOnlyPaths)) failures.push("DOC_SELF_TEST_FAILED");
  const assignedCount = discovered.filter((relative) => assigned.has(relative)).length;
  const projectedSourceCount = discovered.filter((relative) => !candidateOnlyPaths.has(relative)).length;
  const candidateOnlySourceCount = candidateOnlySourceCountForScope(discovered, candidateOnlyPaths, candidateScope);
  const expectedCandidateOnlySourceCount = candidateScope
    ? [...candidateScope.selectedPaths].filter((relative) => candidateOnlyPaths.has(relative) && discovered.includes(relative)).length
    : registry.discovery.integration_projection?.candidate_only_path_count_at_cut;
  if (candidateOnlySourceCount !== expectedCandidateOnlySourceCount) {
    failures.push(`INTEGRATION_PROJECTION_CANDIDATE_ONLY_COUNT ${candidateOnlySourceCount} != ${expectedCandidateOnlySourceCount}`);
  }
  if (projectedSourceCount !== registry.discovery.integration_projection?.projected_relevant_source_paths_at_cut) {
    failures.push(`INTEGRATION_PROJECTION_SOURCE_COUNT ${projectedSourceCount} != ${registry.discovery.integration_projection?.projected_relevant_source_paths_at_cut}`);
  }
  const sourcePercent = discovered.length ? ((assignedCount / discovered.length) * 100).toFixed(1) : "100.0";
  const documentedComponents = registry.components.filter((component) => !validatePointer(`${component.document.path}#${component.document.anchor}`)).length;
  const componentPercent = registry.components.length ? ((documentedComponents / registry.components.length) * 100).toFixed(1) : "100.0";
  const localRelationTotal = relationTotal - remoteOnlyRelations - notApplicableRelations;
  const localVerifiedPercent = localRelationTotal ? ((verifiedRelations / localRelationTotal) * 100).toFixed(1) : "0.0";
  const localPendingPercent = localRelationTotal ? ((pendingRelations / localRelationTotal) * 100).toFixed(1) : "0.0";
  const localUnknownPercent = localRelationTotal ? ((unknownRelations / localRelationTotal) * 100).toFixed(1) : "0.0";
  const remoteRelationPercent = relationTotal ? ((remoteOnlyRelations / relationTotal) * 100).toFixed(1) : "0.0";
  const remoteCheckPercent = remoteChecks.length ? ((remoteChecksVerified / remoteChecks.length) * 100).toFixed(1) : "0.0";
  const verifiedSourcePercent = discovered.length ? ((structurallyVerifiedSources / discovered.length) * 100).toFixed(1) : "0.0";
  const relationCompleteSourcePercent = discovered.length ? ((fullyVerifiedSources / discovered.length) * 100).toFixed(1) : "0.0";
  process.stdout.write(`DOC_COVERAGE sources=${discovered.length} assigned=${assignedCount}/${discovered.length} (${sourcePercent}%) structurally_linked_sources=${structurallyVerifiedSources}/${discovered.length} (${verifiedSourcePercent}%) all_relation_dimensions_verified_sources=${fullyVerifiedSources}/${discovered.length} (${relationCompleteSourcePercent}%) components=${documentedComponents}/${registry.components.length} (${componentPercent}%) groups=${registry.groups.length} relation_slots=${relationTotal} local_relation_slots=${localRelationTotal} verified_local=${verifiedRelations} (${localVerifiedPercent}%) pending_local=${pendingRelations} (${localPendingPercent}%) unknown_local=${unknownRelations} (${localUnknownPercent}%) invalid_local=${invalidRelations} remote_only=${remoteOnlyRelations} (${remoteRelationPercent}% of all relation slots) not_applicable=${notApplicableRelations} remote_checks_verified=${remoteChecksVerified}/${remoteChecks.length} (${remoteCheckPercent}%) remote_checks_pending=${remoteChecks.length - remoteChecksVerified} integration_projection_sources=${projectedSourceCount} candidate_only_wip_sources=${candidateOnlySourceCount} note=group-level_dimensions_weighted_by_path_count; unknown_is_separate_and_gate_failing\n`);
  process.stdout.write(`DOC_GRAPH links=${linkSummary.checkedLinks} anchors=${linkSummary.checkedAnchors} active_reachable=${linkSummary.reachable}/${activeDocuments.length} active_docs=${activeDocuments.length} historical_cataloged=${documentSummary.catalogedCount}/${documentSummary.historicalCount} historical_linked_from_catalog=${documentSummary.linkedCount}/${documentSummary.historicalCount} historical_catalogs=${documentSummary.catalogCount} excluded_docs=${excludedDocumentPaths.size} artifacts=${registry.artifact_families.length} source_exclusion_families=${registry.exclusions.length}\n`);
  if (failures.length) {
    for (const issue of failures.slice(0, 200)) process.stderr.write(`DOC_GATE_FAIL ${issue}\n`);
    if (failures.length > 200) process.stderr.write(`DOC_GATE_FAIL ... ${failures.length - 200} more\n`);
    process.exitCode = 1;
    return 1;
  }
  process.stdout.write("DOC_GATE_PASS source inventory, unique Obsidian entry, active-document reachability, individually linked historical catalogs, justified document/source exclusions, retired-document backups/replacements, source/component assignments, local and remote relation states/resolutions, generated views, paths, anchors, comments, and manifests\n");
  return 0;
}

main();
