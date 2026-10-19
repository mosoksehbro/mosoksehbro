<div align="center">
  <img src="./terminal_header.svg" alt="Terminal Window" width="700" />

  <p align="center">
    <a href="https://gosade.my.id"><img src="https://img.shields.io/badge/Web-gosade.my.id-1a1b27?style=flat-square&logo=google-chrome&logoColor=7aa2f7" alt="Website" /></a>
    <a href="https://x.com/Deeminorr"><img src="https://img.shields.io/badge/Twitter-@Deeminorr-1a1b27?style=flat-square&logo=x&logoColor=7aa2f7" alt="Twitter" /></a>
    <img src="https://img.shields.io/badge/Base-Indonesia_(GMT%2B7)-1a1b27?style=flat-square&logo=google-maps&logoColor=7dcfff" alt="Base" />
    <img src="https://komarev.com/ghpvc/?username=mosoksehbro&color=7aa2f7&style=flat-square&label=views" alt="views" />
  </p>
</div>

<br />

### Stack & Tooling

```bash
Backend      : Go, C#, PHP / Laravel, Node.js, Python
Frontend     : TypeScript, React, Next.js, React Native
Data & Infra : PostgreSQL, MySQL, Redis, Docker, Git, Linux
Core Focus   : Clean Architecture, High-throughput ETL, REST/gRPC APIs, Vision Models
```

<br />

### Architecture & Engineering Blueprint

```text
  [ Clients / Endpoints ]
             │
             ▼
  ┌──────────────────────────────────────────────┐
  │         API Gateway & Reverse Proxy          │  ──▶ TLS Termination / Rate Limiting
  └──────────────────────┬───────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         ▼                               ▼
  ┌──────────────┐                ┌──────────────┐
  │  Core API    │ (Sync/REST)    │ Worker Pool  │ (Async Batch / ETL)
  │  Go / C#     │                │ Python / PHP │
  └──────┬───────┘                └──────┬───────┘
         │                               │
         ├───────────────┬───────────────┤
         ▼               ▼               ▼
  ┌──────────────┐┌──────────────┐┌──────────────┐
  │ PostgreSQL   ││ Redis Cache  ││ Message Bus  │
  │ Primary DB   ││ Key-Value    ││ Event Stream │
  └──────────────┘└──────────────┘└──────────────┘
```

<br />

### Engineering Principles & Focus

```text
• Architecture : Clean Architecture, Domain-Driven Design (DDD), Modular Services
• Reliability  : Idempotency, Graceful Degradation, Structured Telemetry & Logging
• Performance  : Query & Index Tuning, Connection Pooling, Cache Invalidation Strategies
• Current Work : High-throughput concurrent pipelines in Go & Edge CV inference
```

<br />

### Performance & Activity

<div align="center">
  <img src="./profile_card.svg" alt="GitHub Profile Summary" width="700" />
  
  <br /><br />

  <table border="0" cellspacing="0" cellpadding="0">
    <tr align="center">
      <td valign="top">
        <img src="./streak.svg" alt="Streak Stats" width="370" />
      </td>
      <td valign="top">
        <img src="./languages.svg" alt="Top Languages" width="340" />
      </td>
    </tr>
  </table>

  <br />

  <img src="./productivity.svg" alt="Weekly Activity Cadence" width="700" />
</div>

<br />

### Collaboration & Security Footprint

```yaml
Availability   : Open for High-Impact Backend Architecture, Distributed Systems & Consulting
Timezone       : Asia/Jakarta (WIB • GMT+7)
Direct Reach   : martinusade333@gmail.com • https://gosade.my.id
SSH PubKey     : SHA256:gE4b8eTfTKH74dIKeC7xieezZvKQ3JvbhO49OoaMnkk (RSA 4096)
Code Integrity : Signed commits & verified git workflows
```
