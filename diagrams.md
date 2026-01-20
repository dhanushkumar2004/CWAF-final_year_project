# WAF Project: System Design and Logic Documentation

## 1. System Architecture

The system architecture is designed around a "Separation of Concerns" principle. It divides the system into two distinct operational paths: the **Live Traffic Path** (high-speed security filtering) and the **Management Path** (monitoring and configuration). These two paths are bridged by a shared file-based storage system.

### Architecture Diagram

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#eee', 'edgeLabelBackground':'#ffffff', 'tertiaryColor': '#f4f4f4'}}}%%
graph LR
    %% --- STYLING DEFINITIONS ---
    classDef internet fill:#e1e4e8,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5;
    classDef livePath fill:#ffcccc,stroke:#d9534f,stroke-width:3px,color:black;
    classDef adminPath fill:#cce5ff,stroke:#007bff,stroke-width:2px,color:black;
    classDef storage fill:#dba4ea,stroke:#6f42c1,stroke-width:2px,shape:cylinder,color:black;

    %% --- LEFT SIDE: CLIENTS ---
    subgraph Client_Zone ["Client Zone"]
        style Client_Zone fill:#f9f9f9,stroke:none
        UserBrowser("User's Browser<br/>(Proxy: 127.0.0.1:8080)"):::internet
        AdminBrowser("Admin's Browser<br/>([http://127.0.0.1:5000](http://127.0.0.1:5000))"):::internet
    end

    %% --- MIDDLE ZONE: THE HOST MACHINE ---
    subgraph Host_Machine ["WAF HOST MACHINE (Localhost)"]
        style Host_Machine fill:#ffffff,stroke:#666,stroke-width:3px

        %% TOP SWIMLANE: Live Traffic Processing
        subgraph Live_Processing ["1. Live Traffic Processing Path (Hot Path)"]
            style Live_Processing fill:#fff5f5,stroke:#d9534f
            ProxyServer["Proxy Server<br/>(mitmdump :8080)"]:::livePath
            SecurityEngine["Security Engine<br/>(proxy.py Logic)"]:::livePath
        end

        %% MIDDLE: Shared Data
        subgraph Shared_Data ["Shared Storage (Glue)"]
            style Shared_Data fill:#f4f0f7,stroke:#6f42c1,stroke-width:1px
            LogFiles[("waf_logs.json<br/>(Events)")]:::storage
            ConfigFiles[("waf_config.json<br/>(Rules)")]:::storage
        end

        %% BOTTOM SWIMLANE: Management
        subgraph Management ["2. Management & Monitoring Path (Cold Path)"]
            style Management fill:#f0f7ff,stroke:#007bff
            FlaskBackend["Dashboard Backend<br/>(Flask API :5000)"]:::adminPath
        end
    end

    %% --- RIGHT SIDE: THE INTERNET ---
    Internet((Internet /<br/>Target Servers)):::internet


    %% === DEFINING THE FLOWS ===

    %% FLOW 1: The Live Traffic Path (Thick Red Arrows)
    UserBrowser ==>|1. HTTP Request| ProxyServer
    ProxyServer === SecurityEngine
    SecurityEngine ==>|2a. Allowed Request| Internet
    Internet ==>|2b. Response| SecurityEngine
    SecurityEngine ==>|4. Forward Back| UserBrowser
    SecurityEngine --|3. BLOCKED 403|--> UserBrowser

    %% FLOW 2: The Admin Path (Blue Arrows)
    AdminBrowser <-->|API Calls & UI Data| FlaskBackend

    %% FLOW 3: Internal Data Connections (Standard Dotted Arrows)
    SecurityEngine -.->|Write Logs| LogFiles
    ConfigFiles -.->|Read Rules Fast| SecurityEngine

    FlaskBackend -.->|Read/Paginate| LogFiles
    FlaskBackend <-->|Read/Update Config| ConfigFiles

    %% Logical link within proxy
    ProxyServer --- SecurityEngine


    %%{init: {'theme': 'base', 'themeVariables': { 'lineColor': '#333', 'secondaryColor': '#f4f4f4', 'tertiaryColor': '#fff'}}}%%
flowchart TD
    %% Node Styles
    classDef startend fill:#2d3e50,stroke:#333,stroke-width:2px,color:white,shape:stadium;
    classDef process fill:#e1f5fe,stroke:#0277bd,stroke-width:2px;
    classDef decision fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,shape:rhombus;
    classDef block fill:#ffcdd2,stroke:#c62828,stroke-width:2px,color:#c62828;
    classDef allow fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px,color:#2e7d32;

    %% Main Flow
    Start([User Request]) :::startend --> Intercept[Intercept (Port 8080)] :::process
    Intercept --> Config[Load Config Rules] :::process
    
    %% Fast Checks
    Config --> CheckWL{Whitelisted?} :::decision
    CheckWL -- Yes --> Forward[Forward to Server] :::allow
    CheckWL -- No --> CheckRate{Rate Limit<br/>Exceeded?} :::decision
    
    %% Rate Limit Branch
    CheckRate -- Yes --> BlockRate[BLOCK: Rate Limit] :::block
    CheckRate -- No --> CheckAuth{Is Login Page?} :::decision
    
    %% Brute Force Branch
    CheckAuth -- Yes --> CheckBrute{Brute Force?} :::decision
    CheckAuth -- No --> Normalize[Normalize Payload] :::process
    CheckBrute -- Yes --> BlockBrute[BLOCK: Brute Force] :::block
    CheckBrute -- No --> Normalize
    
    %% Deep Scan
    Normalize --> Scan[Scan: SQLi & XSS Patterns] :::process
    Scan --> Score{Threat Score >= 5?} :::decision
    
    %% Final Action
    Score -- Yes --> BlockThreat[BLOCK: 403 Forbidden] :::block
    Score -- No --> Forward
    
    %% Logging (Connected to outcomes)
    BlockRate --> Log[Log Event] :::process
    BlockBrute --> Log
    BlockThreat --> Log
    Forward --> Log
    Log --> End([End]) :::startend


    graph LR
    %% Styles
    classDef entity fill:#e1e4e8,stroke:#333,stroke-width:2px;
    classDef process fill:#e1f5fe,stroke:#0277bd,stroke-width:2px,shape:rounded;
    classDef store fill:#ffe0b2,stroke:#ef6c00,stroke-width:2px,shape:cylinder;

    %% Entities
    User[User / Client]:::entity
    Admin[Administrator]:::entity
    WebServer[Target Web Server]:::entity

    %% Processes
    P1(1.0 Traffic Interception):::process
    P2(2.0 Threat Analysis):::process
    P3(3.0 Action Handler):::process
    P4(4.0 Dashboard Reporting):::process

    %% Data Stores
    D1[(Logs DB)]:::store
    D2[(Config Rules)]:::store

    %% Flows
    User -->|HTTP Request| P1
    P1 -->|Raw Data| P2
    
    D2 -.->|Read Rules| P2
    P2 -->|Threat Score| P3
    
    P3 -->|Allowed Request| WebServer
    WebServer -->|Response| P3
    P3 -->|Response / 403 Error| User
    
    P3 -->|Event Details| D1
    
    Admin -->|Update Config| P4
    P4 -->|Write Rules| D2
    D1 -.->|Read Stats| P4
    P4 -->|Visual Analytics| Admin
