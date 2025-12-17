# Technical Specification Document
## SalesPro CRM Mobile Application

**Version:** 1.0
**Date:** November 2025
**Document Type:** Technical Specification (Database, API, Architecture)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Data Models](#2-data-models)
3. [Database Schema](#3-database-schema)
4. [API Endpoints](#4-api-endpoints)
5. [Enums & Constants](#5-enums--constants)
6. [Entity Relationships](#6-entity-relationships)
7. [Feature-to-Data Mapping](#7-feature-to-data-mapping)

---

## 1. Executive Summary

### 1.1 Project Overview

SalesPro CRM is a mobile-first Customer Relationship Management application designed for sales teams. The application enables users to manage leads, track deals through a sales pipeline, organize tasks, and monitor team performance through analytics dashboards.

### 1.2 Core Modules

| Module | Description |
|--------|-------------|
| **Authentication** | User login, registration, password recovery, onboarding |
| **Dashboard** | KPIs, sales charts, task widgets, activity feed |
| **Leads** | Lead management with filtering, search, and detail views |
| **Deals** | Sales pipeline with Kanban board and list views |
| **Tasks** | Task management with calendar and list views |
| **Notifications** | In-app notification center |
| **Team Management** | Team members, roles, and permissions |
| **Settings** | User profile, preferences, app settings |

### 1.3 User Roles

| Role | Description |
|------|-------------|
| **Admin** | Full access to all features, team management, settings |
| **Sales Manager** | Access to all CRM features, team visibility |
| **Sales Rep** | Access to assigned leads, deals, and tasks |

---

## 2. Data Models

### 2.1 User

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique identifier |
| `name` | String | Yes | Full name |
| `email` | String | Yes | Email address (unique) |
| `phone` | String | No | Phone number |
| `role` | String | Yes | Job title (e.g., "Sales Manager") |
| `avatar` | String | No | URL to profile image |
| `is_admin` | Boolean | Yes | Admin privileges flag |
| `created_at` | DateTime | Yes | Account creation timestamp |
| `updated_at` | DateTime | Yes | Last update timestamp |

### 2.2 Lead

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique identifier |
| `name` | String | Yes | Contact person's full name |
| `company` | String | No | Company name |
| `email` | String | No | Email address |
| `phone` | String | No | Phone number |
| `status` | Enum | Yes | Lead status (see Enums) |
| `source` | Enum | Yes | Lead source (see Enums) |
| `priority` | Enum | Yes | Priority level (see Enums) |
| `assigned_to` | UUID | Yes | FK to User |
| `tags` | String[] | No | Array of custom tags |
| `notes` | Text | No | General notes |
| `created_at` | DateTime | Yes | Creation timestamp |
| `updated_at` | DateTime | Yes | Last update timestamp |

### 2.3 Deal

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique identifier |
| `title` | String | Yes | Deal title/name |
| `value` | Decimal | Yes | Deal monetary value |
| `stage` | Enum | Yes | Pipeline stage (see Enums) |
| `probability` | Integer | Yes | Win probability (0-100%) |
| `close_date` | Date | Yes | Expected close date |
| `lead_id` | UUID | No | FK to Lead |
| `company_name` | String | Yes | Company name |
| `products` | String[] | No | Array of product names |
| `assigned_to` | UUID | Yes | FK to User |
| `priority` | Enum | Yes | Priority level (see Enums) |
| `labels` | String[] | No | Custom labels |
| `created_at` | DateTime | Yes | Creation timestamp |
| `updated_at` | DateTime | Yes | Last update timestamp |

### 2.4 Task

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique identifier |
| `title` | String | Yes | Task title |
| `description` | Text | No | Task description |
| `due_date` | DateTime | Yes | Due date and time |
| `completed` | Boolean | Yes | Completion status |
| `completed_at` | DateTime | No | Completion timestamp |
| `priority` | Enum | Yes | Priority level (see Enums) |
| `assigned_to` | UUID | Yes | FK to User |
| `related_type` | Enum | No | Related entity type ('lead' or 'deal') |
| `related_id` | UUID | No | FK to Lead or Deal |
| `created_at` | DateTime | Yes | Creation timestamp |
| `updated_at` | DateTime | Yes | Last update timestamp |

### 2.5 Activity

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique identifier |
| `type` | Enum | Yes | Activity type (see Enums) |
| `title` | String | Yes | Activity title |
| `description` | Text | No | Activity description |
| `timestamp` | DateTime | Yes | When activity occurred |
| `user_id` | UUID | Yes | FK to User who performed action |
| `related_type` | Enum | Yes | Related entity type ('lead', 'deal', or 'task') |
| `related_id` | UUID | Yes | FK to related entity |
| `created_at` | DateTime | Yes | Creation timestamp |

### 2.6 Notification

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique identifier |
| `user_id` | UUID | Yes | FK to User (recipient) |
| `type` | Enum | Yes | Notification type (see Enums) |
| `title` | String | Yes | Notification title |
| `message` | Text | Yes | Notification body |
| `read` | Boolean | Yes | Read status |
| `related_type` | Enum | No | Related entity type |
| `related_id` | UUID | No | FK to related entity |
| `timestamp` | DateTime | Yes | Creation timestamp |

---

## 3. Database Schema

### 3.1 Table: `users`

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    role VARCHAR(100) NOT NULL,
    avatar VARCHAR(500),
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
```

### 3.2 Table: `leads`

```sql
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'new',
    source VARCHAR(20) NOT NULL,
    priority VARCHAR(10) NOT NULL DEFAULT 'medium',
    assigned_to UUID NOT NULL REFERENCES users(id),
    tags TEXT[],
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_lead_status CHECK (status IN ('new', 'contacted', 'qualified', 'lost')),
    CONSTRAINT chk_lead_source CHECK (source IN ('website', 'referral', 'linkedin', 'cold-call', 'trade-show')),
    CONSTRAINT chk_lead_priority CHECK (priority IN ('low', 'medium', 'high'))
);

CREATE INDEX idx_leads_assigned_to ON leads(assigned_to);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_source ON leads(source);
CREATE INDEX idx_leads_created_at ON leads(created_at DESC);
```

### 3.3 Table: `deals`

```sql
CREATE TABLE deals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    value DECIMAL(15, 2) NOT NULL,
    stage VARCHAR(20) NOT NULL DEFAULT 'prospecting',
    probability INTEGER NOT NULL DEFAULT 20,
    close_date DATE NOT NULL,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    company_name VARCHAR(255) NOT NULL,
    products TEXT[],
    assigned_to UUID NOT NULL REFERENCES users(id),
    priority VARCHAR(10) NOT NULL DEFAULT 'medium',
    labels TEXT[],
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_deal_stage CHECK (stage IN ('prospecting', 'qualified', 'proposal', 'negotiation', 'closed-won', 'closed-lost')),
    CONSTRAINT chk_deal_priority CHECK (priority IN ('low', 'medium', 'high')),
    CONSTRAINT chk_deal_probability CHECK (probability >= 0 AND probability <= 100)
);

CREATE INDEX idx_deals_assigned_to ON deals(assigned_to);
CREATE INDEX idx_deals_stage ON deals(stage);
CREATE INDEX idx_deals_close_date ON deals(close_date);
CREATE INDEX idx_deals_lead_id ON deals(lead_id);
```

### 3.4 Table: `tasks`

```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    due_date TIMESTAMP WITH TIME ZONE NOT NULL,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at TIMESTAMP WITH TIME ZONE,
    priority VARCHAR(10) NOT NULL DEFAULT 'medium',
    assigned_to UUID NOT NULL REFERENCES users(id),
    related_type VARCHAR(10),
    related_id UUID,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_task_priority CHECK (priority IN ('low', 'medium', 'high')),
    CONSTRAINT chk_task_related_type CHECK (related_type IS NULL OR related_type IN ('lead', 'deal'))
);

CREATE INDEX idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_tasks_completed ON tasks(completed);
CREATE INDEX idx_tasks_related ON tasks(related_type, related_id);
```

### 3.5 Table: `activities`

```sql
CREATE TABLE activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    user_id UUID NOT NULL REFERENCES users(id),
    related_type VARCHAR(10) NOT NULL,
    related_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_activity_type CHECK (type IN ('call', 'email', 'note', 'meeting', 'stage_change', 'deal_won', 'deal_lost', 'task_completed')),
    CONSTRAINT chk_activity_related_type CHECK (related_type IN ('lead', 'deal', 'task'))
);

CREATE INDEX idx_activities_user_id ON activities(user_id);
CREATE INDEX idx_activities_related ON activities(related_type, related_id);
CREATE INDEX idx_activities_timestamp ON activities(timestamp DESC);
```

### 3.6 Table: `notifications`

```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    type VARCHAR(10) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    read BOOLEAN NOT NULL DEFAULT FALSE,
    related_type VARCHAR(10),
    related_id UUID,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_notification_type CHECK (type IN ('task', 'deal', 'lead', 'system'))
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_read ON notifications(user_id, read);
CREATE INDEX idx_notifications_timestamp ON notifications(timestamp DESC);
```

### 3.7 Entity-Relationship Diagram (Text)

```
┌──────────────┐       ┌──────────────┐
│    users     │       │    leads     │
├──────────────┤       ├──────────────┤
│ id (PK)      │◄──────│ assigned_to  │
│ name         │       │ id (PK)      │
│ email        │       │ name         │
│ role         │       │ company      │
│ is_admin     │       │ status       │
└──────────────┘       │ source       │
       │               └──────────────┘
       │                      │
       │                      │ (1:N)
       │                      ▼
       │               ┌──────────────┐
       │               │    deals     │
       │               ├──────────────┤
       └──────────────►│ assigned_to  │
                       │ lead_id (FK) │
                       │ id (PK)      │
                       │ title        │
                       │ value        │
                       │ stage        │
                       └──────────────┘
                              │
       ┌──────────────────────┴──────────────────────┐
       │                                              │
       ▼                                              ▼
┌──────────────┐                              ┌──────────────┐
│    tasks     │                              │  activities  │
├──────────────┤                              ├──────────────┤
│ id (PK)      │                              │ id (PK)      │
│ title        │                              │ type         │
│ due_date     │                              │ title        │
│ related_type │ ─────► lead/deal             │ related_type │
│ related_id   │                              │ related_id   │
│ assigned_to  │◄─────────────────────────────│ user_id (FK) │
└──────────────┘                              └──────────────┘

┌──────────────┐
│ notifications│
├──────────────┤
│ id (PK)      │
│ user_id (FK) │ ──────► users
│ type         │
│ title        │
│ related_type │ ──────► lead/deal/task
│ related_id   │
└──────────────┘
```

---

## 4. API Endpoints

### 4.1 Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user account |
| POST | `/api/auth/login` | User login, returns JWT token |
| POST | `/api/auth/logout` | Invalidate user session |
| POST | `/api/auth/forgot-password` | Send password reset email |
| POST | `/api/auth/reset-password` | Reset password with token |
| GET | `/api/auth/me` | Get current authenticated user |

### 4.2 Users & Team

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users/profile` | Get current user profile |
| PUT | `/api/users/profile` | Update current user profile |
| PUT | `/api/users/profile/avatar` | Upload profile avatar |
| PUT | `/api/users/profile/password` | Change password |
| GET | `/api/users/team` | Get all team members |
| POST | `/api/users/team/invite` | Send team invitation |
| PUT | `/api/users/team/{id}/role` | Update team member role |
| DELETE | `/api/users/team/{id}` | Remove team member |

### 4.3 Leads

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/leads` | List leads (supports filters, search, sort, pagination) |
| POST | `/api/leads` | Create new lead |
| GET | `/api/leads/{id}` | Get lead by ID |
| PUT | `/api/leads/{id}` | Update lead |
| DELETE | `/api/leads/{id}` | Delete lead |
| PUT | `/api/leads/{id}/status` | Update lead status |
| POST | `/api/leads/{id}/notes` | Add note to lead |
| GET | `/api/leads/{id}/activities` | Get lead activity timeline |

**Query Parameters for GET `/api/leads`:**
- `search` - Search by name, company, email
- `status` - Filter by status (new, contacted, qualified, lost)
- `source` - Filter by source (website, referral, linkedin, cold-call, trade-show)
- `assigned_to` - Filter by assigned user ID
- `sort` - Sort field (created_at, name, priority)
- `order` - Sort order (asc, desc)
- `page` - Page number
- `limit` - Items per page

### 4.4 Deals

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/deals` | List deals (supports filters, search, pagination) |
| POST | `/api/deals` | Create new deal |
| GET | `/api/deals/{id}` | Get deal by ID |
| PUT | `/api/deals/{id}` | Update deal |
| DELETE | `/api/deals/{id}` | Delete deal |
| PUT | `/api/deals/{id}/stage` | Update deal stage (auto-updates probability) |
| GET | `/api/deals/pipeline` | Get deals grouped by pipeline stage |

**Query Parameters for GET `/api/deals`:**
- `search` - Search by title, company name
- `stage` - Filter by stage
- `assigned_to` - Filter by assigned user ID
- `close_date_from` - Filter by close date range start
- `close_date_to` - Filter by close date range end
- `page` - Page number
- `limit` - Items per page

### 4.5 Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tasks` | List tasks (supports filters, date range) |
| POST | `/api/tasks` | Create new task |
| GET | `/api/tasks/{id}` | Get task by ID |
| PUT | `/api/tasks/{id}` | Update task |
| DELETE | `/api/tasks/{id}` | Delete task |
| PUT | `/api/tasks/{id}/complete` | Toggle task completion |
| GET | `/api/tasks/today` | Get tasks due today |
| GET | `/api/tasks/overdue` | Get overdue tasks |
| GET | `/api/tasks/calendar` | Get tasks for calendar view (by month) |

**Query Parameters for GET `/api/tasks`:**
- `completed` - Filter by completion status (true/false)
- `priority` - Filter by priority
- `due_date_from` - Filter by due date range start
- `due_date_to` - Filter by due date range end
- `assigned_to` - Filter by assigned user ID
- `related_type` - Filter by related entity type
- `related_id` - Filter by related entity ID

### 4.6 Activities

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/activities` | Get activity feed (paginated, recent first) |
| POST | `/api/activities` | Log new activity |
| GET | `/api/activities/entity/{type}/{id}` | Get activities for specific entity |

**Query Parameters for GET `/api/activities`:**
- `user_id` - Filter by user who performed action
- `type` - Filter by activity type
- `related_type` - Filter by related entity type
- `page` - Page number
- `limit` - Items per page

### 4.7 Notifications

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notifications` | Get user notifications (paginated) |
| PUT | `/api/notifications/{id}/read` | Mark notification as read |
| PUT | `/api/notifications/read-all` | Mark all notifications as read |
| GET | `/api/notifications/unread-count` | Get unread notification count |

### 4.8 Dashboard & Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/kpis` | Get KPI metrics (total sales, open deals, pipeline value, conversion rate) |
| GET | `/api/dashboard/pipeline-stats` | Get pipeline funnel data by stage |
| GET | `/api/dashboard/sales-history` | Get monthly sales history for charts |
| GET | `/api/dashboard/deals-closing-soon` | Get deals closing within 7 days |
| GET | `/api/dashboard/task-completion-rate` | Get task completion percentage |

---

## 5. Enums & Constants

### 5.1 Lead Status

| Value | Display Name | Description |
|-------|--------------|-------------|
| `new` | New | Newly created lead, not yet contacted |
| `contacted` | Contacted | Initial contact made |
| `qualified` | Qualified | Lead qualified as potential opportunity |
| `lost` | Lost | Lead disqualified or lost |

### 5.2 Lead Source

| Value | Display Name | Description |
|-------|--------------|-------------|
| `website` | Website | Came through website form |
| `referral` | Referral | Referred by existing customer |
| `linkedin` | LinkedIn | Found via LinkedIn |
| `cold-call` | Cold Call | Acquired through cold calling |
| `trade-show` | Trade Show | Met at trade show/event |

### 5.3 Deal Stage

| Value | Display Name | Probability | Description |
|-------|--------------|-------------|-------------|
| `prospecting` | Prospecting | 20% | Initial stage, exploring opportunity |
| `qualified` | Qualified | 40% | Opportunity confirmed, needs assessment |
| `proposal` | Proposal | 60% | Proposal sent to client |
| `negotiation` | Negotiation | 80% | In final negotiations |
| `closed-won` | Closed Won | 100% | Deal successfully closed |
| `closed-lost` | Closed Lost | 0% | Deal lost to competitor/cancelled |

### 5.4 Priority

| Value | Display Name | Color |
|-------|--------------|-------|
| `high` | High Priority | Red |
| `medium` | Medium Priority | Orange |
| `low` | Low Priority | Gray |

### 5.5 Activity Type

| Value | Display Name | Icon | Description |
|-------|--------------|------|-------------|
| `call` | Phone Call | Phone | Logged phone call |
| `email` | Email | Mail | Email sent/received |
| `note` | Note | StickyNote | General note added |
| `meeting` | Meeting | Calendar | Meeting scheduled/completed |
| `stage_change` | Stage Change | ArrowRight | Deal stage updated |
| `deal_won` | Deal Won | Trophy | Deal closed successfully |
| `deal_lost` | Deal Lost | XCircle | Deal lost |
| `task_completed` | Task Completed | CheckCircle | Task marked complete |

### 5.6 Notification Type

| Value | Display Name | Description |
|-------|--------------|-------------|
| `task` | Task | Task-related notification |
| `deal` | Deal | Deal-related notification |
| `lead` | Lead | Lead-related notification |
| `system` | System | System announcement |

---

## 6. Entity Relationships

### 6.1 Relationship Summary

| Parent | Child | Relationship | FK Column |
|--------|-------|--------------|-----------|
| User | Lead | One-to-Many | `leads.assigned_to` |
| User | Deal | One-to-Many | `deals.assigned_to` |
| User | Task | One-to-Many | `tasks.assigned_to` |
| User | Activity | One-to-Many | `activities.user_id` |
| User | Notification | One-to-Many | `notifications.user_id` |
| Lead | Deal | One-to-Many | `deals.lead_id` |
| Lead/Deal | Task | Polymorphic | `tasks.related_type`, `tasks.related_id` |
| Lead/Deal/Task | Activity | Polymorphic | `activities.related_type`, `activities.related_id` |

### 6.2 Cascade Rules

| Relationship | On Delete |
|--------------|-----------|
| User → Lead | Restrict (cannot delete user with leads) |
| User → Deal | Restrict (cannot delete user with deals) |
| User → Task | Restrict (cannot delete user with tasks) |
| Lead → Deal | Set Null (deals remain, lead_id becomes null) |
| Lead/Deal → Task | Cascade delete or nullify based on business rules |
| Any → Activity | Cascade delete (activities deleted with parent) |
| User → Notification | Cascade delete |

---

## 7. Feature-to-Data Mapping

### 7.1 Authentication Screens

| Screen | API Endpoints | Data Required |
|--------|---------------|---------------|
| Login | `POST /auth/login` | email, password |
| Register | `POST /auth/register` | name, email, password |
| Forgot Password | `POST /auth/forgot-password` | email |
| Splash | None | N/A (static) |
| Onboarding | None | N/A (static) |

### 7.2 Dashboard

| Widget | API Endpoints | Data Required |
|--------|---------------|---------------|
| KPI Cards | `GET /dashboard/kpis` | totalSales, openDeals, pipelineValue, leadsConverted |
| Sales Chart | `GET /dashboard/sales-history` | monthly sales array |
| Task Completion Ring | `GET /dashboard/task-completion-rate` | percentage |
| Pipeline Funnel | `GET /dashboard/pipeline-stats` | stages with counts and values |
| Deals Closing Soon | `GET /dashboard/deals-closing-soon` | deal list |
| Today's Tasks | `GET /tasks/today` | task list (max 3) |
| Activity Feed | `GET /activities` | recent activities (max 4) |
| Notification Badge | `GET /notifications/unread-count` | count |

### 7.3 Leads Module

| Screen | API Endpoints | Data Required |
|--------|---------------|---------------|
| Lead List | `GET /leads` | lead array with filters |
| Lead Detail | `GET /leads/{id}`, `GET /leads/{id}/activities` | lead object, activities |
| Lead Create | `POST /leads` | form data |
| Lead Edit | `PUT /leads/{id}` | form data |
| Add Note | `POST /leads/{id}/notes` | note text |

### 7.4 Deals Module

| Screen | API Endpoints | Data Required |
|--------|---------------|---------------|
| Deal List/Kanban | `GET /deals`, `GET /deals/pipeline` | deals grouped by stage |
| Deal Detail | `GET /deals/{id}` | deal object with lead info |
| Deal Create | `POST /deals` | form data |
| Deal Edit | `PUT /deals/{id}` | form data |
| Stage Update | `PUT /deals/{id}/stage` | new stage value |

### 7.5 Tasks Module

| Screen | API Endpoints | Data Required |
|--------|---------------|---------------|
| Task List | `GET /tasks` | tasks grouped by date category |
| Task Calendar | `GET /tasks/calendar` | tasks by month |
| Task Detail | `GET /tasks/{id}` | task object |
| Task Create | `POST /tasks` | form data |
| Toggle Complete | `PUT /tasks/{id}/complete` | task ID |

### 7.6 Settings & Profile

| Screen | API Endpoints | Data Required |
|--------|---------------|---------------|
| Profile Settings | `GET /users/profile`, `PUT /users/profile` | user object |
| Team Management | `GET /users/team` | team member array |
| Notifications | `GET /notifications`, `PUT /notifications/read-all` | notification array |

---

## Appendix A: Response Format Standards

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 100
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email is required",
    "details": { ... }
  }
}
```

### Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Internal Server Error |

---

## Appendix B: Authentication

All API endpoints (except auth routes) require authentication via JWT Bearer token:

```
Authorization: Bearer <jwt_token>
```

Token should be included in the `Authorization` header of every request.

---

*Document generated from SalesPro CRM SvelteKit prototype analysis.*
