# Implementation Plan

- [x] 1. Set up project structure and core interfaces
  - Create monorepo structure with separate packages for client agents, backend API, and dashboard
  - Define TypeScript interfaces for shared types (PromptEvent, ClassificationResult, LogEntry)
  - Set up Python package structure for FastAPI backend
  - Configure build tools (TypeScript compiler, Python packaging)
  - _Requirements: 1.1, 2.1, 3.1_

- [x] 2. Implement GLiNER-based Classification Engine
  - [x] 2.1 Create Python classification service with GLiNER model
    - Install gliner library and download knowledgator/gliner-pii-edge-v1.0 model
    - Implement model initialization with local caching
    - Create classify() function that accepts text and returns detected entities with confidence scores
    - Map GLiNER entity types to internal PII categories (person, email, phone, credit_card, etc.)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.6_
  
  - [x] 2.2 Implement risk scoring algorithm
    - Create scoring logic based on entity count and confidence levels
    - Assign green/amber/red risk levels according to thresholds
    - Handle edge cases (empty prompts, very long prompts)
    - _Requirements: 2.5_
  
  - [x] 2.3 Add regex-based fallback patterns
    - Implement regex patterns for emails, phone numbers, credit cards, SSNs
    - Create fallback classification when GLiNER model is unavailable
    - Merge GLiNER and regex results, deduplicating overlapping detections
    - _Requirements: 2.1, 2.2, 2.3_
  
  - [x] 2.4 Write unit tests for classification engine
    - Test with known PII samples (names, emails, credit cards)
    - Test edge cases (empty strings, very long text, special characters)
    - Verify risk scoring logic with various entity combinations
    - _Requirements: 2.1, 2.5, 2.6_

- [x] 3. Implement Sanitization Engine
  - [x] 3.1 Create sanitization logic using GLiNER detection results
    - Replace detected entities with typed placeholders (e.g., [PERSON], [EMAIL])
    - Implement masking strategy for partial redaction
    - Implement complete redaction strategy
    - Preserve prompt structure and whitespace
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [x] 3.2 Generate diff between original and sanitized prompts
    - Create diff visualization showing replacements
    - Highlight changed spans with entity type labels
    - _Requirements: 4.4_
  
  - [x] 3.3 Write unit tests for sanitization engine
    - Test placeholder replacement accuracy
    - Test masking and redaction strategies
    - Verify diff generation correctness
    - _Requirements: 4.1, 4.2, 4.3_

- [ ] 4. Build FastAPI backend service
  - [ ] 4.1 Set up FastAPI application structure
    - Create FastAPI app with CORS middleware
    - Configure Pydantic models for request/response validation
    - Set up async database connection pool (asyncpg for PostgreSQL)
    - Implement JWT authentication middleware
    - _Requirements: 3.1, 3.2_
  
  - [ ] 4.2 Implement log ingestion endpoint
    - Create POST /api/v1/logs/batch endpoint for batched log uploads
    - Validate incoming log entries against schema
    - Insert logs into PostgreSQL database
    - Implement rate limiting per device (1000 logs/hour)
    - _Requirements: 3.1, 3.4_
  
  - [ ] 4.3 Implement log query endpoints
    - Create GET /api/v1/logs endpoint with filtering (date range, risk level, tool name, user)
    - Implement pagination (page, limit parameters)
    - Create GET /api/v1/stats/summary endpoint for dashboard statistics
    - Optimize queries with database indexes
    - _Requirements: 3.2, 3.5_
  
  - [ ] 4.4 Implement configuration endpoints
    - Create GET /api/v1/config endpoint to fetch firewall configuration
    - Create PUT /api/v1/config endpoint to update configuration
    - Validate configuration changes (retention days 30-365, valid regex patterns)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [ ] 4.5 Implement log export functionality
    - Create GET /api/v1/logs/export endpoint with format parameter (csv, json)
    - Generate CSV files with proper headers and escaping
    - Generate JSON files with complete log data
    - Stream large exports to avoid memory issues
    - _Requirements: 3.3_
  
  - [ ] 4.6 Write integration tests for API endpoints
    - Test log ingestion with valid and invalid data
    - Test query endpoints with various filters
    - Test configuration CRUD operations
    - Test export functionality with different formats
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 5. Create database schema and migrations
  - [ ] 5.1 Design PostgreSQL database schema
    - Create logs table with indexes on timestamp, userId, toolName, riskLevel
    - Create config table for firewall configuration
    - Create devices table for device registration
    - Create users table for authentication
    - _Requirements: 3.1, 3.4_
  
  - [ ] 5.2 Implement database migrations
    - Set up Alembic for database migrations
    - Create initial migration with all tables
    - Add indexes for query performance
    - _Requirements: 3.4_
  
  - [ ] 5.3 Implement log retention policy
    - Create scheduled job to delete logs older than configured retention period
    - Add database trigger or cron job for automatic cleanup
    - _Requirements: 3.4, 6.4_

