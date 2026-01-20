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
