graph LR
    %% --- STYLING ---
    classDef actorStyle fill:#fff,stroke:#333,stroke-width:0px,font-size:14px;
    classDef usecaseStyle fill:#fff,stroke:#333,stroke-width:2px,rx:20,ry:20;

    %% --- ACTORS ---
    Admin[👤 Administrator]:::actorStyle
    WebUser[👤 Web User]:::actorStyle
    TargetServer[🖥️ Target Server]:::actorStyle

    %% --- SYSTEM BOUNDARY ---
    subgraph System_Boundary ["WAF Security System"]
        direction TB
        %% Dashboard Use Cases
        UC1([View Real-time Stats]):::usecaseStyle
        UC2([Configure Rules]):::usecaseStyle
        UC3([Monitor Threat Logs]):::usecaseStyle
        UC4([Export Logs CSV/JSON]):::usecaseStyle

        %% Core WAF Use Cases
        UC5([Intercept HTTP Traffic]):::usecaseStyle
        UC6([Analyze Payload]):::usecaseStyle
        UC7([Block Malicious Request]):::usecaseStyle
        UC8([Forward Safe Request]):::usecaseStyle
        UC9([Log Security Event]):::usecaseStyle
    end

    %% --- RELATIONSHIPS ---
    %% Admin Actions
    Admin --- UC1
    Admin --- UC2
    Admin --- UC3
    Admin --- UC4

    %% User Actions
    WebUser --> UC5

    %% Internal Logic
    UC5 -.->|include| UC6
    UC6 -.->|include| UC9

    UC6 -.->|extend: Score > 5| UC7
    UC6 -.->|extend: Score < 5| UC8

    %% System Output
    UC8 --> TargetServer
