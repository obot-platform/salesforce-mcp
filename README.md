# Salesforce MCP Server

A Model Context Protocol (MCP) server implementation for Salesforce, providing tools to manage contacts, leads, opportunities, accounts, cases, and more.

## Features

This MCP server provides the following tools:

### Contact Management
- `describe_contact_schema` - Get available fields for Contact objects
- `create_contact` - Create new contacts
- `update_contact` - Update existing contacts
- `delete_contact` - Delete contacts

### Lead Management
- `describe_lead_schema` - Get available fields for Lead objects
- `create_lead` - Create new leads
- `update_lead` - Update existing leads
- `delete_lead` - Delete leads
- `convert_lead_to_opportunity` - Convert leads to opportunities

### Account Management
- `describe_account_schema` - Get available fields for Account objects
- `create_account` - Create new accounts
- `update_account` - Update existing accounts
- `delete_account` - Delete accounts

### Opportunity Management
- `describe_opportunity_schema` - Get available fields for Opportunity objects
- `create_opportunity` - Create new opportunities
- `update_opportunity` - Update existing opportunities
- `delete_opportunity` - Delete opportunities

### Case Management
- `describe_case_schema` - Get available fields for Case objects
- `create_case` - Create new cases
- `update_case` - Update existing cases
- `delete_case` - Delete cases

### Utility Tools
- `query` - Execute SOQL queries
- `get_direct_link` - Get direct URLs to Salesforce objects
- `email_message` - Create email messages using Enhanced Email functionality

## Configuration

No environment variables are required. The server gets configuration from HTTP headers:

- `x-forwarded-access-token` - Salesforce access token
- `x-forwarded-salesforce-instance-url` - Salesforce instance URL (e.g., https://yourcompany.my.salesforce.com)

## Usage

The server runs on port 9000 at the path `/mcp/salesforce`. You can test it by visiting:

```
http://localhost:9000/health
```

## Installation

1. Install dependencies:
```bash
uv sync
```

2. Run the server:
```bash
python -m app.main
```