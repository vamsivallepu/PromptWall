# Requirements Document

## Introduction

The AI Usage Firewall is a lightweight monitoring and governance system that provides organizations with visibility and control over employee usage of AI tools. The system detects AI tool usage across browser, desktop, and CLI environments, classifies prompts by sensitivity level, logs all activity in a centralized dashboard, and provides sanitized prompts with sensitive data removed.

## Glossary

- **AI Usage Firewall**: The complete system that monitors, classifies, and logs AI tool usage
- **Detection Engine**: The component that identifies when employees interact with AI tools
- **Classification Engine**: The on-device model that analyzes prompts for sensitive content
- **Sanitization Engine**: The component that removes sensitive data from prompts and provides secure alternatives
- **Dashboard**: The centralized web interface displaying usage logs and risk assessments
- **Prompt**: Text input submitted by an employee to an AI tool
- **Sensitive Data**: Information including PII (Personally Identifiable Information), contracts, financial data, or intellectual property
- **Risk Tag**: A classification label (red/amber/green) indicating the sensitivity level of a prompt
- **AI Tool**: Any web-based, desktop, or CLI application that provides AI capabilities (e.g., ChatGPT, Claude, Copilot)

## Requirements

### Requirement 1

**User Story:** As a compliance officer, I want to see which AI tools employees are using, so that I can understand our organization's AI tool landscape and potential risk exposure.

#### Acceptance Criteria

1. WHEN an employee interacts with a supported AI tool through browser, desktop, or CLI, THE Detection Engine SHALL capture the tool name and timestamp
2. THE Detection Engine SHALL support detection of major AI tools including ChatGPT, Claude, Gemini, Copilot, and Perplexity
3. THE Detection Engine SHALL operate across browser extensions, desktop applications, and command-line interfaces
4. THE Dashboard SHALL display a list of all detected AI tools with usage frequency and last access time
5. THE Dashboard SHALL provide filtering capabilities by tool name, user, and time range

### Requirement 2

**User Story:** As a compliance officer, I want prompts automatically classified by sensitivity level, so that I can quickly identify high-risk AI usage without manually reviewing every interaction.

#### Acceptance Criteria

1. WHEN a prompt is captured, THE Classification Engine SHALL analyze the content for sensitive data types
2. THE Classification Engine SHALL identify PII including names, email addresses, phone numbers, addresses, and identification numbers
3. THE Classification Engine SHALL identify financial data including account numbers, credit card numbers, and transaction details
4. THE Classification Engine SHALL identify contractual information and intellectual property markers
5. THE Classification Engine SHALL assign a risk tag of red (high sensitivity), amber (medium sensitivity), or green (low sensitivity) to each prompt
6. THE Classification Engine SHALL perform all analysis on-device without transmitting prompt content to external services

### Requirement 3

**User Story:** As a compliance officer, I want all AI tool usage logged in a central dashboard, so that I can audit employee interactions and demonstrate compliance to regulators.

#### Acceptance Criteria

1. THE AI Usage Firewall SHALL log every detected AI tool interaction with timestamp, user identifier, tool name, and risk tag
2. THE Dashboard SHALL display logs in a searchable and sortable table format
3. THE Dashboard SHALL provide export functionality for audit reports in CSV and JSON formats
4. THE Dashboard SHALL retain logs for a configurable retention period with a minimum of 90 days
5. THE Dashboard SHALL display summary statistics including total interactions, risk distribution, and top users

### Requirement 4

**User Story:** As an employee, I want to receive a sanitized version of my prompt with sensitive data removed, so that I can safely use AI tools without exposing confidential information.

#### Acceptance Criteria

1. WHEN the Classification Engine detects sensitive data in a prompt, THE Sanitization Engine SHALL generate a sanitized version with sensitive data replaced by placeholders
2. THE Sanitization Engine SHALL replace PII with generic placeholders (e.g., "[NAME]", "[EMAIL]", "[PHONE]")
3. THE Sanitization Engine SHALL replace financial data with type-appropriate placeholders (e.g., "[ACCOUNT_NUMBER]", "[AMOUNT]")
4. THE AI Usage Firewall SHALL present the sanitized prompt to the employee before submission to the AI tool
5. THE AI Usage Firewall SHALL allow the employee to review and approve the sanitized prompt or cancel the submission

### Requirement 5

**User Story:** As a system administrator, I want the firewall to operate with minimal performance impact, so that employee productivity is not negatively affected.

#### Acceptance Criteria

1. THE Detection Engine SHALL add no more than 100 milliseconds of latency to AI tool interactions
2. THE Classification Engine SHALL complete prompt analysis within 500 milliseconds for prompts up to 10,000 characters
3. THE AI Usage Firewall SHALL consume no more than 200 MB of system memory during normal operation
4. THE AI Usage Firewall SHALL operate without requiring constant internet connectivity for core detection and classification functions
5. THE Dashboard SHALL load the main view within 2 seconds under normal network conditions

### Requirement 6

**User Story:** As a system administrator, I want to configure which AI tools are monitored and sensitivity thresholds, so that I can customize the firewall to my organization's specific needs and risk tolerance.

#### Acceptance Criteria

1. THE AI Usage Firewall SHALL provide a configuration interface for enabling or disabling monitoring of specific AI tools
2. THE AI Usage Firewall SHALL allow administrators to adjust sensitivity thresholds for red, amber, and green classifications
3. THE AI Usage Firewall SHALL support custom patterns for identifying organization-specific sensitive data
4. THE AI Usage Firewall SHALL allow configuration of log retention periods between 30 and 365 days
5. THE AI Usage Firewall SHALL validate all configuration changes and provide clear error messages for invalid settings
