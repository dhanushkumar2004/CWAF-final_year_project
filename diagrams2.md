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
