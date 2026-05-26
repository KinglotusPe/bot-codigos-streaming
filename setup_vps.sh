#!/bin/bash

# Colors
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Bot Setup...${NC}"

# 1. Update and Install Dependencies
echo -e "${GREEN}📦 Installing system dependencies...${NC}"
sudo apt update
sudo apt install -y python3-pip python3-venv unzip

# 2. Setup Python Virtual Environment
echo -e "${GREEN}🐍 Setting up Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# 3. Install Python Requirements
echo -e "${GREEN}📥 Installing Python libraries...${NC}"
pip install -r requirements.txt

# 4. Create Systemd Service (Auto-start)
SERVICE_FILE=/etc/systemd/system/telegram_bot.service
CURRENT_DIR=$(pwd)
USER_NAME=$(whoami)

echo -e "${GREEN}⚙️ Creating systemd service at $SERVICE_FILE...${NC}"

# Create service file content
sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=Telegram Streaming Bot
After=network.target

[Service]
User=$USER_NAME
WorkingDirectory=$CURRENT_DIR
ExecStart=$CURRENT_DIR/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL

# 5. Enable and Start Service
echo -e "${GREEN}🔌 Enabling and starting bot service...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable telegram_bot
sudo systemctl restart telegram_bot

echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "Check status with: ${GREEN}sudo systemctl status telegram_bot${NC}"
echo -e "View logs with: ${GREEN}sudo journalctl -u telegram_bot -f${NC}"
