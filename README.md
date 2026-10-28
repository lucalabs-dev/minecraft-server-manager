# MINECRAFT-SERVER-MANAGER

## DESCRIPTION
This web application is a Docker-based system for creating and managing Minecraft servers



## Features

- Create Minecraft servers using PaperMC
- Automatically download the required server JAR
- Select a Minecraft version
- Automatically initialize server files
- Manage multiple Minecraft servers
- Start, stop, and restart servers through the web interface
- View server status (online/offline)
- View server logs in real time using Server-Sent Events (SSE)
- Delete servers and their associated files
- Validate server names to prevent invalid input
- Dynamically load the server list from stored data
- Dynamically load available Minecraft versions from the PaperMC API
- Store server information in a JSON file
- Run Minecraft servers inside a Docker container
- Run Minecraft servers as a non-root user



## Technologies

- Python
- FastAPI
- HTML, CSS, and JavaScript
- Docker
- Nginx
- JSON for storing server data
- Server-Sent Events (SSE) for real-time server log streaming
- PaperMC API for retrieving available Minecraft versions



## How to Start

### Prerequisites
- Docker must be installed on your system.

### Starting the Application
1. Open a terminal in the project's root directory.
2. Run the following command to build and start the Docker containers:

   docker compose up --build

3. Once the containers are running, open the following URL in your browser:

   http://localhost:8080



## Project Structure

Minecraft-Server-Manager/
├── backend/
│   └── api/            # FastAPI backend
│       └── Dockerfile  # Backend container configuration 
├── data/
│   ├── servers/        # Minecraft server files
│   └── servers.json    # Registered server information
├── docker/             # Docker-related files
├── frontend/
│   └── html/           # HTML, CSS and JavaScript
├── nginx/
│   └── nginx.conf      # Nginx configuration
├── docker-compose.yml
└── README.md