# 🚀 Phase 1 Quick Reference Guide

## 📋 Quick Commands

### Test All Phase 1 Features
```bash
# 1. Health Check
curl http://localhost:5000/api/health | python3 -m json.tool

# 2. User Stats
curl http://localhost:5000/api/analytics/user-stats | python3 -m json.tool

# 3. Cache Stats
curl http://localhost:5000/api/cache/stats | python3 -m json.tool

# 4. Memory Stats
curl http://localhost:5000/api/memory/stats | python3 -m json.tool

# 5. System Analytics
curl http://localhost:5000/api/analytics/system | python3 -m json.tool

# 6. PHQ-9 Trends (30 days)
curl "http://localhost:5000/api/analytics/trends/phq9?days=30" | python3 -m json.tool

# 7. GAD-7 Trends (30 days)
curl "http://localhost:5000/api/analytics/trends/gad7?days=30" | python3 -m json.tool

# 8. Crisis Patterns
curl "http://localhost:5000/api/analytics/crisis-patterns?days=30" | python3 -m json.tool

# 9. Engagement Metrics
curl http://localhost:5000/api/analytics/engagement | python3 -m json.tool

# 10. Mental Health Trajectory
curl http://localhost:5000/api/analytics/trajectory | python3 -m json.tool
```

---

## 🧪 Test Conversation Memory

```bash
# Send multiple messages to build context
curl -X POST http://localhost:5000/ask \
  -d "query=I've been feeling very anxious lately"

curl -X POST http://localhost:5000/ask \
  -d "query=What should I do about it?"
# ^ This should reference the previous message

# Check memory stats
curl http://localhost:5000/api/memory/stats

# Clear memory
curl -X POST http://localhost:5000/api/memory/clear
```

---

## 📊 Test Caching System

```bash
# Make the same query twice (second should be cached)
curl -X POST http://localhost:5000/ask -d "query=What is depression?"
curl -X POST http://localhost:5000/ask -d "query=What is depression?"

# Check cache stats
curl http://localhost:5000/api/cache/stats
# Should show: hit_rate > 0%, hits > 0

# Personal queries are NOT cached (contain "I", "my", "me")
curl -X POST http://localhost:5000/ask -d "query=I am feeling depressed"
curl -X POST http://localhost:5000/ask -d "query=I am feeling depressed"
# Both will hit LLM (not cached)
```

---

## 📝 View Logs

```bash
# Tail application logs
tail -f logs/chatbot.log

# Tail error logs
tail -f logs/errors.log

# Search for errors
grep ERROR logs/chatbot.log

# View last 50 lines
tail -n 50 logs/chatbot.log

# View logs with timestamps
cat logs/chatbot.log | grep "INFO"
```

---

## 🔧 Code Usage Examples

### Import Phase 1 Modules

```python
# In your Python code
from cache_manager import cache, cached_response, cache_llm_response
from analytics import get_user_stats, get_assessment_trends
from conversation_memory import memory_manager, ConversationContextBuilder
from error_handler import logger, handle_errors, log_performance
```

### Use Caching

```python
from cache_manager import cached_response

@cached_response('my_function', ttl=3600)
def expensive_function(param):
    # Your expensive operation
    return result
```

### Use Error Handling

```python
from error_handler import handle_errors, log_performance

@handle_errors("My Feature")
@log_performance("My Operation")
def my_function():
    # Your code here
    logger.info("Operation started")
    # ...
    logger.info("Operation completed")
```

### Get User Analytics

```python
from analytics import get_user_stats, get_mental_health_trajectory

# Get user statistics
stats = get_user_stats(user_id=1)
print(f"Total conversations: {stats['total_conversations']}")

# Get trajectory
trajectory = get_mental_health_trajectory(user_id=1)
print(f"Status: {trajectory['overall_status']}")
print(f"Score: {trajectory['trajectory_score']}/100")
```

### Manage Conversation Memory

```python
from conversation_memory import memory_manager

# Add conversation
memory_manager.add_exchange(user_id, user_msg, bot_response)

# Get context
context = memory_manager.get_conversation_context(user_id)

# Clear memory
memory_manager.clear_memory(user_id)
```

---

## 📚 Documentation Files

| File | Description | Lines |
|------|-------------|-------|
| `PHASE1_COMPLETE.md` | Complete implementation guide | 850+ |
| `PHASE1_DEPLOYED.md` | Deployment summary | 400+ |
| `PHASE1_QUICK_REFERENCE.md` | This file | 200+ |

---

## 🎯 Common Tasks

### Check System Health
```bash
curl http://localhost:5000/api/health
```

### Monitor Cache Performance
```bash
watch -n 5 'curl -s http://localhost:5000/api/cache/stats | python3 -m json.tool'
```

### Monitor Memory Usage
```bash
watch -n 5 'curl -s http://localhost:5000/api/memory/stats | python3 -m json.tool'
```

### Clear All Cache (Admin)
```bash
curl -X POST http://localhost:5000/api/cache/clear
```

### View Real-time Logs
```bash
tail -f logs/chatbot.log | grep -E "INFO|ERROR|WARNING"
```

---

## 🐛 Troubleshooting

### Application Not Starting?
```bash
# Check if port is in use
lsof -i :5000

# Kill existing process
pkill -f "python3 app.py"

# Start fresh
python3 app.py
```

### Cache Not Working?
```bash
# Check cache stats
curl http://localhost:5000/api/cache/stats

# Clear cache and test
curl -X POST http://localhost:5000/api/cache/clear
```

### Logs Not Appearing?
```bash
# Check logs directory
ls -la logs/

# Check file permissions
chmod 755 logs/
chmod 644 logs/*.log
```

### Database Issues?
```bash
# Reinitialize database
python3 -c "from database import init_db; init_db()"
```

---

## 📊 Expected Output Examples

### Healthy System
```json
{
  "status": "Healthy",
  "total_errors": 0,
  "database": "connected",
  "llm_primary": "available",
  "llm_secondary": "available"
}
```

### Active Cache
```json
{
  "hit_rate": "75.50%",
  "hits": 151,
  "misses": 49,
  "size": 42
}
```

### Active Memory
```json
{
  "active_conversations": 15,
  "total_memories": 120
}
```

### User Improving
```json
{
  "trajectory_score": 75,
  "overall_status": "Improving",
  "phq9_trend": "improving",
  "gad7_trend": "stable"
}
```

---

## 🔗 Related Files

- `app.py` - Main application with Phase 1 integration
- `cache_manager.py` - Caching system
- `analytics.py` - Analytics engine
- `conversation_memory.py` - Memory management
- `error_handler.py` - Logging & error handling

---

## 📞 Quick Help

| Issue | Solution |
|-------|----------|
| 404 Error | Check endpoint spelling and method (GET/POST) |
| 500 Error | Check `logs/errors.log` for stack trace |
| Slow responses | Check cache hit rate, consider increasing TTL |
| High memory | Clear conversation memory periodically |
| Missing logs | Ensure `logs/` directory exists |

---

## ✅ Phase 1 Checklist

- [ ] Application running (`python3 app.py`)
- [ ] Health endpoint returns "Healthy"
- [ ] Cache stats accessible
- [ ] Memory stats accessible
- [ ] Analytics endpoints working
- [ ] Logs being written
- [ ] No errors in error log
- [ ] Conversation memory functional
- [ ] Caching reducing LLM calls

---

**Quick Start:** `curl http://localhost:5000/api/health`

**Documentation:** See `PHASE1_COMPLETE.md` for full details

**Next Phase:** User authentication & email notifications
