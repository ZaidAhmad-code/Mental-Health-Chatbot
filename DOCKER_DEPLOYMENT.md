# Mental Health Chatbot - Docker Deployment Guide

## 🐳 Quick Start

### Prerequisites
- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (usually comes with Docker Desktop)

### Option 1: Using Docker Compose (Recommended)

1. **Build and run the container:**
   ```bash
   docker-compose up -d
   ```

2. **Access the application:**
   Open your browser and go to: `http://localhost:5000`

3. **Stop the container:**
   ```bash
   docker-compose down
   ```

### Option 2: Using Docker directly

1. **Build the Docker image:**
   ```bash
   docker build -t mental-health-chatbot .
   ```

2. **Run the container:**
   ```bash
   docker run -d -p 5000:5000 \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/mental_health.db:/app/mental_health.db \
     --name mental-health-chatbot \
     mental-health-chatbot
   ```

3. **Access the application:**
   Open your browser and go to: `http://localhost:5000`

4. **Stop the container:**
   ```bash
   docker stop mental-health-chatbot
   docker rm mental-health-chatbot
   ```

## 📊 Database Access

All user data is stored in `mental_health.db` in your local directory. You can access it using:

```bash
# View all users
sqlite3 mental_health.db "SELECT id, username, email, created_at FROM users;"

# View recent chats
sqlite3 mental_health.db "SELECT user_id, message, response, created_at FROM chat_history ORDER BY created_at DESC LIMIT 10;"

# View assessments
sqlite3 mental_health.db "SELECT user_id, assessment_type, score, severity, created_at FROM assessment_results ORDER BY created_at DESC;"
```

## 🔧 Useful Commands

### View logs:
```bash
docker-compose logs -f
```

### Restart the application:
```bash
docker-compose restart
```

### Rebuild after code changes:
```bash
docker-compose up -d --build
```

### Access container shell:
```bash
docker exec -it mental-health-chatbot /bin/bash
```

### Backup database:
```bash
cp mental_health.db mental_health_backup_$(date +%Y%m%d_%H%M%S).db
```

## 📤 Sharing with Friends for Testing

### Method 1: Share Docker Image (Centralized Database)

1. **Build and save the image:**
   ```bash
   docker build -t mental-health-chatbot .
   docker save mental-health-chatbot -o mental-health-chatbot.tar
   ```

2. **Share the .tar file** with your friends

3. **Friends load and run:**
   ```bash
   docker load -i mental-health-chatbot.tar
   docker run -p 5000:5000 mental-health-chatbot
   ```

⚠️ **Important:** With this method, each friend runs their own isolated database on their machine. Their data stays on their computer.

### Method 2: Deploy to Cloud (Shared Database)

Deploy to a cloud service where everyone connects to the same instance:
- **Heroku** (Free tier available)
- **Railway** (Easy deployment)
- **DigitalOcean** (More control)
- **AWS/GCP/Azure** (Enterprise)

With cloud deployment, all testers connect to YOUR server and all data comes to your database.

## 🔒 Privacy & Testing Notes

**What data is collected:**
- ✅ User accounts (username, email, password hash)
- ✅ All chat messages and responses
- ✅ Mental health assessments
- ✅ Mood tracking data
- ✅ Login/activity timestamps

**For Testing:**
- 🔔 Inform testers that data is being collected
- 🔔 Ask them to use fake/test data
- 🔔 Add a testing disclaimer in the app
- 🔔 Delete test data after testing is complete

## 🛠️ Troubleshooting

### Port already in use:
```bash
# Change port in docker-compose.yml from 5000:5000 to 8080:5000
# Then access via http://localhost:8080
```

### Database permission issues:
```bash
chmod 666 mental_health.db
```

### Container won't start:
```bash
docker-compose logs
```

### Clear everything and start fresh:
```bash
docker-compose down -v
rm mental_health.db
docker-compose up -d
```

## 📋 Environment Variables

Create a `.env` file for configuration:
```env
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
GROQ_API_KEY=your-groq-api-key
GOOGLE_API_KEY=your-google-api-key
```

## 🚀 Production Deployment Tips

1. **Set a strong SECRET_KEY** in your environment
2. **Use HTTPS** (Let's Encrypt certificates)
3. **Set up regular database backups**
4. **Monitor disk space** for chat logs
5. **Consider rate limiting** for API calls
6. **Add health check endpoint** for monitoring
