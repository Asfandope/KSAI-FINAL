#!/bin/bash

# KS AI Development Helper Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
}

# Install dependencies
install_deps() {
    print_info "Installing dependencies..."
    
    # Install root dependencies
    pnpm install
    
    # Install API dependencies
    cd apps/api
    pip install -r requirements.txt
    cd ../..
    
    print_success "Dependencies installed successfully!"
}

# Start development environment
start_dev() {
    print_info "Starting development environment..."
    
    check_docker
    
    # Start Docker services
    docker-compose up -d postgres redis qdrant
    
    # Wait for services to be ready
    print_info "Waiting for services to be ready..."
    sleep 10
    
    # Start the API in the background
    print_info "Starting API server..."
    cd apps/api
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    API_PID=$!
    cd ../..
    
    # Start the frontend
    print_info "Starting frontend..."
    cd apps/web
    pnpm dev &
    WEB_PID=$!
    cd ../..
    
    print_success "Development environment started!"
    print_info "Frontend: http://localhost:3000"
    print_info "API: http://localhost:8000"
    print_info "API Docs: http://localhost:8000/docs"
    print_info "Qdrant UI: http://localhost:6333/dashboard"
    print_info ""
    print_info "Press Ctrl+C to stop all services"
    
    # Wait for user to stop
    wait
}

# Stop development environment
stop_dev() {
    print_info "Stopping development environment..."
    
    # Stop Docker services
    docker-compose down
    
    # Kill any running processes
    pkill -f "uvicorn app.main:app" || true
    pkill -f "next dev" || true
    
    print_success "Development environment stopped!"
}

# Reset database
reset_db() {
    print_warning "This will reset the database. All data will be lost!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Resetting database..."
        
        docker-compose down postgres
        docker volume rm ks-ai-platform_postgres_data 2>/dev/null || true
        docker-compose up -d postgres
        
        print_success "Database reset successfully!"
    else
        print_info "Database reset cancelled."
    fi
}

# Show logs
show_logs() {
    print_info "Showing Docker logs..."
    docker-compose logs -f
}

# Show help
show_help() {
    echo "KS AI Development Helper Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  install     Install all dependencies"
    echo "  start       Start development environment"
    echo "  stop        Stop development environment"
    echo "  reset-db    Reset database (WARNING: destroys data)"
    echo "  logs        Show Docker logs"
    echo "  help        Show this help message"
    echo ""
}

# Main script
case "${1:-help}" in
    install)
        install_deps
        ;;
    start)
        start_dev
        ;;
    stop)
        stop_dev
        ;;
    reset-db)
        reset_db
        ;;
    logs)
        show_logs
        ;;
    help|*)
        show_help
        ;;
esac