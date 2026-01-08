#!/bin/bash

# Mental Health Chatbot - Database Viewer Script
# This script helps you view data from your testing database

DB_FILE="mental_health.db"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Mental Health Chatbot - Data Viewer${NC}"
echo -e "${BLUE}================================${NC}\n"

if [ ! -f "$DB_FILE" ]; then
    echo -e "${YELLOW}Database file not found: $DB_FILE${NC}"
    exit 1
fi

# Function to show menu
show_menu() {
    echo -e "\n${GREEN}What would you like to view?${NC}"
    echo "1. All Users"
    echo "2. Recent Chat Messages (last 20)"
    echo "3. Assessment Results"
    echo "4. Mood Tracking Data"
    echo "5. User Activity Summary"
    echo "6. Export All Data to CSV"
    echo "7. Backup Database"
    echo "8. Clear Test Data"
    echo "9. Exit"
    echo -n "Enter your choice [1-9]: "
}

# Function to view users
view_users() {
    echo -e "\n${GREEN}=== All Users ===${NC}"
    sqlite3 -header -column "$DB_FILE" "
        SELECT 
            id,
            username,
            email,
            created_at,
            last_login
        FROM users
        ORDER BY created_at DESC;
    "
}

# Function to view recent chats
view_chats() {
    echo -e "\n${GREEN}=== Recent Chat Messages ===${NC}"
    sqlite3 -header -column "$DB_FILE" "
        SELECT 
            ch.id,
            u.username,
            substr(ch.message, 1, 50) as message,
            substr(ch.response, 1, 50) as response,
            ch.created_at
        FROM chat_history ch
        LEFT JOIN users u ON ch.user_id = u.id
        ORDER BY ch.created_at DESC
        LIMIT 20;
    "
}

# Function to view assessments
view_assessments() {
    echo -e "\n${GREEN}=== Assessment Results ===${NC}"
    sqlite3 -header -column "$DB_FILE" "
        SELECT 
            ar.id,
            u.username,
            ar.assessment_type,
            ar.score,
            ar.severity,
            ar.created_at
        FROM assessment_results ar
        LEFT JOIN users u ON ar.user_id = u.id
        ORDER BY ar.created_at DESC;
    "
}

# Function to view mood tracking
view_mood() {
    echo -e "\n${GREEN}=== Mood Tracking Data ===${NC}"
    sqlite3 -header -column "$DB_FILE" "
        SELECT 
            mt.id,
            u.username,
            mt.mood,
            mt.timestamp
        FROM mood_tracker mt
        LEFT JOIN users u ON mt.user_id = u.id
        ORDER BY mt.timestamp DESC
        LIMIT 50;
    "
}

# Function to view activity summary
view_summary() {
    echo -e "\n${GREEN}=== User Activity Summary ===${NC}"
    sqlite3 -header -column "$DB_FILE" "
        SELECT 
            u.username,
            u.email,
            COUNT(DISTINCT cs.id) as total_sessions,
            COUNT(ch.id) as total_messages,
            COUNT(DISTINCT ar.id) as assessments_taken,
            u.created_at as joined_date,
            u.last_login
        FROM users u
        LEFT JOIN chat_sessions cs ON u.id = cs.user_id
        LEFT JOIN chat_history ch ON u.id = ch.user_id
        LEFT JOIN assessment_results ar ON u.id = ar.user_id
        GROUP BY u.id
        ORDER BY total_messages DESC;
    "
}

# Function to export data
export_data() {
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    EXPORT_DIR="exports"
    mkdir -p "$EXPORT_DIR"
    
    echo -e "\n${GREEN}Exporting data to CSV files...${NC}"
    
    sqlite3 -header -csv "$DB_FILE" "SELECT * FROM users;" > "$EXPORT_DIR/users_$TIMESTAMP.csv"
    sqlite3 -header -csv "$DB_FILE" "SELECT * FROM chat_history;" > "$EXPORT_DIR/chats_$TIMESTAMP.csv"
    sqlite3 -header -csv "$DB_FILE" "SELECT * FROM assessment_results;" > "$EXPORT_DIR/assessments_$TIMESTAMP.csv"
    sqlite3 -header -csv "$DB_FILE" "SELECT * FROM mood_tracker;" > "$EXPORT_DIR/mood_$TIMESTAMP.csv"
    
    echo -e "${GREEN}✓ Data exported to $EXPORT_DIR/ directory${NC}"
    ls -lh "$EXPORT_DIR"/*_$TIMESTAMP.csv
}

# Function to backup database
backup_db() {
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="mental_health_backup_$TIMESTAMP.db"
    
    cp "$DB_FILE" "$BACKUP_FILE"
    echo -e "\n${GREEN}✓ Database backed up to: $BACKUP_FILE${NC}"
    ls -lh "$BACKUP_FILE"
}

# Function to clear test data
clear_test_data() {
    echo -e "\n${YELLOW}⚠️  WARNING: This will delete all data except the first admin user!${NC}"
    echo -n "Are you sure? (yes/no): "
    read -r confirm
    
    if [ "$confirm" = "yes" ]; then
        # Backup first
        backup_db
        
        sqlite3 "$DB_FILE" "
            DELETE FROM chat_history WHERE user_id > 1;
            DELETE FROM chat_sessions WHERE user_id > 1;
            DELETE FROM assessment_results WHERE user_id > 1;
            DELETE FROM mood_tracker WHERE user_id > 1;
            DELETE FROM sentiment_history WHERE user_id > 1;
            DELETE FROM conversations WHERE user_id > 1;
            DELETE FROM users WHERE id > 1;
        "
        
        echo -e "${GREEN}✓ Test data cleared (backup created)${NC}"
    else
        echo -e "${YELLOW}Cancelled.${NC}"
    fi
}

# Main loop
while true; do
    show_menu
    read -r choice
    
    case $choice in
        1) view_users ;;
        2) view_chats ;;
        3) view_assessments ;;
        4) view_mood ;;
        5) view_summary ;;
        6) export_data ;;
        7) backup_db ;;
        8) clear_test_data ;;
        9) echo -e "\n${GREEN}Goodbye!${NC}"; exit 0 ;;
        *) echo -e "${YELLOW}Invalid choice. Please try again.${NC}" ;;
    esac
done
