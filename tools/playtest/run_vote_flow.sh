#!/usr/bin/env bash
set -e

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
PROJECT_ROOT=$(cd "$SCRIPT_DIR/../../" && pwd)

VERBOSE=false
STEP=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --step)
            STEP="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

log() {
    if [ "$VERBOSE" = true ]; then
        echo "[$(date -Iseconds)] $1"
    fi
}

error() {
    echo "ERROR: $1" >&2
    exit 1
}

log "Starting Vote Flow E2E Test..."

cd "$PROJECT_ROOT"

if [ -z "$STEP" ] || [ "$STEP" = "create_cycle" ]; then
    log "Step 1: Creating vote cycle..."
    python "$SCRIPT_DIR/test_vote_flow.py" create_cycle || error "Failed to create vote cycle"
fi

if [ -z "$STEP" ] || [ "$STEP" = "add_candidates" ]; then
    log "Step 2: Adding candidates..."
    python "$SCRIPT_DIR/test_vote_flow.py" add_candidates || error "Failed to add candidates"
fi

if [ -z "$STEP" ] || [ "$STEP" = "open_cycle" ]; then
    log "Step 3: Opening vote cycle..."
    python "$SCRIPT_DIR/test_vote_flow.py" open_cycle || error "Failed to open vote cycle"
fi

if [ -z "$STEP" ] || [ "$STEP" = "submit_vote" ]; then
    log "Step 4: Submitting votes..."
    python "$SCRIPT_DIR/test_vote_flow.py" submit_vote || error "Failed to submit votes"
fi

if [ -z "$STEP" ] || [ "$STEP" = "close_and_count" ]; then
    log "Step 5: Closing and counting votes..."
    python "$SCRIPT_DIR/test_vote_flow.py" close_and_count || error "Failed to close and count votes"
fi

if [ -z "$STEP" ] || [ "$STEP" = "verify_result" ]; then
    log "Step 6: Verifying result..."
    python "$SCRIPT_DIR/test_vote_flow.py" verify_result || error "Failed to verify result"
fi

log "Vote Flow E2E Test completed successfully!"
echo "SUCCESS: All steps passed"