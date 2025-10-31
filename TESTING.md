# Tixxety API - Testing Guide

## Quick Setup and Testing

### 1. Install Test Dependencies
```bash
pip install httpx pytest-mock
```

### 2. Run All Tests
```bash
# Option 1: Using the Python script
python run_tests.py

# Option 2: Using pytest directly
python -m pytest tests/ -v

```

### 3. Run Specific Tests
```bash
# Run only user tests
python -m pytest tests/test_users.py -v

# Run only event tests  
python -m pytest tests/test_events.py -v

# Run only ticket tests
python -m pytest tests/test_tickets.py -v

# Run only model tests
python -m pytest tests/test_models.py -v

# Run only task tests
python -m pytest tests/test_tasks.py -v

# Run only integration tests
python -m pytest tests/test_integration.py -v
```

### 4. Run a Specific Test Method
```bash
python -m pytest tests/test_users.py::TestUserCreation::test_create_user_success -v
```

## Test Coverage

The test suite includes:

### 📋 **Complete API Endpoint Tests**
- **User Management**: Create users, validate inputs, handle duplicates
- **Event Management**: Create events, list events, validate data
- **Ticket Operations**: Reserve tickets, payment processing, status updates
- **Nearby Events**: Location-based event discovery with distance calculations

### 🔧 **Core Feature Tests**
- **Database Models**: User, Event, Ticket, Venue value objects
- **Business Logic**: Ticket expiration, sold-out events, location calculations
- **Celery Tasks**: Background ticket expiration processing
- **Data Validation**: Input validation, constraint enforcement

### ⚠️ **Error Handling Tests**
- **Validation Errors**: Invalid emails, coordinates, missing fields
- **Business Rule Violations**: Duplicate emails, sold-out events, expired tickets
- **Database Constraints**: Foreign key violations, unique constraints
- **Edge Cases**: Boundary values, empty data, race conditions

### 🔄 **Integration Tests**
- **Complete Workflows**: Full ticket booking process
- **Multiple User Scenarios**: Concurrent bookings, sold-out events
- **API Integration**: End-to-end testing across all endpoints
- **Performance Tests**: Large datasets, concurrent operations

## Test Features

### Success Scenarios ✅
- User registration with valid data
- Event creation with all fields
- Successful ticket reservation and payment
- Nearby events discovery based on location
- Celery task execution for ticket expiration

### Error Scenarios ❌
- Invalid input validation (emails, coordinates, etc.)
- Duplicate email registration attempts
- Booking tickets for sold-out events
- Payment attempts on expired/paid tickets
- Missing user/event references
- Database constraint violations

### Edge Cases 🎯
- Boundary coordinate values (±90°, ±180°)
- Zero/negative ticket quantities
- Same start/end times for events
- Very large distances for nearby events
- Multiple tickets per user per event
- Race conditions in ticket booking

## Example Test Run Output

```
tests/test_users.py::TestUserCreation::test_create_user_success ✓
tests/test_users.py::TestUserCreation::test_create_user_duplicate_email ✓
tests/test_events.py::TestEventCreation::test_create_event_success ✓
tests/test_tickets.py::TestTicketReservation::test_reserve_ticket_success ✓
tests/test_integration.py::TestAPIIntegration::test_complete_ticket_booking_flow ✓
```

The tests use an in-memory SQLite database, so they run fast and don't affect the main database.
