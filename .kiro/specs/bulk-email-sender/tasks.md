# Implementation Plan: Bulk Email Sender

## Overview

This implementation plan breaks down the Bulk Email Sender platform into discrete coding tasks. The system consists of a Django REST API backend with Celery for asynchronous processing, PostgreSQL for data storage, Redis for caching and job queuing, Claude AI integration for email optimization, and a React frontend with Tailwind CSS.

The implementation follows a phased approach: core infrastructure → backend services → AI integration → frontend → testing and deployment. Each task builds incrementally, with checkpoints to ensure stability before proceeding.

## Tasks

- [x] 1. Set up core infrastructure and project structure
  - [x] 1.1 Initialize Django project with PostgreSQL and Redis configuration
    - Create Django project with settings for development and production
    - Configure PostgreSQL database connection with connection pooling
    - Set up Redis for caching and Celery broker
    - Configure environment variables for sensitive settings
    - Set up CORS middleware for frontend integration
    - _Requirements: 1.7_

  - [x] 1.2 Configure Celery with Redis broker and result backend
    - Install and configure Celery with Redis
    - Create Celery app configuration with task routing
    - Set up Celery beat for scheduled tasks
    - Configure task retry policies and rate limits
    - _Requirements: 9.1, 9.5_

  - [x] 1.3 Create base database models and initial migrations
    - Define User model with email verification fields
    - Create SMTPConfig, RecipientList, Recipient, Template, Campaign, EmailLog, EmailEvent models
    - Add database indexes for performance (user_id, email, tracking_id, created_at)
    - Generate and apply initial migrations
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 8.1, 9.6_

  - [x] 1.4 Write property test for database model constraints
    - **Property: Database integrity constraints**
    - **Validates: Requirements 1.1, 2.1, 3.1**
    - Test that foreign key relationships are enforced
    - Test that unique constraints prevent duplicates

- [x] 2. Implement user authentication and authorization
  - [x] 2.1 Create user registration endpoint with email verification
    - Implement POST /api/auth/register endpoint
    - Add password complexity validation (min 8 chars, mixed case, numbers)
    - Generate email verification token
    - Send verification email via Django email backend
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ] 2.2 Write property test for password complexity enforcement
    - **Property 1: Password Complexity Enforcement**
    - **Validates: Requirements 1.2**
    - Test that only passwords meeting complexity requirements are accepted

  - [ ] 2.3 Write property test for email verification
    - **Property 2: Email Verification Sent on Registration**
    - **Validates: Requirements 1.3**
    - Test that verification email is sent for every valid registration

  - [x] 2.4 Implement JWT authentication with token refresh
    - Create POST /api/auth/login endpoint
    - Generate JWT access tokens with 1-hour expiration
    - Generate refresh tokens with longer expiration
    - Implement POST /api/auth/refresh endpoint
    - Add JWT authentication middleware
    - _Requirements: 1.4, 1.5_

  - [ ] 2.5 Write property tests for JWT token behavior
    - **Property 3: JWT Token Expiration**
    - **Validates: Requirements 1.4**
    - Test that tokens expire exactly 1 hour after issuance
    - **Property 4: Expired Token Rejection**
    - **Validates: Requirements 1.5**
    - Test that expired tokens are rejected

  - [x] 2.6 Add rate limiting to authentication endpoints
    - Install and configure django-ratelimit or DRF throttling
    - Set rate limit to 5 attempts per minute per IP
    - Return 429 status with retry-after header
    - _Requirements: 1.6_

  - [ ] 2.7 Write property test for authentication rate limiting
    - **Property 5: Authentication Rate Limiting**
    - **Validates: Requirements 1.6**
    - Test that >5 attempts in 1 minute are rejected

  - [x] 2.8 Implement email verification endpoint
    - Create POST /api/auth/verify-email endpoint
    - Validate verification token
    - Mark user as verified in database
    - Return success response
    - _Requirements: 1.3_

- [x] 3. Checkpoint - Authentication complete

