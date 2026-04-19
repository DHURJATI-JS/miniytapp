🚀 YT Mini: AI Multimodal Video Intelligence System

YT Mini is a high-integrity, multimodal AI application designed for automated video summarization and architectural durability. Built on a production-mirror environment of Arch Linux, it leverages state-of-the-art LLMs and neural captioning to transform video content into structured intelligence.
⚠️ Mandatory Permission & Contact Protocol

CRITICAL: This software is NOT open-source for unauthorized commercial or private redistribution.
    Authorization Required: You MUST contact the author and receive explicit written consent before cloning, deploying, or utilizing this codebase in any production or public environment.
    Contact: Please reach out to the developer to discuss licensing or access.
        Developer Email: dhurjatisharma2010@gmail.com (Referenced in system integrity report and system variable {{g.myemail}})
        Subject Line: Security Inquiry: Studio v2 Access Request

🧠 AI Multimodal Pipeline

The system utilizes a multi-stage inference engine to "see" and "hear" video content:
 YT Mini: AI Multimodal Video Intelligence System

YT Mini is a high-integrity, multimodal AI application designed for automated video summarization and architectural durability. Built on a production-mirror environment of Arch Linux, it leverages state-of-the-art LLMs and neural captioning to transform video content into structured intelligence.


🧠 AI Multimodal Pipeline

The system utilizes a multi-stage inference engine to "see" and "hear" video content:
    The process queue is handled by Flask executor and each user is alloted a 60second timeout window 
    Visual Extraction: Custom logic captures 07 key frames per video to provide visual context.
    Multimodal LLM: Ollama (Micicpm-v) processes Base64 encoded frames for secure image-to-text transmission.
    Neural Audio: Whisper V3 Turbo provides lightning-fast caption extraction for deep textual understanding.
    Real-time Updates: SocketIO streams the AI's "thought process" and progress directly to the client UI.
📊 Performance Benchmarks (Locust Verified)

The architecture has been stress-tested to hardware saturation to ensure stability under extreme load.
Metric	Result
Total Requests (10 min window)	354,496
Burst Peak Throughput	688.08 req/s
Sustained Equilibrium	504.05 req/s
Failure Rate (Under 700 req/s)	0.00%
Hardware Bottleneck Analysis

During Phase 2 (Extreme Saturation) at 783.90 req/s, a 19.81% failure rate was recorded. Analysis confirms this was a hardware utility limit:
    VRAM: Analysis of 7 frames per video exhausted the 12GB VRAM buffer.
    GIL Limits: Python’s Global Interpreter Lock reached context-switching limits.
    I/O Wait: Hit the physical caps of the SATA SSD and PostgreSQL socket availability.
🛡️ Security & Infrastructure
    Data Integrity: SQLAlchemy ORM with parameterized queries to prevent SQL Injection.
    Defensive Layer: * IP-based Rate Limiting (50 req/min).
        CSRF Integrity tokens for all state-changing actions.
        flask-talisman with moderate to strict Content Security Policy.
        Global context-aware XSS Auto-escaping.
    Production Stack: * Server: Nginx (Reverse Proxy) + Gunicorn (Eventlet Workers).
        Database: PostgreSQL 16.
        Real-time: Flask-SocketIO.
    
💻 Mirror Production Environment

    OS: Arch Linux

    CPU: Intel i5-12400F 

    RAM: 32GB DDR4

    GPU: NVIDIA RTX 3060 (12GB VRAM)

    Storage: 1TB SATA SSD

🛠️ Usage (Authorized Users Only)

After receiving permission, the stack can be launched via the production protocol:

    Start the Infrastructure:
    Bash
    sudo systemctl start nginx
    sudo systemctl start postgresql

    Launch the Stack:
    Bash
    ./system/bin/python -m gunicorn -k eventlet -w 1 --bind 127.0.0.1:5000 app:system

Copyright © 2026 Dhurjati Sharma. All Rights Reserved.
Notice: Licensing & Collaboration
This project is currently proprietary. If you'd like to clone, deploy, or use this codebase for your own work, please reach out for permission first. I’m happy to discuss access or licensing!
Contact:
    Developer: Dhurjati Sharma
    Email: dhurjatisharma2010@gmail.com
    
👉 [View Technical Architecture & Security Protocols](./techdetails.md)
