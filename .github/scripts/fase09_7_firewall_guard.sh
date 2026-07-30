#!/bin/sh
# Fail-closed firewall guard for the three F9.7-owned egress chains only.

set -u

ACTION=${1:-}
CHAIN=${2:-}
STATE_DIR=${3:-}
SUDO=${F97_FIREWALL_SUDO-sudo}

usage() {
    echo "usage: fase09_7_firewall_guard.sh setup|cleanup CHAIN STATE_DIR" >&2
    exit 2
}

case "$ACTION" in
    setup|cleanup) ;;
    *) usage ;;
esac

case "$CHAIN" in
    F97_FRONTEND_EGRESS|FASE097_EGRESS|FASE097_AUDIT_EGRESS) ;;
    *)
        echo "Unsupported F9.7 firewall chain" >&2
        exit 2
        ;;
esac

[ -n "$STATE_DIR" ] || usage
[ -d "$STATE_DIR" ] || {
    echo "Firewall state directory is missing" >&2
    exit 1
}

run_firewall() {
    if [ -n "$SUDO" ]; then
        "$SUDO" "$@"
    else
        "$@"
    fi
}

marker() {
    printf '%s/%s-%s\n' "$STATE_DIR" "$1" "$2"
}

check_available() {
    firewall=$1
    family=$2
    if ! run_firewall "$firewall" -w 10 -L OUTPUT >/dev/null; then
        echo "$family firewall is unavailable" >&2
        return 1
    fi
    return 0
}

chain_status() {
    firewall=$1
    run_firewall "$firewall" -w 10 -nL "$CHAIN" >/dev/null 2>&1
}

jump_status() {
    firewall=$1
    run_firewall "$firewall" -w 10 -C OUTPUT -j "$CHAIN" >/dev/null 2>&1
}

setup_family() {
    firewall=$1
    family=$2
    family_failed=0

    check_available "$firewall" "$family" || return 1

    if chain_status "$firewall"; then
        echo "$family chain already exists before setup" >&2
        return 1
    else
        rc=$?
        if [ "$rc" -ne 1 ]; then
            echo "$family chain absence check failed (rc=$rc)" >&2
            return 1
        fi
    fi

    if jump_status "$firewall"; then
        echo "$family jump already exists before setup" >&2
        return 1
    else
        rc=$?
        if [ "$rc" -ne 1 ]; then
            echo "$family jump absence check failed (rc=$rc)" >&2
            return 1
        fi
    fi

    if run_firewall "$firewall" -w 10 -N "$CHAIN"; then
        : > "$(marker "$family" chain)" || family_failed=1
    else
        echo "$family chain creation failed" >&2
        return 1
    fi

    run_firewall "$firewall" -w 10 -A "$CHAIN" -o lo -j RETURN || family_failed=1
    run_firewall "$firewall" -w 10 -A "$CHAIN" -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN || family_failed=1
    run_firewall "$firewall" -w 10 -A "$CHAIN" -j REJECT || family_failed=1

    if run_firewall "$firewall" -w 10 -I OUTPUT 1 -j "$CHAIN"; then
        : > "$(marker "$family" jump)" || family_failed=1
    else
        echo "$family jump insertion failed" >&2
        family_failed=1
    fi

    return "$family_failed"
}

cleanup_family() {
    firewall=$1
    family=$2
    family_failed=0
    chain_marker=$(marker "$family" chain)
    jump_marker=$(marker "$family" jump)

    if ! check_available "$firewall" "$family"; then
        return 1
    fi

    if [ -f "$jump_marker" ]; then
        while true; do
            if jump_status "$firewall"; then
                if ! run_firewall "$firewall" -w 10 -D OUTPUT -j "$CHAIN"; then
                    echo "$family owned jump removal failed" >&2
                    family_failed=1
                    break
                fi
            else
                rc=$?
                if [ "$rc" -eq 1 ]; then
                    break
                fi
                echo "$family owned jump check failed (rc=$rc)" >&2
                family_failed=1
                break
            fi
        done
    fi

    if [ -f "$chain_marker" ]; then
        if chain_status "$firewall"; then
            if ! run_firewall "$firewall" -w 10 -F "$CHAIN"; then
                echo "$family owned chain flush failed" >&2
                family_failed=1
            fi
            if ! run_firewall "$firewall" -w 10 -X "$CHAIN"; then
                echo "$family owned chain delete failed" >&2
                family_failed=1
            fi
        else
            rc=$?
            if [ "$rc" -ne 1 ]; then
                echo "$family owned chain check failed (rc=$rc)" >&2
                family_failed=1
            fi
        fi
    fi

    if [ -f "$jump_marker" ]; then
        if jump_status "$firewall"; then
            echo "$family owned jump remains after cleanup" >&2
            family_failed=1
        else
            rc=$?
            if [ "$rc" -ne 1 ]; then
                echo "$family final jump absence check failed (rc=$rc)" >&2
                family_failed=1
            fi
        fi
    fi

    if [ -f "$chain_marker" ]; then
        if chain_status "$firewall"; then
            echo "$family owned chain remains after cleanup" >&2
            family_failed=1
        else
            rc=$?
            if [ "$rc" -ne 1 ]; then
                echo "$family final chain absence check failed (rc=$rc)" >&2
                family_failed=1
            fi
        fi
    fi

    return "$family_failed"
}

guard_failed=0
if [ "$ACTION" = setup ]; then
    setup_family iptables ipv4 || guard_failed=1
    setup_family ip6tables ipv6 || guard_failed=1
else
    cleanup_family iptables ipv4 || guard_failed=1
    cleanup_family ip6tables ipv6 || guard_failed=1
fi

exit "$guard_failed"