- [ ] 6. Build browser extension for web AI tool detection
  - [ ] 6.1 Create Manifest V3 extension structure
    - Set up manifest.json with required permissions (activeTab, storage)
    - Create background service worker for detection logic
    - Create content scripts for AI tool page injection
    - _Requirements: 1.1, 1.2_
  
  - [ ] 6.2 Implement AI tool detection for major platforms
    - Add content script for ChatGPT (chat.openai.com) to intercept form submissions
    - Add content script for Claude (claude.ai) to intercept API calls
    - Add content script for Gemini (gemini.google.com) to monitor input fields
    - Add content script for Copilot (copilot.microsoft.com) to capture prompts
    - _Requirements: 1.2_
  
  - [ ] 6.3 Integrate classification engine in extension
    - Load GLiNER model via ONNX Runtime Web (if available) or call local Python service
    - Classify prompts before submission to AI tools
    - Display risk level to user in real-time
    - _Requirements: 2.1, 2.5, 2.6, 5.1, 5.2_
  
  - [ ] 6.4 Implement prompt interception and sanitization UI
    - Show modal when sensitive data is detected
    - Display original vs sanitized prompt with diff highlighting
    - Provide "Use Sanitized" and "Cancel" buttons
    - Log user decision (used sanitized or cancelled)
    - _Requirements: 4.4, 4.5_
  
  - [ ] 6.5 Implement local log buffering and sync
    - Store logs in browser local storage
    - Batch upload logs to backend API every 5 minutes or 50 logs
    - Retry failed uploads with exponential backoff
    - Handle offline mode gracefully
    - _Requirements: 3.1, 5.1, 5.2_
  
  - [ ] 6.6 Write extension tests
    - Test content script injection on AI tool pages
    - Test prompt detection and interception
    - Test classification integration
    - Test log buffering and sync logic
    - _Requirements: 1.1, 1.2, 2.1, 3.1_

