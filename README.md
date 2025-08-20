# Exchange Odoo data with external systems

A comprehensive integration framework for Odoo 18.0 that provides seamless data exchange capabilities between Odoo and external systems.

## Overview

This repository contains the **ATA Exchange V4** module - a powerful integration solution designed to facilitate bidirectional communication between Odoo and various external systems. The module supports multiple integration patterns including outgoing data transfers, incoming data requests, and real-time API endpoints.

## Features

### 🔄 **Bidirectional Data Exchange**
- **Outgoing Data**: Transfer data from Odoo to external systems
- **Incoming Requests**: Handle incoming API requests from external systems
- **Data Requests**: Request and retrieve data from external systems
- **Inner Data Matching**: Internal data synchronization and matching

### 🔐 **Security & Authentication**
- **API Key Management**: Secure API key generation and validation
- **Multiple Authentication Types**: Support for Basic Auth, Token Auth, and No Auth
- **Token Provider Methods**: Extensible token provider system
- **Access Control**: Comprehensive security rules and permissions

### 📊 **Queue Management**
- **Exchange Queue**: Automatic queuing system for data exchange operations
- **Retry Mechanism**: Configurable retry attempts for failed exchanges
- **State Management**: Track exchange states (new, idle, in_exchange)
- **Cron Integration**: Automated processing via scheduled jobs

### 🔍 **Monitoring & Logging**
- **Exchange Logs**: Detailed logging of all exchange operations
- **Request/Response Tracking**: Complete audit trail of API communications
- **Error Handling**: Comprehensive error logging and reporting
- **Performance Monitoring**: Track exchange performance and statistics

### ⚙️ **Configuration Management**
- **External Systems**: Configure multiple external system connections
- **Method Configuration**: Define and manage exchange methods
- **Domain Mapping**: Map data domains between systems
- **Flexible Settings**: Extensive configuration options

## Architecture

### Core Models

- **`ata.exchange.system`**: External system configuration and connection management
- **`ata.exchange.method`**: Exchange method definitions and configurations
- **`ata.exchange.queue`**: Queue management for exchange operations
- **`ata.exchange.log`**: Comprehensive logging and audit trails
- **`ata.exchange.api.key`**: API key management and security
- **`ata.exchange.handler`**: Request processing and dispatching

### Controllers

- **`AtaExchangeIncomingController`**: Handles incoming HTTP/JSON requests
- **HTTP Dispatchers**: Custom request routing and processing
- **JSON-RPC Support**: Full JSON-RPC protocol implementation

### Data Flow

1. **Incoming Requests** → API Key Validation → Method Resolution → Handler Dispatch → Response
2. **Outgoing Data** → Queue Addition → Processing → External System Call → Logging
3. **Data Requests** → Method Execution → External API Call → Data Processing → Response

## Configuration

### 1. External System Setup

Navigate to **Settings → External Systems** to configure your external systems:

- **System Details**: Name, description, server address, and port
- **Authentication**: Choose authentication type and configure credentials
- **Connection Settings**: SSL, proxy settings, and connection parameters

### 2. Method Configuration

Define exchange methods in **Integration → Methods**:

- **Method Type**: Select from outgoing data, request data, incoming request, or inner types
- **Model Binding**: Link methods to specific Odoo models
- **API Requirements**: Configure API key requirements
- **Notifications**: Set up notification preferences

### 3. API Key Management

Manage API keys in **Integration → API Keys**:

- **Auto-generation**: Automatic UUID-based key generation
- **System Linking**: Associate keys with specific external systems
- **Access Control**: Define method-specific access permissions

### Handling Incoming Requests

The module automatically handles incoming requests at:
- **Standard endpoint**: `/api/ata_exchange_v4/<method_name>`
- **JSON-RPC endpoint**: `/api/ata_exchange_v4/jsonrpc`

## Development

### Extending the Module

1. **Custom Handlers**: Inherit from `ata.exchange.handler` to create custom request handlers
2. **Token Providers**: Extend token provider methods using `selection_add`
3. **Custom Methods**: Create specialized exchange methods for specific use cases

### Testing

The module includes comprehensive error handling and logging for debugging:

- Check **Integration → Exchange Logs** for detailed operation logs
- Monitor **Integration → Queue** for processing status
- Review **Integration → Queue Usage** for performance metrics

## Dependencies

- **Odoo Core**: base, mail
- **Python Packages**: pydantic (for data validation)

## Support

For support and documentation:
- **Documentation**: [Google Docs](https://docs.google.com/document/d/1EeH-4xgoMnLQGrsSZORt5rM4KM5kiPj8zMauZxArKc0/edit?usp=sharing)
- **Issues**: Create an issue on the GitHub repository
- **Contact**: gnezamay@todo.ltd

## License

This module is licensed under the Odoo Proprietary License v1.0 (OPL-1).

## Contributors

- **gnezamay** - Lead Developer and Maintainer

---

**Category**: Integration/Base  
**Author**: gnezamay  
**Website**: todo.ltd
