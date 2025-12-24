#!/bin/bash
# Bash script to run multi-agent testing and gap analysis

set -e

# Default values
SUITE="full"
VERBOSE=""
AGENTS=()
MAX_PARALLEL=""
OUTPUT=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --agents)
            shift
            while [[ $# -gt 0 ]] && [[ ! $1 =~ ^-- ]]; do
                AGENTS+=("$1")
                shift
            done
            ;;
        --max-parallel)
            MAX_PARALLEL="$2"
            shift 2
            ;;
        --suite)
            SUITE="$2"
            shift 2
            ;;
        --output)
            OUTPUT="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE="--verbose"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "Starting Multi-Agent Testing and Gap Analysis Framework..."

# Set database URL if not set
if [ -z "$DATABASE_URL" ]; then
    export DATABASE_URL="postgresql://jobautomation:password@localhost:5433/jobautomation"
    echo "Using default DATABASE_URL"
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SERVICE_DIR="$( cd "$SCRIPT_DIR/../.." && pwd )"
cd "$SERVICE_DIR"

# Build command arguments
ARGS=()

if [ ${#AGENTS[@]} -gt 0 ]; then
    for agent in "${AGENTS[@]}"; do
        ARGS+=("--agents" "$agent")
    done
fi

if [ -n "$MAX_PARALLEL" ]; then
    ARGS+=("--max-parallel" "$MAX_PARALLEL")
fi

if [ -n "$SUITE" ]; then
    ARGS+=("--suite" "$SUITE")
fi

if [ -n "$OUTPUT" ]; then
    ARGS+=("--output" "$OUTPUT")
fi

if [ -n "$VERBOSE" ]; then
    ARGS+=("$VERBOSE")
fi

# Run the Python script
echo ""
echo "Running agents..."
python -m tests.agents.run_agents "${ARGS[@]}"

if [ $? -ne 0 ]; then
    echo ""
    echo "Agent execution failed"
    exit 1
fi

echo ""
echo "Agent execution completed successfully!"
echo "Check reports in: tests/agents/reports/"


