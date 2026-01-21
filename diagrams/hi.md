flowchart LR
    %% Main Nodes
    Start([User Request])
    Intercept[Intercept via Proxy]
    LoadConfig[Load Config]

    %% Decisions - Quotes added for safety
    WL{"Whitelisted?"}
    Rate{"Rate Limit Exceeded?"}
    Auth{"Login Page?"}
    Brute{"Brute Force?"}
    Score{"Threat Score High?"}

    %% Processes
    Normalize[Normalize Payload]
    Scan[Scan SQLi and XSS]

    %% Terminals
    Allow[Allow Request]
    BlockRate[Block: Rate Limit]
    BlockBrute[Block: Brute Force]
    BlockThreat[Block: Attack]
    Log[Log Event]

    %% Connections
    Start --> Intercept --> LoadConfig --> WL
    
    %% Whitelist Path
    WL -- Yes --> Allow --> Log
    WL -- No --> Rate

    %% Rate Limit Path
    Rate -- Yes --> BlockRate --> Log
    Rate -- No --> Auth

    %% Auth and Brute Force Path
    Auth -- Yes --> Brute
    Brute -- Yes --> BlockBrute --> Log
    Brute -- No --> Normalize

    %% Inspection Path
    Auth -- No --> Normalize
    Normalize --> Scan --> Score

    %% Final Decision Path
    Score -- Yes --> BlockThreat --> Log
    Score -- No --> Allow
