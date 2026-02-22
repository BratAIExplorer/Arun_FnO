# VPS Deployment Guide — F&O Sentinel

> **Goal**: Deploy the web platform on `76.13.179.32` on port **8080** as a standalone project.

---

## 1. Prerequisites on VPS
Ensure the VPS has **Docker** and **Docker Compose** installed.
If not installed, run:
```bash
sudo apt-get update
sudo apt-get install docker.io docker-compose -y
sudo systemctl start docker
sudo systemctl enable docker
```

## 2. Clone and Setup
SSH into your VPS and run:
```bash
# Clone the NEW repository
git clone https://github.com/BratAIExplorer/Arun_FnO.git
cd Arun_FnO

# Create environment file
cp web/.env.example web/.env
```

## 3. Configure `.env`
Edit the `web/.env` file:
```bash
nano web/.env
```
Set a unique `SECRET_KEY` (any random string of 32+ characters). This is used for JWT tokens and credential encryption.

## 4. Run the Platform
Run the production compose file:
```bash
docker-compose -f docker-compose.web.prod.yml up -d --build
```

## 5. Access
The platform is now running on port **8080**.
Open your browser and go to:
**http://76.13.179.32:8080**

---

## 🏗️ Technical Details (Isolation)
- **Port 8080**: This project uses port 8080 specifically to avoid conflict with other web apps running on port 80 or 443.
- **Docker Network**: The containers run in an isolated bridge network.
- **Data Persistence**: A named volume `fno_sentinel_data` is created to keep your database safe even if containers are deleted.

## 🛠️ Maintenance Commands
- **Stop**: `docker-compose -f docker-compose.web.prod.yml stop`
- **View Logs**: `docker-compose -f docker-compose.web.prod.yml logs -f`
- **Update Code**: 
  ```bash
  git pull web main
  docker-compose -f docker-compose.web.prod.yml up -d --build
  ```
