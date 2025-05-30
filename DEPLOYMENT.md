# Deployment Guide

## Quick Start

1. **Clone and Setup**:
   ```bash
   git clone https://github.com/Shahrukhahamed/py_tbot.git
   cd py_tbot
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Test Build**:
   ```bash
   python final_test.py
   ```

4. **Run Bot**:
   ```bash
   python main.py
   ```

## Required Credentials

### Telegram Bot Token
1. Message @BotFather on Telegram
2. Create a new bot with `/newbot`
3. Copy the token to `TELEGRAM_BOT_TOKEN` in `.env`

### Supabase Setup
1. Create account at https://supabase.com
2. Create a new project
3. Go to Settings > API
4. Copy URL and anon key to `.env`

### Database Schema
The bot will automatically create required tables:
- `wallets` - Tracked wallet addresses
- `transactions` - Transaction records  
- `settings` - Bot configuration
- `users` - User management

## Production Deployment

### Using Docker
```bash
# Build image
docker build -t py_tbot .

# Run with environment file
docker run -d --env-file .env py_tbot
```

### Using systemd (Linux)
```bash
# Create service file
sudo nano /etc/systemd/system/py_tbot.service

[Unit]
Description=Blockchain Transaction Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/py_tbot
ExecStart=/usr/bin/python3 main.py
Restart=always
EnvironmentFile=/path/to/py_tbot/.env

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable py_tbot
sudo systemctl start py_tbot
```

### Using PM2 (Node.js Process Manager)
```bash
# Install PM2
npm install -g pm2

# Start bot
pm2 start main.py --name py_tbot --interpreter python3

# Save PM2 configuration
pm2 save
pm2 startup
```

## Monitoring

### Logs
- Console output: Real-time status
- File logs: `bot.log` (rotated automatically)

### Health Check
```bash
# Test all components
python final_test.py

# Check specific component
python -c "from src.utils.logger import logger; logger.log('Health check')"
```

## Scaling

### Redis Setup (Optional)
```bash
# Install Redis
sudo apt install redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:alpine

# Update .env
REDIS_URL=redis://localhost:6379
```

### Multiple Instances
- Use different Telegram bot tokens
- Share same database/Redis instance
- Load balance with nginx if needed

## Troubleshooting

### Common Issues

1. **Import Errors**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Database Connection**:
   - Check Supabase credentials
   - Verify network connectivity
   - Check API key permissions

3. **RPC Connection Errors**:
   - Update RPC URLs in `config/blockchains.json`
   - Get API keys for services like Infura
   - Use public RPC endpoints as fallback

4. **Memory Issues**:
   - Enable Redis for caching
   - Reduce tracking frequency
   - Limit number of tracked addresses

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main.py
```

## Security

### Best Practices
- Keep `.env` file secure and never commit it
- Use environment variables in production
- Regularly rotate API keys
- Monitor bot activity logs
- Set up admin user restrictions

### Firewall Rules
```bash
# Allow only necessary ports
sudo ufw allow 22    # SSH
sudo ufw allow 443   # HTTPS
sudo ufw deny 6379   # Redis (if external access not needed)
```

## Maintenance

### Updates
```bash
git pull origin main
pip install -r requirements.txt
python final_test.py
# Restart bot
```

### Backup
- Database: Use Supabase backup features
- Configuration: Backup `.env` and `config/` directory
- Logs: Archive `bot.log` files regularly

### Performance Monitoring
- Monitor memory usage
- Check response times
- Track error rates in logs
- Monitor blockchain RPC usage