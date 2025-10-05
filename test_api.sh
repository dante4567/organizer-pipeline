#!/bin/bash
# Easy API testing script for Organizer API
# Usage: ./test_api.sh [tasks|calendar|contacts|all]

BASE_URL="http://127.0.0.1:8000/api/v1"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_test() {
    echo -e "${BLUE}==> $1${NC}"
}

echo_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Test Tasks CRUD
test_tasks() {
    echo_test "Testing Tasks CRUD"

    # CREATE
    echo_test "1. Creating a task..."
    TASK_RESPONSE=$(curl -s -X POST "$BASE_URL/tasks/" \
        -H "Content-Type: application/json" \
        -d '{
            "title": "Test Task from Script",
            "description": "Testing the API",
            "priority": "high",
            "tags": ["test", "automation"]
        }')
    TASK_ID=$(echo $TASK_RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
    echo "Task ID: $TASK_ID"
    echo_success "Task created"

    # READ ALL
    echo_test "2. Getting all tasks..."
    curl -s "$BASE_URL/tasks/" | python3 -m json.tool
    echo_success "Retrieved tasks"

    # READ BY PRIORITY
    echo_test "3. Getting high priority tasks..."
    curl -s "$BASE_URL/tasks/?priority=high" | python3 -m json.tool
    echo_success "Filtered tasks"

    # UPDATE
    echo_test "4. Updating task..."
    curl -s -X PUT "$BASE_URL/tasks/$TASK_ID" \
        -H "Content-Type: application/json" \
        -d '{
            "title": "Updated Task",
            "status": "completed",
            "priority": "high"
        }' | python3 -m json.tool
    echo_success "Task updated"

    # DELETE
    echo_test "5. Deleting task..."
    curl -s -X DELETE "$BASE_URL/tasks/$TASK_ID"
    echo_success "Task deleted"

    echo ""
}

# Test Calendar CRUD
test_calendar() {
    echo_test "Testing Calendar CRUD"

    # CREATE
    echo_test "1. Creating a calendar event..."
    EVENT_RESPONSE=$(curl -s -X POST "$BASE_URL/calendar/events" \
        -H "Content-Type: application/json" \
        -d '{
            "title": "Team Meeting",
            "description": "Weekly sync",
            "start_time": "2025-10-10T14:00:00Z",
            "end_time": "2025-10-10T15:00:00Z",
            "event_type": "meeting",
            "location": "Conference Room A",
            "attendees": ["alice@example.com", "bob@example.com"],
            "calendar_name": "Work"
        }')
    EVENT_ID=$(echo $EVENT_RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
    echo "Event ID: $EVENT_ID"
    echo_success "Event created"

    # READ ALL
    echo_test "2. Getting all events..."
    curl -s "$BASE_URL/calendar/events" | python3 -m json.tool
    echo_success "Retrieved events"

    # READ BY TYPE
    echo_test "3. Getting meeting events..."
    curl -s "$BASE_URL/calendar/events?event_type=meeting" | python3 -m json.tool
    echo_success "Filtered events"

    # UPDATE
    echo_test "4. Updating event..."
    curl -s -X PUT "$BASE_URL/calendar/events/$EVENT_ID" \
        -H "Content-Type: application/json" \
        -d '{
            "title": "Team Meeting - Updated",
            "description": "Weekly sync with notes",
            "start_time": "2025-10-10T14:00:00Z",
            "end_time": "2025-10-10T16:00:00Z",
            "event_type": "meeting",
            "location": "Conference Room B"
        }' | python3 -m json.tool
    echo_success "Event updated"

    # DELETE
    echo_test "5. Deleting event..."
    curl -s -X DELETE "$BASE_URL/calendar/events/$EVENT_ID"
    echo_success "Event deleted"

    echo ""
}

# Test Contacts CRUD
test_contacts() {
    echo_test "Testing Contacts CRUD"

    # CREATE
    echo_test "1. Creating a contact..."
    CONTACT_RESPONSE=$(curl -s -X POST "$BASE_URL/contacts/" \
        -H "Content-Type: application/json" \
        -d '{
            "full_name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "organization": "Acme Corp"
        }')
    CONTACT_ID=$(echo $CONTACT_RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
    echo "Contact ID: $CONTACT_ID"
    echo_success "Contact created"

    # READ ALL
    echo_test "2. Getting all contacts..."
    curl -s "$BASE_URL/contacts/" | python3 -m json.tool
    echo_success "Retrieved contacts"

    # UPDATE
    echo_test "3. Updating contact..."
    curl -s -X PUT "$BASE_URL/contacts/$CONTACT_ID" \
        -H "Content-Type: application/json" \
        -d '{
            "full_name": "John Doe Jr.",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "organization": "Acme Corp"
        }' | python3 -m json.tool
    echo_success "Contact updated"

    # DELETE
    echo_test "4. Deleting contact..."
    curl -s -X DELETE "$BASE_URL/contacts/$CONTACT_ID"
    echo_success "Contact deleted"

    echo ""
}

# Main
case "${1:-all}" in
    tasks)
        test_tasks
        ;;
    calendar)
        test_calendar
        ;;
    contacts)
        test_contacts
        ;;
    all)
        test_tasks
        test_calendar
        test_contacts
        ;;
    *)
        echo "Usage: $0 [tasks|calendar|contacts|all]"
        exit 1
        ;;
esac

echo_success "All tests completed!"
