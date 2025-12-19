#!/bin/bash
# Version management script
# Usage: ./version-manager.sh [tag|release|changelog]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

ACTION="${1:-help}"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Create version tag
create_tag() {
    local version=$1
    local message=${2:-"Release $version"}
    
    if [ -z "$version" ]; then
        error "Version required"
    fi
    
    log "Creating tag: $version"
    git tag -a "v$version" -m "$message"
    git push origin "v$version"
    
    log "Tag created: v$version"
}

# Create release
create_release() {
    local version=$1
    local changelog=$2
    
    log "Creating release for version: $version"
    
    # Generate changelog if not provided
    if [ -z "$changelog" ]; then
        changelog=$(git log --pretty=format:"- %s" $(git describe --tags --abbrev=0 HEAD^ 2>/dev/null || echo "")..HEAD)
    fi
    
    # Create GitHub release (requires gh CLI)
    if command -v gh &> /dev/null; then
        gh release create "v$version" \
            --title "Release $version" \
            --notes "$changelog"
    else
        log "GitHub CLI not available, tag created: v$version"
    fi
}

# Generate changelog
generate_changelog() {
    local from_tag=${1:-$(git describe --tags --abbrev=0 HEAD^ 2>/dev/null || echo "")}
    local to_tag=${2:-HEAD}
    
    log "Generating changelog from $from_tag to $to_tag"
    
    echo "# Changelog"
    echo ""
    echo "## Version $(git describe --tags --abbrev=0 2>/dev/null || echo 'unreleased')"
    echo ""
    git log --pretty=format:"- %s (%h)" "$from_tag".."$to_tag"
}

# Track deployment
track_deployment() {
    local version=$1
    local environment=$2
    
    log "Tracking deployment: $version to $environment"
    
    echo "$(date -Iseconds),$version,$environment" >> "$PROJECT_ROOT/logs/deployments.csv"
}

# Main
main() {
    case $ACTION in
        tag)
            create_tag "$2" "$3"
            ;;
        release)
            create_release "$2" "$3"
            ;;
        changelog)
            generate_changelog "$2" "$3"
            ;;
        track)
            track_deployment "$2" "$3"
            ;;
        *)
            echo "Usage: $0 [tag|release|changelog|track] [options]"
            exit 1
            ;;
    esac
}

main "$@"
