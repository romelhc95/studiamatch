#!/usr/bin/env bash
set -euo pipefail

STAGED_DIR="/opt/node-staging/web"
APP_WEB_DIR="/app/web"
NODE_MODULES_DIR="${APP_WEB_DIR}/node_modules"
STAGED_MANIFESTS="${STAGED_DIR}/manifests.sha256"
VOLUME_MARKER="${NODE_MODULES_DIR}/.studiamatch-node-deps.sha256"
EXPECTED_UID="${STUDIAMATCH_UID:-1000}"
EXPECTED_GID="${STUDIAMATCH_GID:-1000}"

log() { echo "[init-container] $*"; }
die() { echo "[init-container] ERROR: $*" >&2; exit 1; }

current_manifest_hashes() {
  (cd "${APP_WEB_DIR}" && sha256sum package.json package-lock.json)
}

expected_volume_marker() {
  printf 'STUDIAMATCH_UID=%s\nSTUDIAMATCH_GID=%s\n' "${EXPECTED_UID}" "${EXPECTED_GID}"
  cat "${STAGED_MANIFESTS}"
}

verify_manifests_match_image() {
  [ -f "${STAGED_MANIFESTS}" ] || die "staged manifest hashes missing from image"
  local staged current
  staged="$(cat "${STAGED_MANIFESTS}")"
  current="$(current_manifest_hashes)"
  if [ "${staged}" != "${current}" ]; then
    log "Node dependency manifests differ from image."
    log "Run docker compose build before starting."
    die "source web/package.json or web/package-lock.json hash != staged image hash"
  fi
  log "Node dependency manifests match image staging."
}

provision_node_volume() {
  verify_manifests_match_image
  local staged_marker
  staged_marker="$(expected_volume_marker)"
  if [ -f "${VOLUME_MARKER}" ] && [ "$(cat "${VOLUME_MARKER}")" = "${staged_marker}" ]; then
    log "node_modules volume up to date (manifest hash match): reusing existing volume, no npm ci."
    return 0
  fi
  log "Provisioning named node_modules volume from image staging (npm ci runs only during image build)."
  mkdir -p "${NODE_MODULES_DIR}"
  find "${NODE_MODULES_DIR}" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
  cp -a "${STAGED_DIR}/node_modules/." "${NODE_MODULES_DIR}/"
  printf '%s\n' "${staged_marker}" > "${VOLUME_MARKER}"
  chown -R "${EXPECTED_UID}:${EXPECTED_GID}" "${NODE_MODULES_DIR}"
  log "node_modules volume provisioned and owned by ${EXPECTED_UID}:${EXPECTED_GID}."
}

verify_node_volume() {
  verify_manifests_match_image
  local staged_marker
  staged_marker="$(expected_volume_marker)"
  if [ ! -f "${VOLUME_MARKER}" ] || [ "$(cat "${VOLUME_MARKER}")" != "${staged_marker}" ]; then
    die "node_modules volume out of sync with image staging; run: docker compose up -d (node-deps re-provisions it)"
  fi
  if [ ! -e "${NODE_MODULES_DIR}/.bin/next" ]; then
    die "next binary not found in node_modules volume"
  fi
  log "node_modules volume verified: reusable, no npm ci."
}

main() {
  case "${1-}" in
    --prepare-node)
      if [ "$(id -u)" -eq 0 ]; then provision_node_volume; else verify_node_volume; fi
      ;;
    "")
      if [ "$(id -u)" -eq 0 ]; then
        log "No command given: preparing/verifying Node volume, then exiting."
        provision_node_volume
      else
        verify_node_volume
      fi
      ;;
    *)
      if [ "$(id -u)" -eq 0 ]; then provision_node_volume; else verify_node_volume; fi
      log "Executing command: $*"
      exec "$@"
      ;;
  esac
}

main "$@"
