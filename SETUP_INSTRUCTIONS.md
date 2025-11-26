# Open WebUI Sebastian - Setup Instructions

## ✅ Container Status

- **Container Name:** `open-webui-sebastian`
- **Port:** `8084` (mapped to internal 8080)
- **Network:** Connected to both `ai-stack-network` and default bridge
- **Access URL:** `http://<your-server-ip>:8084`

## 🔗 Network Connectivity

The container can reach:
- ✅ **Ollama:** `http://ollama:11434` (on ai-stack-network)
- ✅ **Backend API:** `http://langgraph-agents:8000` (on ai-stack-network)

---

## 📝 Setup Steps

### Step 1: Access Open WebUI

1. Open your browser and go to: `http://<your-server-ip>:8084`
2. Create an admin account (first user becomes admin)
3. Log in

### Step 2: Install the Sebastian Pipe Function

1. Click on your profile (top right)
2. Navigate to **Admin Panel** → **Functions**
3. Click the **"+"** button to create a new function
4. Copy the entire contents of `/mnt/user/appdata/open-webui-sebastian/sebastian_streaming_pipe.py`
5. Paste it into the function editor
6. Click **Save**

### Step 3: Configure the Pipe Function

1. Find the "Sebastian" function in the list
2. Click the **⚙️ Settings** icon
3. Configure the following **Valves**:

   ```
   BACKEND_URL: http://langgraph-agents:8000
   API_KEY: e74742e8b2f5fd66401636ef79b01124b193ed94f7baa249c4899dc5fea9164c
   USER_ID: 00000000-0000-0000-0000-000000000001
   MODEL_NAME: sebastian
   REQUEST_TIMEOUT: 120
   DEBUG_MODE: true
   ```

   **Important:** Use `http://langgraph-agents:8000` NOT `host.docker.internal` because they're on the same Docker network!

4. Click **Save**

### Step 4: Enable the Function

1. Toggle the switch to **enable** the Sebastian function
2. Refresh the page

### Step 5: Test It!

1. Click **"New Chat"**
2. In the model dropdown (top of chat), select **"Sebastian"**
3. Send a test message: `"Hello, what is 2+2?"`
4. You should see the response stream in real-time, word by word! 🎉

---

## 🐛 Troubleshooting

### If you get "Connection Error"

**Check the BACKEND_URL valve:**
```bash
# Inside the container, test connectivity:
docker exec open-webui-sebastian curl http://langgraph-agents:8000/health
```

Should return: `{"status":"healthy",...}`

### If streaming doesn't work

1. Check DEBUG_MODE is set to `true` in valves
2. Open browser console (F12) and check for errors
3. Check container logs:
   ```bash
   docker logs open-webui-sebastian -f
   ```

### If you get "Invalid API Key"

Make sure the API_KEY valve matches the one in `/mnt/user/appdata/ai_stack/.env`:
```bash
grep API_KEY /mnt/user/appdata/ai_stack/.env
```

---

## 🔄 Container Management

**Start:**
```bash
cd /mnt/user/appdata/open-webui-sebastian
docker-compose up -d
```

**Stop:**
```bash
docker-compose down
```

**Restart:**
```bash
docker-compose restart
```

**View Logs:**
```bash
docker logs open-webui-sebastian -f
```

---

## 🌐 Accessing from Different Devices

- **Local server:** `http://localhost:8084`
- **Local network:** `http://192.168.0.12:8084` (replace with your server IP)
- **Tailscale:** `http://100.69.74.56:8084` (if you have Tailscale configured)

---

## 📊 What's Next?

Once Sebastian is working, you'll have:
- ✅ Real-time streaming chat with your LangGraph agents
- ✅ Conversation continuity (chat history maintained)
- ✅ Automatic routing to specialized agents (Task, Event, Food, etc.)
- ✅ Beautiful Open WebUI interface

Ready for **Phase 2**? We can now add:
- 📅 Calendar page
- ✅ Tasks page
- 📆 Events page
- ⏰ Reminders page

All integrated with your backend and styled to match Open WebUI!

---

**Created:** November 25, 2025
**Project:** AI Stack - Custom Agent Interface
**Phase:** 1 Complete ✅
