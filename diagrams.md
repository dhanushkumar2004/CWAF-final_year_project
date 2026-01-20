# WAF Project: System Design and Logic Documentation

This document details the visual architecture, decision logic, and data flow of the Web Application Firewall.

---

## 1. System Architecture

The architecture separates the high-speed traffic interception ("Hot Path") from the administrative dashboard ("Cold Path"), using shared JSON files as the synchronization layer.

### Architecture Diagram
*Illustrates the physical components and the separation of Client, Host, and Internet zones.*

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
        AdminBrowser("Admin's Browser<br/>(Dashboard: 127.0.0.1:5000)"):::internet
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
    UserBrowser ==>|HTTP Request| ProxyServer
    ProxyServer === SecurityEngine
    SecurityEngine ==>|Allowed| Internet
    Internet ==>|Response| SecurityEngine
    SecurityEngine ==>|Forward Back| UserBrowser
    SecurityEngine --|Blocked 403|--> UserBrowser

    AdminBrowser <-->|API Calls| FlaskBackend

    SecurityEngine -.->|Write Logs| LogFiles
    ConfigFiles -.->|Read Rules| SecurityEngine
    FlaskBackend -.->|Read Logs| LogFiles
    FlaskBackend <-->|Update Config| ConfigFiles



---

## 2. Process Flow (Algorithm)

This flowchart details the step-by-step decision-making process inside the proxy engine for every intercepted request.

### Logic Flowchart
*Illustrates the sequential security checks applied to each request before allowing or blocking it.*

```mermaid
flowchart TD
    Start([User Request])
    Intercept[Intercept via Proxy]
    LoadConfig[Load Config Rules]

    WL{Whitelisted?}
    Rate{Rate Limit Exceeded?}
    Auth{Login Page?}
    Brute{Brute Force Detected?}
    Normalize[Normalize Payload]
    Scan[Scan SQLi & XSS Patterns]
    Score{Threat Score ≥ Threshold?}

    Allow[Allow Request]
    BlockRate[Block: Rate Limit]
    BlockBrute[Block: Brute Force]
    BlockThreat[Block: Malicious Payload]
    Log[Log Event]

    Start --> Intercept --> LoadConfig --> WL
    WL -- Yes --> Allow --> Log
    WL -- No --> Rate

    Rate -- Yes --> BlockRate --> Log
    Rate -- No --> Auth

    Auth -- Yes --> Brute
    Brute -- Yes --> BlockBrute --> Log
    Brute -- No --> Normalize

    Auth -- No --> Normalize
    Normalize --> Scan --> Score

    Score -- Yes --> BlockThreat --> Log
    Score -- No --> Allow --> Log