- [ ] 7. Build desktop agent for desktop AI tool monitoring
  - [ ] 7.1 Create cross-platform desktop agent structure
    - Set up Electron or Python-based desktop app
    - Implement system tray icon and background service
    - Create OS-specific monitoring modules (Windows, macOS, Linux)
    - _Requirements: 1.1, 1.3_
  
  - [ ] 7.2 Implement clipboard monitoring
    - Monitor clipboard for copy events
    - Detect when clipboard content is pasted into AI desktop apps
    - Classify clipboard content before paste completes
    - _Requirements: 1.1, 5.1, 5.2_
  
  - [ ] 7.3 Implement window title and process monitoring
    - Detect when AI desktop applications are active (ChatGPT app, etc.)
    - Monitor window titles for AI tool identification
    - Track application focus changes
    - _Requirements: 1.1, 1.2_
  
  - [ ] 7.4 Integrate GLiNER classification service
    - Run local Python service with GLiNER model
    - Classify detected prompts in real-time
    - Cache model in memory for fast inference
    - _Requirements: 2.1, 2.5, 2.6, 5.1, 5.2, 5.3_
  
  - [ ] 7.5 Implement desktop notification UI
    - Show native OS notification when sensitive data is detected
    - Provide quick actions (view sanitized, cancel, proceed anyway)
    - Log user decisions
    - _Requirements: 4.4, 4.5_
  
  - [ ] 7.6 Implement log sync to backend
    - Buffer logs locally in SQLite database
    - Sync logs to backend API periodically
    - Handle network failures with retry logic
    - _Requirements: 3.1, 5.1, 5.2_
  
  - [ ] 7.7 Write desktop agent tests
    - Test clipboard monitoring on each OS
    - Test window/process detection
    - Test classification integration
    - Test log sync functionality
    - _Requirements: 1.1, 1.3, 2.1, 3.1_

- [ ] 8. Build CLI interceptor for command-line AI tools
  - [ ] 8.1 Create shell script installer
    - Generate shell functions/aliases for common AI CLIs (gh copilot, aichat, etc.)
    - Modify .bashrc, .zshrc, .config/fish/config.fish to load interceptor
    - Support bash, zsh, and fish shells
    - _Requirements: 1.1, 1.3_
  
  - [ ] 8.2 Implement CLI command interception
    - Wrap AI CLI commands to capture stdin and arguments
    - Extract prompt text from command invocation
    - Pass prompt to classification service
    - _Requirements: 1.1, 1.2_
  
  - [ ] 8.3 Integrate classification and sanitization
    - Call local GLiNER service for prompt classification
    - Display risk level in terminal with colored output
    - Show sanitized prompt if sensitive data detected
    - Prompt user to confirm or cancel
    - _Requirements: 2.1, 2.5, 4.1, 4.4, 4.5_
  
  - [ ] 8.4 Implement CLI log collection
    - Write logs to local file (~/.ai-firewall/logs.jsonl)
    - Create background sync process to upload logs to backend
    - Handle offline mode with local-only logging
    - _Requirements: 3.1, 5.1, 5.2_
  
  - [ ] 8.5 Write CLI interceptor tests
    - Test shell function generation for each shell
    - Test command interception and prompt extraction
    - Test classification integration
    - Test log collection and sync
    - _Requirements: 1.1, 1.3, 2.1, 3.1_

