#!/bin/bash

# Database Migration Helper Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Navigate to API directory
cd "$(dirname "$0")/../apps/api"

case "${1:-help}" in
    upgrade)
        print_info "Running database migrations..."
        alembic upgrade head
        print_success "Database migrations completed!"
        ;;
    downgrade)
        print_warning "Downgrading database..."
        alembic downgrade -1
        print_success "Database downgraded!"
        ;;
    current)
        print_info "Current database revision:"
        alembic current
        ;;
    history)
        print_info "Migration history:"
        alembic history --verbose
        ;;
    generate)
        if [ -z "$2" ]; then
            print_error "Please provide a migration message"
            echo "Usage: $0 generate 'migration message'"
            exit 1
        fi
        print_info "Generating new migration: $2"
        alembic revision --autogenerate -m "$2"
        print_success "Migration generated!"
        ;;
    reset)
        print_warning "This will reset the database to initial state!"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Resetting database..."
            alembic downgrade base
            alembic upgrade head
            print_success "Database reset completed!"
        else
            print_info "Reset cancelled."
        fi
        ;;
    help|*)
        echo "Database Migration Helper"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  upgrade         Run all pending migrations"
        echo "  downgrade       Downgrade by one migration"
        echo "  current         Show current database revision"
        echo "  history         Show migration history"
        echo "  generate 'msg'  Generate new migration"
        echo "  reset           Reset database to initial state"
        echo "  help            Show this help message"
        echo ""
        ;;
esac