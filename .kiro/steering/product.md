# Product Overview

AI Usage Firewall is a lightweight monitoring and governance system that provides organizations with visibility and control over employee usage of AI tools.

## Core Functionality

- **Multi-platform monitoring**: Detects AI tool usage across web browsers, desktop applications, and CLI tools
- **Privacy-first architecture**: All sensitive data analysis and classification happens on-device
- **Risk classification**: Automatically classifies prompts as green/amber/red based on detected sensitive entities
- **Centralized dashboard**: Web-based analytics and configuration management
- **Entity detection**: Identifies PII, financial data, contracts, IP, and custom patterns in prompts

## System Components

1. **Client-side agents**: Browser extension, desktop agent, and CLI interceptor that detect AI tool usage and classify prompts locally
2. **Backend API**: FastAPI service for log ingestion and data retrieval
3. **Dashboard**: React-based web interface for viewing usage analytics and managing configuration

## Key Principles

- Privacy by design: Sensitive data never leaves the device
- Lightweight: Minimal performance impact on user workflows
- Extensible: Support for custom sensitivity patterns and monitored tools
