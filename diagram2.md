# WAF Project: System Design and Logic Documentation

This document details the visual architecture, decision logic, and data flow of the Web Application Firewall.

---

## 1. System Architecture

The architecture separates the high-speed traffic interception ("Hot Path") from the administrative dashboard ("Cold Path"), using shared JSON files as the synchronization layer.

### Architecture Diagram
*Illustrates the physical components and separation of Client, Host, and Internet zones.*

```mermaid
graph LR
    classDef internet fill:#e1e4e8,stroke:#333,stroke-width:2px;
    classDef livePath fill:#ffcccc,stroke:#d9534f,stroke-width:3px;
    classDef adminPath fill:#cce5ff,stroke:#007bff,stroke-width:2px;
    classDef storage fill:#dba4ea,stroke:#6f42c1,stroke-width:2px;

    subgraph Client_Zone["Client Zone"]
        UserBrowser["User Browser (Proxy :8080)"]:::internet
        AdminBrowser["Admin Browser (Dashboard :5000)"]:::internet
    end

    subgraph Host["WAF Host Machine"]
        subgraph HotPath["Hot Path"]
            Proxy["mitmproxy :8080"]:::livePath
            Engine["Security Engine (proxy.py)"]:::livePath
        end

        subgraph Storage["Shared Storage"]
            Logs["waf_logs.json"]:::storage
            Config["waf_config.json"]:::storage
        end

        subgraph ColdPath["Cold Path"]
            Dashboard["Flask Dashboard :5000"]:::adminPath
        end
    end

    Internet["Target Servers"]:::internet

    UserBrowser --> Proxy --> Engine
    Engine -->|Allowed| Internet
    Internet --> Engine --> UserBrowser
    Engine --|Blocked 403|--> UserBrowser

    Engine -.-> Logs
    Config -.-> Engine
    Dashboard -.-> Logs
    Dashboard <-->|Update| Config
    AdminBrowser <-->|API| Dashboard
```

---

## 2. Process Flow (Algorithm)

This flowchart shows the decision logic applied to every intercepted request.

### Logic Flowchart

```mermaid
flowchart TD
    Start([User Request])
    Intercept[Intercept via Proxy]
    LoadConfig[Load Config]

    WL{Whitelisted?}
    Rate{Rate Limit Exceeded?}
    Auth{Login Page?}
    Brute{Brute Force?}
    Normalize[Normalize Payload]
    Scan[Scan SQLi / XSS]
    Score{Threat Score High?}

    Allow[Allow Request]
    BlockRate[Block: Rate Limit]
    BlockBrute[Block: Brute Force]
    BlockThreat[Block: Attack]
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
```

---

## 3. Data Flow Diagram (DFD – Level 1)

This diagram shows how data moves between users, processes, and storage.

### DFD Level 1

```mermaid
graph LR
    User[User]
    Admin[Administrator]
    Server[Web Server]

    P1[Traffic Interception]
    P2[Threat Analysis]
    P3[Action Handler]
    P4[Dashboard Reporting]

    Logs[(Logs)]
    Config[(Config)]

    User -->|Request| P1
    P1 --> P2
    Config -.-> P2
    P2 --> P3

    P3 -->|Allowed| Server
    Server -->|Response| P3
    P3 -->|Response / 403| User

    P3 --> Logs
    Logs -.-> P4

    Admin --> P4
    P4 --> Config
    P4 --> Admin
```