- [x] 4. Build SMTP configuration management
  - [x] 4.1 Create SMTP configuration CRUD endpoints
    - Implement POST /api/smtp-configs endpoint
    - Implement GET /api/smtp-configs endpoint (list user's configs)
    - Implement GET /api/smtp-configs/{id} endpoint
    - Implement PUT /api/smtp-configs/{id} endpoint
    - Implement DELETE /api/smtp-configs/{id} endpoint
    - Support Gmail, SendGrid, Mailgun, and custom SMTP providers
    - _Requirements: 2.1, 2.5, 2.6_

  - [x] 4.2 Implement SMTP credential encryption
    - Install cryptography library (Fernet)
    - Create encryption utility functions
    - Encrypt passwords before saving to database
    - Decrypt passwords when loading from database
    - Store encryption key in environment variable
    - _Requirements: 2.2_

  - [ ] 4.3 Write property test for SMTP credential encryption
    - **Property 6: SMTP Credential Encryption**
    - **Validates: Requirements 2.2**
    - Test that passwords are never stored as plaintext

  - [x] 4.4 Add SMTP validation with test email sending
    - Create POST /api/smtp-configs/{id}/test endpoint
    - Connect to SMTP server with provided credentials
    - Send test email to user's email address
    - Return descriptive error messages on failure
    - Mark configuration as validated on success
    - _Requirements: 2.3, 2.4_

  - [ ] 4.5 Write property test for SMTP validation error messages
    - **Property 7: SMTP Validation Error Messages**
    - **Validates: Requirements 2.4**
    - Test that all SMTP failures return descriptive errors

- [x] 5. Implement recipient list management
  - [x] 5.1 Create CSV upload and parsing service
    - Implement POST /api/recipient-lists endpoint with multipart/form-data
    - Parse CSV files using Python csv module
    - Extract email addresses and metadata from columns
    - Support files up to 10MB
    - Store CSV file in S3 or local storage
    - _Requirements: 3.1, 3.5, 3.6_

  - [ ] 5.2 Write property test for CSV email extraction
    - **Property 8: CSV Email Extraction**
    - **Validates: Requirements 3.1**
    - Test that all emails in CSV are extracted

  - [x] 5.3 Add email validation using RFC 5322 standards
    - Implement email validation function using email-validator library
    - Validate each email address during CSV processing
    - Flag invalid emails with specific error reasons
    - Store validation results in Recipient model
    - _Requirements: 3.2, 3.3_

  - [ ] 5.4 Write property test for email validation and flagging
    - **Property 9: Email Validation and Flagging**
    - **Validates: Requirements 3.2, 3.3**
    - Test that invalid emails are flagged with error reasons

  - [x] 5.5 Implement email deduplication within recipient lists
    - Add deduplication logic during CSV processing
    - Use case-insensitive email comparison
    - Keep first occurrence of duplicate emails
    - Update recipient count statistics
    - _Requirements: 3.4_

  - [ ] 5.6 Write property test for email deduplication
    - **Property 10: Email Deduplication**
    - **Validates: Requirements 3.4**
    - Test that duplicate emails (case-insensitive) are removed

  - [x] 5.7 Store recipient metadata from CSV columns
    - Extract all CSV columns beyond email
    - Store metadata as JSONB in Recipient model
    - Support custom field names from CSV headers
    - _Requirements: 3.5_

  - [ ] 5.8 Write property test for recipient metadata preservation
    - **Property 11: Recipient Metadata Preservation**
    - **Validates: Requirements 3.5**
    - Test that all CSV columns are stored as metadata

  - [x] 5.9 Create recipient list retrieval endpoints
    - Implement GET /api/recipient-lists endpoint (list user's lists)
    - Implement GET /api/recipient-lists/{id} endpoint (with recipients)
    - Implement GET /api/recipient-lists/{id}/invalid endpoint (invalid emails only)
    - Implement DELETE /api/recipient-lists/{id} endpoint
    - Add pagination for large recipient lists
    - _Requirements: 3.1_

  - [x] 5.10 Optimize CSV processing for 10,000 recipients in <30 seconds
    - Use batch inserts for recipient records
    - Process CSV in chunks to avoid memory issues
    - Add progress tracking for large uploads
    - _Requirements: 3.7_

- [ ] 6. Checkpoint - Ensure recipient management tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Build email template management
  - [x] 7.1 Create template CRUD endpoints
    - Implement POST /api/templates endpoint
    - Implement GET /api/templates endpoint (list user's templates)
    - Implement GET /api/templates/{id} endpoint
    - Implement PUT /api/templates/{id} endpoint
    - Implement DELETE /api/templates/{id} endpoint
    - _Requirements: 4.1, 4.6_

  - [x] 7.2 Add template variable syntax validation
    - Create validation function for {{variable}} syntax
    - Check for matching braces and valid identifiers
    - Validate on template save
    - Return specific error messages for syntax errors
    - _Requirements: 4.3_

  - [x] 7.3 Write property test for template syntax validation
    - **Property 13: Template Syntax Validation**
    - **Validates: Requirements 4.3**
    - Test that invalid syntax is rejected

  - [x] 7.4 Implement template preview with sample data
    - Create POST /api/templates/{id}/preview endpoint
    - Accept sample data in request body
    - Render template with sample data
    - Return rendered subject and body
    - _Requirements: 4.4_

  - [x] 7.5 Add template variable rendering engine
    - Create template rendering function using Jinja2 or string.Template
    - Replace {{variable}} with values from recipient metadata
    - Handle missing variables gracefully
    - _Requirements: 4.2_

  - [x] 7.6 Write property test for template variable rendering
    - **Property 12: Template Variable Rendering**
    - **Validates: Requirements 4.2**
    - Test that all variables are replaced with metadata values

  - [x] 7.7 Implement template versioning
    - Add version field to Template model
    - Increment version on each update
    - _Requirements: 4.5_

  - [x] 7.8 Write property test for template version increment
    - **Property 14: Template Version Increment**
    - **Validates: Requirements 4.5**
    - Test that version increments on every update

  - [x] 7.9 Add template duplication feature
    - Create POST /api/templates/{id}/duplicate endpoint
    - Copy template with "Copy of" prefix
    - Reset version to 1 for duplicated template
    - _Requirements: 4.6_

- [x] 8. Integrate Claude AI for email optimization
  - [x] 8.1 Set up Claude API client with error handling
    - Install anthropic Python SDK
    - Create Claude API client wrapper
    - Add retry logic with exponential backoff
    - Handle rate limits (429 responses)
    - Set 10-second timeout per request
    - _Requirements: 5.5, 6.1_

  - [x] 8.2 Implement AI subject line generation
    - Create POST /api/ai/generate-subjects endpoint
    - Call Claude API with email body as context
    - Generate exactly 5 subject line alternatives
    - Return results within 3 seconds
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [x] 8.3 Write property test for subject line generation count
    - **Property 15: Subject Line Generation Count**
    - **Validates: Requirements 5.1**
    - Test that exactly 5 subject lines are returned

  - [x] 8.4 Write property test for AI service error handling
    - **Property 16: AI Service Error Handling**
    - **Validates: Requirements 5.5**
    - Test that AI failures return descriptive errors

  - [x] 8.5 Implement AI email personalization
    - Create POST /api/ai/personalize endpoint
    - Accept template_id and recipient_ids
    - Process personalization per recipient
    - Store personalized content for each recipient
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 8.6 Write property test for AI personalization with metadata
    - **Property 17: AI Personalization Uses Metadata**
    - **Validates: Requirements 6.1**
    - Test that personalized content incorporates recipient metadata

  - [x] 8.7 Add spam score analysis
    - Create POST /api/ai/spam-check endpoint
    - Call Claude API to analyze email content
    - Return score between 0-100
    - Provide specific recommendations
    - Flag spam trigger words
    - Complete analysis within 2 seconds
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [x] 8.8 Write property tests for spam analysis
    - **Property 19: Spam Score Range Validation**
    - **Validates: Requirements 7.2**
    - Test that score is always 0-100
    - **Property 20: Spam Analysis Completeness**
    - **Validates: Requirements 7.3, 7.4**
    - Test that recommendations and trigger words are included

  - [x] 8.9 Implement template-only mode (AI disabled)
    - Add enable_ai_personalization flag to Campaign model
    - When disabled, use only template variable substitution
    - Skip AI personalization calls
    - _Requirements: 6.5_

  - [x] 8.10 Write property test for template-only mode
    - **Property 18: Template-Only Mode**
    - **Validates: Requirements 6.5**
    - Test that AI is not called when personalization is disabled

- [ ] 9. Checkpoint - Ensure AI integration tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Build campaign management system
  - [x] 10.1 Create campaign CRUD endpoints
    - Implement POST /api/campaigns endpoint
    - Implement GET /api/campaigns endpoint (list user's campaigns)
    - Implement GET /api/campaigns/{id} endpoint
    - Implement PUT /api/campaigns/{id} endpoint
    - Implement DELETE /api/campaigns/{id} endpoint
    - Support draft and scheduled campaigns
    - _Requirements: 8.1, 8.5, 8.6_

  - [x] 10.2 Write property test for campaign-recipient association
    - **Property 21: Campaign-Recipient Association**
    - **Validates: Requirements 8.2**
    - Test that campaigns maintain valid recipient list reference

  - [x] 10.3 Add campaign validation before activation
    - Validate all required fields are populated (name, subject, template, recipient_list, smtp_config)
    - Check that recipient list has valid emails
    - Return descriptive errors for missing fields
    - _Requirements: 8.4_

  - [x] 10.4 Write property test for campaign activation validation
    - **Property 22: Campaign Activation Validation**
    - **Validates: Requirements 8.4**
    - Test that incomplete campaigns cannot be activated

  - [x] 10.5 Implement campaign activation endpoint
    - Create POST /api/campaigns/{id}/activate endpoint
    - Validate campaign configuration
    - Create Celery task for campaign sending
    - Update campaign status to "queued"
    - Return job_id for progress tracking
    - _Requirements: 8.1, 9.1_

  - [x] 10.6 Write property test for background job creation
    - **Property 23: Background Job Creation**
    - **Validates: Requirements 9.1**
    - Test that activation creates async job

  - [x] 10.7 Add campaign progress tracking endpoint
    - Create GET /api/campaigns/{id}/progress endpoint
    - Return total, sent, failed, pending counts
    - Calculate progress percentage
    - Estimate completion time based on send rate
    - _Requirements: 9.7_

  - [ ] 10.8 Implement scheduled campaign execution
    - Add scheduled_at field to Campaign model
    - Create Celery beat task to check for scheduled campaigns
    - Activate campaigns when scheduled_at is reached
    - _Requirements: 8.5_

- [x] 11. Implement bulk email sending pipeline
  - [x] 11.1 Create main campaign sending Celery task
    - Implement send_campaign Celery task
    - Load campaign, recipients, template, SMTP config
    - If AI personalization enabled, batch personalize content
    - Create individual send_email tasks for each recipient
    - Update campaign status to "sending"
    - _Requirements: 9.1, 6.4_

  - [x] 11.2 Implement individual email sending task with retry logic
    - Create send_email_task Celery task with max_retries=3
    - Render template with recipient data
    - Embed unique tracking pixel
    - Wrap URLs with click trackers
    - Send via SMTP
    - Log send attempt with status
    - Retry with exponential backoff (60s, 120s, 240s) on failure
    - _Requirements: 9.3, 9.4, 9.5, 9.6_

  - [x] 11.3 Write property test for unique tracking pixel embedding
    - **Property 24: Unique Tracking Pixel Embedding**
    - **Validates: Requirements 9.3**
    - Test that each email has unique tracking ID

  - [x] 11.4 Write property test for URL click tracking
    - **Property 25: URL Click Tracking**
    - **Validates: Requirements 9.4**
    - Test that all URLs are wrapped with click trackers

  - [x] 11.5 Write property test for email send retry logic
    - **Property 26: Email Send Retry Logic**
    - **Validates: Requirements 9.5**
    - Test that failed sends retry 3 times with exponential backoff

  - [x] 11.6 Write property test for email send logging
    - **Property 27: Email Send Logging**
    - **Validates: Requirements 9.6**
    - Test that all send attempts are logged

  - [x] 11.7 Implement real-time progress updates
    - Update campaign sent_count and failed_count after each email
    - Cache progress metrics in Redis for fast retrieval
    - Update campaign status to "completed" when all emails processed
    - _Requirements: 9.7_

  - [ ] 11.8 Write property test for campaign progress updates
    - **Property 28: Campaign Progress Updates**
    - **Validates: Requirements 9.7**
    - Test that progress metrics update as emails are processed

  - [ ] 11.9 Implement rate limiting for email sending
    - Configure Celery task rate limit to 1000 emails/minute
    - Respect SMTP provider rate limits
    - Add configurable rate limit per SMTP config
    - _Requirements: 9.2_

  - [x] 11.10 Add tracking pixel and click tracker URL generation
    - Generate unique tracking_id (UUID) per recipient per campaign
    - Create tracking pixel HTML: `<img src="/track/open/{tracking_id}" width="1" height="1" />`
    - Wrap URLs: replace href with `/track/click/{tracking_id}?url={encoded_url}`
    - Embed tracking pixel at end of email body
    - _Requirements: 9.3, 9.4_

- [ ] 12. Checkpoint - Ensure email sending tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Build email tracking and analytics
  - [x] 13.1 Implement tracking pixel endpoint
    - Create GET /track/open/{tracking_id} endpoint
    - Look up EmailLog by tracking_id
    - Create EmailEvent record with event_type="open"
    - Store timestamp, user_agent, IP address
    - Return 1x1 transparent PNG image
    - _Requirements: 9.3_

  - [x] 13.2 Implement click tracker endpoint
    - Create GET /track/click/{tracking_id} endpoint with url query parameter
    - Look up EmailLog by tracking_id
    - Create EmailEvent record with event_type="click"
    - Store clicked URL, timestamp, user_agent, IP address
    - Return 302 redirect to original URL
    - _Requirements: 9.4_

  - [x] 13.3 Add bounce webhook handler
    - Create POST /api/webhooks/bounce endpoint
    - Parse bounce notification from SMTP provider
    - Update EmailLog status to "bounced"
    - Store bounce reason
    - _Requirements: 9.6_

  - [x] 13.4 Build campaign analytics endpoint
    - Create GET /api/campaigns/{id}/analytics endpoint
    - Calculate total_sent, total_opened, total_clicked, total_bounced
    - Calculate open_rate, click_rate, bounce_rate
    - Aggregate opens and clicks over time for charts
    - Use database queries with proper indexes
    - _Requirements: 9.7_

  - [x] 13.5 Write unit tests for analytics calculations
    - Test open rate calculation: (unique opens / total sent) * 100
    - Test click rate calculation: (unique clicks / total sent) * 100
    - Test bounce rate calculation: (total bounced / total sent) * 100
    - Test edge cases (zero sent, zero opens)

- [ ] 14. Build React frontend application
  - [ ] 14.1 Set up React project with Vite and Tailwind CSS
    - Initialize Vite project with React and TypeScript
    - Install and configure Tailwind CSS
    - Install shadcn/ui components
    - Set up React Router for navigation
    - Configure TanStack Query for data fetching
    - Set up Zustand for state management
    - _Requirements: 1.1_

  - [ ] 14.2 Create authentication pages
    - Build registration page with form validation
    - Build login page with JWT token storage
    - Build email verification page
    - Implement token refresh logic
    - Add protected route wrapper
    - _Requirements: 1.1, 1.3, 1.4_

  - [ ] 14.3 Build SMTP configuration management UI
    - Create SMTP config list page
    - Build SMTP config form (create/edit)
    - Add provider selection (Gmail, SendGrid, Mailgun, Custom)
    - Implement test email button
    - Show validation status
    - _Requirements: 2.1, 2.3, 2.5_

  - [ ] 14.4 Create recipient list upload interface
    - Build recipient list page with upload button
    - Implement CSV file upload with drag-and-drop
    - Show upload progress
    - Display validation results (valid/invalid counts)
    - Show list of invalid emails with error reasons
    - _Requirements: 3.1, 3.2, 3.3_

  - [ ] 14.5 Build email template editor
    - Integrate Monaco Editor for template editing
    - Add syntax highlighting for {{variables}}
    - Implement template preview panel
    - Add sample data input for preview
    - Create template list page
    - Build template form (create/edit/duplicate)
    - _Requirements: 4.1, 4.2, 4.4, 4.6_

  - [ ] 14.6 Create AI features UI
    - Add "Generate Subject Lines" button in campaign form
    - Display 5 generated subject lines with selection
    - Add "Check Spam Score" button
    - Display spam score with recommendations and trigger words
    - Add AI personalization toggle in campaign form
    - _Requirements: 5.1, 6.1, 7.1, 7.2, 7.3_

  - [ ] 14.7 Build campaign creation wizard
    - Create multi-step campaign form
    - Step 1: Basic info (name, subject)
    - Step 2: Select template
    - Step 3: Select recipient list
    - Step 4: Select SMTP config
    - Step 5: AI options (personalization, subject generation)
    - Step 6: Review and activate
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [ ] 14.8 Implement campaign list and detail pages
    - Build campaign list page with status filters
    - Show campaign cards with key metrics
    - Create campaign detail page
    - Display campaign configuration
    - Show real-time progress during sending
    - Add activate/pause/delete actions
    - _Requirements: 8.1, 9.7_

  - [ ] 14.9 Build analytics dashboard with Recharts
    - Create analytics page for campaign
    - Display key metrics (sent, opened, clicked, bounced)
    - Show open rate, click rate, bounce rate
    - Add line charts for opens and clicks over time
    - Add responsive design for mobile
    - _Requirements: 9.7_

  - [ ] 14.10 Write frontend unit tests
    - Test authentication flow
    - Test form validation
    - Test API integration with mocked responses
    - Test routing and protected routes

- [ ] 15. Checkpoint - Ensure frontend integration works
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 16. Add security and production readiness
  - [ ] 16.1 Implement HTTPS enforcement in production
    - Configure Django SECURE_SSL_REDIRECT
    - Set SECURE_HSTS_SECONDS
    - Add security headers middleware
    - _Requirements: 1.7_

  - [x] 16.2 Add comprehensive error handling
    - Create custom exception handlers for DRF
    - Return consistent error response format
    - Add error logging with context
    - Redact sensitive data from logs
    - _Requirements: 2.4, 5.5_

  - [ ] 16.3 Implement audit logging for sensitive operations
    - Log user registration and login attempts
    - Log SMTP config changes
    - Log campaign activations
    - Log email send failures
    - Store logs with user_id, timestamp, action, IP address

  - [ ] 16.4 Add input validation and sanitization
    - Validate all API inputs with DRF serializers
    - Sanitize email content to prevent XSS
    - Validate file uploads (size, type)
    - Add SQL injection prevention (use ORM only)
    - _Requirements: 1.2, 3.6_

  - [ ] 16.5 Write security tests
    - Test password hashing (bcrypt)
    - Test SMTP credential encryption
    - Test JWT token security
    - Test rate limiting
    - Test CORS configuration
    - Test input validation

- [ ] 17. Set up deployment infrastructure
  - [ ] 17.1 Create Docker containers
    - Write Dockerfile for Django application
    - Write Dockerfile for Celery worker
    - Write Dockerfile for React frontend
    - Create docker-compose.yml for local development
    - Configure PostgreSQL and Redis containers

  - [ ] 17.2 Configure production deployment
    - Set up AWS/Render deployment configuration
    - Configure environment variables
    - Set up PostgreSQL database (RDS or managed)
    - Set up Redis instance (ElastiCache or managed)
    - Configure S3 bucket for CSV uploads
    - Set up load balancer and SSL certificate

  - [ ] 17.3 Add monitoring and logging
    - Install Sentry for error tracking
    - Configure CloudWatch or Datadog for metrics
    - Set up log aggregation
    - Create alerting rules (error rate, queue depth, etc.)
    - Add health check endpoints

  - [ ] 17.4 Configure backup and disaster recovery
    - Set up automated PostgreSQL backups
    - Configure Redis persistence
    - Document recovery procedures
    - Test backup restoration

- [ ] 18. Final integration and testing
  - [ ] 18.1 Run full integration test suite
    - Test complete user flow: registration → campaign → sending → analytics
    - Test error scenarios and edge cases
    - Test with multiple SMTP providers
    - Test with large recipient lists (10,000+)

  - [ ] 18.2 Perform load testing
    - Test 1,000 emails/minute sending rate
    - Test 100 concurrent API requests
    - Test CSV upload with 10,000 recipients
    - Verify performance targets are met

  - [ ] 18.3 Conduct security audit
    - Run OWASP ZAP or similar security scanner
    - Test for SQL injection, XSS, CSRF
    - Verify authentication and authorization
    - Test rate limiting and input validation

  - [ ] 18.4 Create user documentation
    - Write API documentation (OpenAPI/Swagger)
    - Create user guide for frontend
    - Document deployment procedures
    - Write troubleshooting guide

- [ ] 19. Final checkpoint - Production deployment
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP delivery
- Each task references specific requirements for traceability
- Property-based tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Checkpoints ensure incremental validation and allow for user feedback
- The implementation uses Python/Django for backend and TypeScript/React for frontend as specified in the design
- All external service integrations (Claude AI, SMTP, S3) include error handling and retry logic
- Security is prioritized throughout with encryption, authentication, rate limiting, and input validation
