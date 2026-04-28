# Telegram Bot Deployment Guide for Koyeb

## Prerequisites
- Telegram bot token from @BotFather
- Backend API deployed and accessible
- Koyeb account

## Environment Variables to Set in Koyeb

When deploying to Koyeb, set these environment variables in the Koyeb dashboard:

```
TELEGRAM_BOT_TOKEN=8135539130:AAE-JsiopCXk3mXUf4zmYl_AtU5FHRcuIro
API_BASE_URL=http://backend:8000
```

**Important Notes:**

1. **API_BASE_URL Options:**
   - If backend is in the same Koyeb app: `http://backend:8000`
   - If backend is a separate Koyeb service: `https://your-backend-app.koyeb.app`
   - Make sure the backend URL is accessible from the bot container

2. **Token Storage Warning:**
   - Current implementation uses file-based storage (`data/tokens.json`)
   - This is **ephemeral** on Koyeb - tokens will be lost on restart
   - Users will need to re-login after each deployment
   - For production, migrate to Redis or database storage

## Deployment Steps

### Option 1: Deploy with Docker Compose (Local Testing)

```bash
cd opportunity_finder_bot
docker-compose up --build
```

### Option 2: Deploy to Koyeb

1. **Push code to GitHub** (if not already done)

2. **Create new Koyeb service:**
   - Go to Koyeb dashboard
   - Click "Create Service"
   - Select "GitHub" as source
   - Choose your repository
   - Set build context: `opportunity_finder_bot`
   - Set Dockerfile path: `opportunity_finder_bot/Dockerfile`

3. **Set environment variables:**
   - Add `TELEGRAM_BOT_TOKEN`
   - Add `API_BASE_URL`

4. **Deploy:**
   - Click "Deploy"
   - Wait for build to complete
   - Check logs for "Starting bot with API base URL: ..."

## Testing the Bot

1. **Find your bot on Telegram:**
   - Search for your bot username (set in @BotFather)
   - Or use the link: `https://t.me/YOUR_BOT_USERNAME`

2. **Test basic commands:**
   ```
   /start          - Should show welcome menu
   /login          - Should prompt for email
   /opportunities  - Should ask you to login first
   ```

3. **Test login flow:**
   - Send `/login`
   - Enter your email (registered in backend)
   - Enter your password
   - Should see "Login successful! Your Telegram account is now linked."

4. **Test features:**
   - `/opportunities` - Browse opportunities
   - `/search python` - Search for Python opportunities
   - `/matches` - View your personalized matches

## Troubleshooting

### Bot doesn't respond
- Check Koyeb logs for errors
- Verify `TELEGRAM_BOT_TOKEN` is correct
- Test token with: `curl https://api.telegram.org/bot<TOKEN>/getMe`

### "Unable to fetch opportunities"
- Check `API_BASE_URL` is correct
- Verify backend is running and accessible
- Check backend logs for API errors
- Test backend: `curl <API_BASE_URL>/api/opportunities/`

### "Login failed"
- Verify user exists in backend database
- Check backend logs for authentication errors
- Ensure email/password are correct

### "Your session expired"
- Token storage is ephemeral on Koyeb
- Users need to re-login after bot restarts
- Consider migrating to Redis for persistent storage

### Connection errors
- Check if backend is accessible from bot container
- If using `http://backend:8000`, ensure both services are in same network
- If using external URL, ensure it's publicly accessible

## Known Limitations

1. **Ephemeral Token Storage:**
   - Tokens stored in `data/tokens.json` are lost on restart
   - Users must re-login after each deployment
   - **Fix:** Migrate to Redis or database storage

2. **No Health Check:**
   - Koyeb can't monitor bot health
   - **Fix:** Add HTTP health check endpoint

3. **Limited Pagination:**
   - Only shows 5 results per page
   - **Fix:** Increase limit or make it configurable

4. **No Notification Delivery:**
   - Backend can create Telegram notifications but can't send them
   - **Fix:** Implement notification webhook or polling

## Next Steps for Production

1. **Implement persistent token storage:**
   - Use Redis (recommended)
   - Or store in backend database via API

2. **Add health check endpoint:**
   - Simple HTTP server on port 8080
   - Returns "OK" for Koyeb monitoring

3. **Implement notification delivery:**
   - Bot polls backend for pending notifications
   - Or backend calls bot webhook to send notifications

4. **Add error monitoring:**
   - Sentry integration
   - Better logging and alerting

5. **Improve user experience:**
   - Better error messages
   - More pagination options
   - Rich formatting with buttons
