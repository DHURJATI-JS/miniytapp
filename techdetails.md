🛠️ Advanced System Architecture & Logic

This document outlines the specialized backend logic, security protocols, and automated maintenance tasks of the YT Mini ecosystem.
🔒 Security & Identity Management
    Cryptographic Hashing: User security is maintained using Werzueg hashing, ensuring that even in the event of a database compromise, raw credentials remain inaccessible.
    Admin Command Center: A restricted dashboard allowing for real-time monitoring of system health, hardware utility, and manual content moderation.
    Token Sanitation: Automated scheduler tasks identify and purge expired Password Reset and Session tokens every 24 hours to prevent "ghost" authentication entries.
🛡️ "Instant-Kill" IP Blacklisting

The system employs a high-speed defensive layer against malicious actors:
    Log-Based Identification: Suspicious activity (Rate-limit tripping, 404-probing) is captured in the system logs.
    Blacklist Protocol: The administrator can append a malicious IP to a flat blacklist.txt file.
    Zero-Latency Drop: The middleware checks every incoming request against this file's hash set. If a match is found, the connection is dropped instantly before it even hits the SQLAlchemy layer, saving CPU cycles.
🚀 Caching & Resource Optimization

To prevent redundant AI inference costs (Whisper/Ollama), the system uses a Lazy-Loading Cache Strategy:
    The Content Hash: Every processed video generates a unique hash based on its metadata. If a user requests a video that has been summarized before, the system serves the cached JSON summary from PostgreSQL/Redis instead of re-running the AI pipeline.
    Automated Cache Invalidation: Upon updating or deleting the video the cached is cleared instantly. In case of a peamnent user delete and channel delete it takes a time of 1 day to clear the cache.
    Cold Storage: Cached video data is refreshed or verified every 1 day to ensure visual/textual alignment.

⚡ Background Workers & Schedulers

The system handles "janitorial" tasks automatically to maintain Arch Linux system health:
    CleanFiles Task: A periodic cron-style function that scans the temp/ and uploads/ directories for orphaned .mp4 or .wav fragments left behind by interrupted uploads or update processes.
    Task Resets: Background workers (Scheduler) reset stalled tasks every 60s to prevent queue clogging.
📈 View Count & Engagement Logic
    Unique View Verification: To prevent view-count inflation, the system User-ID pairs. A view is only incremented once every 24 hours per unique user.
    Multi-Channel Architecture: Users can instantiate multiple "Channel" identities, each with separate SQLAlchemy-joined queries for custom algorithmic sorting (Trending vs. Chronological).
⚙️ Hardware-Adaptive Settings

A unique feature of this system is its Elastic Resource Allocation:
    Processing Power Adjustment: Users/Admins can toggle the "Inference Weight" in settings.
        Low Power: Reduces frame capture to 3 frames/vid.
        Extreme Power: RTX 3060 full-throttle (7+ frames, Whisper V3 Large).
    Joined Load Queries: We use joinedload() in SQLAlchemy to minimize "N+1" query problems, ensuring that loading a playlist with 50 videos only takes a single optimized SQL trip.
