# Scraper Service

## Table of Contents
1. [Introduction](#introduction)
2. [Setup and Run](#setup-and-run)
3. [Enhancements](#enhancements)

## Introduction

A scalable web scraping service built with FastAPI that enables automated extraction of product information from e-commerce websites. The service implements error handling, caching mechanisms, and follows clean architecture principles to ensure maintainability and extensibility.

## Setup and Run

To set up and run the application, follow these steps:

1. **Prerequisites:**
   - Ensure you have Python 3.9 or higher installed on your system.
   - Docker and Docker Compose
   - Redis

2. **Environment Variables:**
    - Edit .env with your configuration
    ```
    cp .env.txt .env
    ```

3. **Running with Docker:**
    - Build and start services
    ```
    docker compose up --build -d
    ```
    - Stop 
    ```
    docker compose down -v
    ```

## Enhancements
 - Applying design pattern such as "Strategy Pattern" for both storage and notification will make it extensible to add new storage or notification methods 
 
 ##  **Performance Optimizations:**
 1. **Caching** 
  -  Implement multi-level caching (Memory + Redis)
  - Intelligent cache invalidation

2. **Parallel Processing**
 - Implement worker pools for distributed scraping
 - Add queue system (Kafka) for job distribution

3. **Rate Limiting**
 - Implement adaptive rate limiting
 - Backoff strategies for failed requests

## **Testing:** 
1. **Test Coverage**
 - Integration Tests 
 - Unit Tests
 - Load Tests

2. **Test Data Management**
 - Test data factories
 - Mock response management
 - Test environment management

Feel free to explore and implement further enhancements to improve the functionality and performance of the Backend Application.