- [ ] 9. Build dashboard web application
  - [ ] 9.1 Set up React application with TypeScript
    - Create React app with Vite for fast builds
    - Set up React Router for navigation
    - Configure Tailwind CSS and shadcn/ui components
    - Set up React Query for API state management
    - _Requirements: 3.2, 3.5_
  
  - [ ] 9.2 Implement authentication flow
    - Create login page with JWT authentication
    - Store JWT token in secure httpOnly cookie or localStorage
    - Implement token refresh logic
    - Add protected route wrapper for authenticated pages
    - _Requirements: 3.2_
  
  - [ ] 9.3 Create overview dashboard page
    - Display summary statistics (total logs, risk distribution, top tools)
    - Show charts for usage trends over time (Recharts)
    - Display recent high-risk interactions
    - Add date range selector for filtering
    - _Requirements: 3.5_
  
  - [ ] 9.4 Create detailed logs table page
    - Display paginated table of all log entries
    - Implement filtering by date range, risk level, tool name, user
    - Add search functionality for user IDs
    - Show expandable rows with full log details
    - Implement sorting by timestamp, risk level, tool name
    - _Requirements: 3.2, 3.5_
  
  - [ ] 9.5 Create user activity view
    - Display per-user statistics and activity timeline
    - Show user's risk profile (percentage of red/amber/green interactions)
    - List user's most-used AI tools
    - _Requirements: 3.2, 3.5_
  
  - [ ] 9.6 Create tool usage breakdown page
    - Display statistics grouped by AI tool
    - Show usage trends for each tool over time
    - Highlight tools with highest risk interactions
    - _Requirements: 1.4, 3.5_
  
  - [ ] 9.7 Implement export functionality
    - Add export button to logs table
    - Allow selection of export format (CSV, JSON)
    - Apply current filters to export
    - Download generated file
    - _Requirements: 3.3_
  
  - [ ] 9.8 Create configuration management page
    - Display current firewall configuration
    - Allow editing of monitored tools (enable/disable)
    - Allow editing of sensitivity thresholds
    - Allow editing of custom patterns for organization-specific data
    - Allow editing of log retention period
    - Validate configuration changes before saving
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [ ] 9.9 Write dashboard component tests
    - Test authentication flow
    - Test dashboard data loading and display
    - Test filtering and search functionality
    - Test export functionality
    - Test configuration management
    - _Requirements: 3.2, 3.3, 3.5, 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 10. Implement error handling and resilience
  - [ ] 10.1 Add client-side error handling
    - Handle classification engine failures with regex fallback
    - Handle network failures with local buffering
    - Display user-friendly error messages
    - Log errors for debugging
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [ ] 10.2 Add server-side error handling
    - Implement global exception handler in FastAPI
    - Return appropriate HTTP status codes and error messages
    - Log all errors with stack traces
    - Implement database connection retry logic
    - _Requirements: 3.1, 3.2_
  
  - [ ] 10.3 Implement rate limiting and quotas
    - Add rate limiting middleware to FastAPI (slowapi)
    - Implement per-device quotas (1000 logs/hour)
    - Return 429 Too Many Requests with retry-after header
    - _Requirements: 3.1_

- [ ] 11. Create deployment configurations
  - [ ] 11.1 Create Docker configurations
    - Write Dockerfile for FastAPI backend
    - Write Dockerfile for dashboard (nginx serving static files)
    - Create docker-compose.yml for local development
    - _Requirements: 3.1, 3.2_
  
  - [ ] 11.2 Create Kubernetes manifests
    - Create deployment manifests for backend and dashboard
    - Create service manifests for load balancing
    - Create ConfigMap for environment configuration
    - Create Secret for sensitive credentials
    - _Requirements: 3.1, 3.2_
  
  - [ ] 11.3 Set up CI/CD pipeline
    - Create GitHub Actions workflow for automated testing
    - Create build pipeline for browser extension
    - Create build pipeline for desktop agent
    - Create deployment pipeline for backend and dashboard
    - _Requirements: 3.1, 3.2_

- [ ] 12. Create installation and setup documentation
  - [ ] 12.1 Write browser extension installation guide
    - Document how to install from Chrome Web Store / Firefox Add-ons
    - Document manual installation for development
    - Document configuration steps
    - _Requirements: 1.1, 1.2_
  
  - [ ] 12.2 Write desktop agent installation guide
    - Document installation on Windows, macOS, Linux
    - Document required permissions and setup
    - Document troubleshooting common issues
    - _Requirements: 1.1, 1.3_
  
  - [ ] 12.3 Write CLI interceptor installation guide
    - Document shell script installation for bash, zsh, fish
    - Document how to verify installation
    - Document uninstallation steps
    - _Requirements: 1.1, 1.3_
  
  - [ ] 12.4 Write backend deployment guide
    - Document Docker deployment steps
    - Document Kubernetes deployment steps
    - Document environment variable configuration
    - Document database setup and migrations
    - _Requirements: 3.1, 3.4_
  
  - [ ] 12.5 Write dashboard user guide
    - Document how to access and navigate dashboard
    - Document filtering and search features
    - Document export functionality
    - Document configuration management
    - _Requirements: 3.2, 3.3, 3.5, 6.1, 6.2, 6.3, 6.4, 6.5_
