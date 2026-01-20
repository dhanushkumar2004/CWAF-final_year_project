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

        subgraph Live_Processing ["Hot Path"]
            ProxyServer["Proxy Server<br/>(mitmdump :8080)"]:::livePath
            SecurityEngine["Security Engine<br/>(proxy.py)"]:::livePath
        end

        subgraph Shared_Data ["Shared Storage"]
            LogFiles[("waf_logs.json")]:::storage
            ConfigFiles[("waf_config.json")]:::storage
        end

        subgraph Management ["Cold Path"]
            FlaskBackend["Dashboard Backend<br/>(Flask API :5000)"]:::adminPath
        end
    end

    Internet((Internet / Target Servers)):::internet

    UserBrowser --> ProxyServer --> SecurityEngine
    SecurityEngine -->|Allowed| Internet
    Internet --> SecurityEngine --> UserBrowser
    SecurityEngine --|Blocked 403|--> UserBrowser

    AdminBrowser <-->|API Calls| FlaskBackend

    SecurityEngine -.->|Write Logs| LogFiles
    ConfigFiles -.->|Read Rules| SecurityEngine
    FlaskBackend -.->|Read Logs| LogFiles
    FlaskBackend <-->|Update Config| ConfigFiles
