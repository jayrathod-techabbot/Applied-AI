# Module 10: AI Governance & Compliance — Diagrams

## Table of Contents
1. [AI Governance Framework](#1-ai-governance-framework)
2. [Guardrail Pipeline Architecture](#2-guardrail-pipeline-architecture)
3. [EU AI Act Risk Classification Flow](#3-eu-ai-act-risk-classification-flow)
4. [Responsible AI Lifecycle](#4-responsible-ai-lifecycle)
5. [GDPR Compliance Data Flow](#5-gdpr-compliance-data-flow)

---

## 1. AI Governance Framework

### ASCII Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AI GOVERNANCE FRAMEWORK                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  │
│  │   POLICIES  │  │  STANDARDS  │  │  PROCESSES  │  │   METRICS    │  │
│  ├─────────────┤  ├─────────────┤  ├─────────────┤  ├──────────────┤  │
│  │ Ethics      │  │ Model Cards │  │ Use Case    │  │ Fairness     │  │
│  │ Privacy     │  │ Testing     │  │   Approval  │  │ Drift Rate   │  │
│  │ Security    │  │ Documentation│ │ Deployment  │  │ Incident     │  │
│  │ Data Gov    │  │ Bias Audit  │  │ Monitoring  │  │   Count      │  │
│  │ Risk Mgmt   │  │ Explain-    │  │ Incident    │  │ Compliance   │  │
│  │             │  │   ability   │  │   Response  │  │   Score      │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘  │
│         │                │                │                 │          │
│         └────────────────┼────────────────┼─────────────────┘          │
│                          │                │                            │
│                   ┌──────▼────────────────▼──────┐                     │
│                   │     GOVERNANCE BOARD          │                     │
│                   ├───────────────────────────────┤                     │
│                   │  Chief AI Officer (Chair)     │                     │
│                   │  Data Science Lead            │                     │
│                   │  CISO                         │                     │
│                   │  DPO / Privacy Officer        │                     │
│                   │  Legal Counsel                │                     │
│                   │  Ethics Advisor               │                     │
│                   │  Business Unit Reps           │                     │
│                   └──────────────┬────────────────┘                     │
│                                  │                                      │
│              ┌───────────────────┼───────────────────┐                  │
│              │                   │                   │                  │
│       ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐           │
│       │   RISK      │    │  COMPLIANCE │    │   AUDIT     │           │
│       │ MANAGEMENT  │    │   TEAM      │    │   TEAM      │           │
│       ├─────────────┤    ├─────────────┤    ├─────────────┤           │
│       │ Assess      │    │ GDPR/HIPAA  │    │ Bias Audits │           │
│       │ Mitigate    │    │ EU AI Act   │    │ Performance │           │
│       │ Monitor     │    │ SOC 2       │    │ Fairness    │           │
│       │ Report      │    │ Industry    │    │ Explain-    │           │
│       │             │    │   specific  │    │   ability   │           │
│       └─────────────┘    └─────────────┘    └─────────────┘           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Mermaid Diagram

```mermaid
graph TB
    subgraph Framework["AI Governance Framework"]
        P["Policies<br/>Ethics, Privacy, Security,<br/>Data Gov, Risk Mgmt"]
        S["Standards<br/>Model Cards, Testing,<br/>Documentation, Bias Audit"]
        PR["Processes<br/>Use Case Approval,<br/>Deployment, Monitoring"]
        M["Metrics<br/>Fairness, Drift Rate,<br/>Incident Count, Compliance"]
    end

    subgraph Board["Governance Board"]
        CAO["Chief AI Officer"]
        DSL["Data Science Lead"]
        CISO["CISO"]
        DPO["DPO"]
        LEGAL["Legal Counsel"]
        ETHICS["Ethics Advisor"]
    end

    subgraph Teams["Operational Teams"]
        RM["Risk Management"]
        COMP["Compliance Team"]
        AUDIT["Audit Team"]
    end

    P --> Board
    S --> Board
    PR --> Board
    M --> Board

    Board --> RM
    Board --> COMP
    Board --> AUDIT

    RM -->|"Assess, Mitigate,<br/>Monitor"| OUTPUT["AI Systems"]
    COMP -->|"GDPR, HIPAA,<br/>EU AI Act"| OUTPUT
    AUDIT -->|"Bias, Fairness,<br/>Performance"| OUTPUT

    style Framework fill:#1a1a2e,stroke:#e94560,color:#fff
    style Board fill:#16213e,stroke:#0f3460,color:#fff
    style Teams fill:#0f3460,stroke:#533483,color:#fff
    style OUTPUT fill:#e94560,stroke:#fff,color:#fff
```

---

## 2. Guardrail Pipeline Architecture

### ASCII Diagram

```
                    USER REQUEST
                         │
                         ▼
              ┌──────────────────────┐
              │   API GATEWAY        │
              │   - Rate Limiting    │
              │   - AuthN / AuthZ    │
              └──────────┬───────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  INPUT GUARDRAILS                       │
│                                                         │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐ │
│  │ Length  │ │   PII    │ │ Injection│ │  Content   │ │
│  │ Check  │ │ Detector │ │ Detector │ │ Moderation │ │
│  │        │ │          │ │          │ │   API      │ │
│  └────┬────┘ └────┬─────┘ └────┬─────┘ └─────┬──────┘ │
│       │           │            │              │        │
│       └───────────┼────────────┼──────────────┘        │
│                   │            │                       │
│            ┌──────▼────────────▼──────┐                │
│            │    INPUT VALIDATION      │                │
│            │    PASS / BLOCK          │                │
│            └────────────┬─────────────┘                │
└─────────────────────────┼───────────────────────────────┘
                          │
                   ┌──────▼──────┐
                   │             │
              PASS │         BLOCK
                   │             │
            ┌──────▼──────┐  ┌──▼──────────────┐
            │  LLM        │  │  BLOCKED        │
            │  SERVICE    │  │  RESPONSE       │
            │             │  │  "Request       │
            │             │  │   cannot be     │
            │             │  │   processed"    │
            └──────┬──────┘  └─────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│                  OUTPUT GUARDRAILS                      │
│                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐ │
│  │ Toxicity │ │Factuality│ │   PII    │ │  Format   │ │
│  │ Screen   │ │  Check   │ │Re-scan   │ │ Validator │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └─────┬─────┘ │
│       │            │            │              │       │
│       └────────────┼────────────┼──────────────┘       │
│                    │            │                      │
│             ┌──────▼────────────▼──────┐               │
│             │   OUTPUT VALIDATION      │               │
│             │   PASS / FLAG / BLOCK    │               │
│             └────────────┬─────────────┘               │
└──────────────────────────┼──────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  RESPONSE   │
                    │  TO USER    │
                    └─────────────┘

         ┌──────────────────────────────────┐
         │       CROSS-CUTTING LAYER        │
         │  ┌────────┐ ┌────────┐ ┌──────┐ │
         │  │ Audit  │ │ Metric │ │Alert │ │
         │  │ Logger │ │Collect │ │ Mgr  │ │
         │  └────────┘ └────────┘ └──────┘ │
         └──────────────────────────────────┘
```

### Mermaid Diagram

```mermaid
flowchart TB
    USER["User Request"] --> GW["API Gateway<br/>Rate Limiting, Auth"]

    GW --> INPUT["Input Guardrails"]

    subgraph IG["Input Guardrail Pipeline"]
        direction LR
        LC["Length Check"] --> PII["PII Detection"]
        PII --> ID["Injection Detection"]
        ID --> CM["Content Moderation"]
    end

    INPUT --> DECISION{"All Checks<br/>Pass?"}

    DECISION -->|No| BLOCK["Blocked Response<br/>'Cannot process request'"]
    DECISION -->|Yes| LLM["LLM Service"]

    LLM --> OUTPUT["Output Guardrails"]

    subgraph OG["Output Guardrail Pipeline"]
        direction LR
        TOX["Toxicity Screen"] --> FACT["Factuality Check"]
        FACT --> PII2["PII Re-scan"]
        PII2 --> FMT["Format Validation"]
    end

    OUTPUT --> RESULT{"Output<br/>Valid?"}

    RESULT -->|No| REGEN["Regenerate or Flag"]
    RESULT -->|Yes| RESP["Response to User"]

    REGEN --> LLM

    IG -.->|"Logs"| AUDIT["Audit Logger"]
    OG -.->|"Logs"| AUDIT
    AUDIT --> METRICS["Metrics & Alerts"]

    style USER fill:#e94560,color:#fff
    style BLOCK fill:#c0392b,color:#fff
    style RESP fill:#27ae60,color:#fff
    style LLM fill:#3498db,color:#fff
```

---

## 3. EU AI Act Risk Classification Flow

### ASCII Diagram

```
                    ┌──────────────────┐
                    │   AI SYSTEM      │
                    │   ASSESSMENT     │
                    └────────┬─────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │  Is the system a PROHIBITED  │
              │  practice?                   │
              │  - Social scoring            │
              │  - Real-time biometric       │
              │    surveillance (public)     │
              │  - Manipulation of           │
              │    vulnerable groups         │
              └──────────────┬───────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
                   YES               NO
                    │                 │
                    ▼                 ▼
        ┌────────────────┐  ┌──────────────────────────┐
        │  UNACCEPTABLE  │  │  Is the system a HIGH    │
        │  RISK          │  │  RISK application?       │
        │                │  │  - Biometrics            │
        │  PROHIBITED    │  │  - Critical infrastructure│
        │  Cannot be     │  │  - Education/employment  │
        │  deployed      │  │  - Essential services    │
        │                │  │  - Law enforcement       │
        └────────────────┘  │  - Migration/justice     │
                            └────────────┬─────────────┘
                                         │
                                ┌────────┴────────┐
                                │                 │
                               YES               NO
                                │                 │
                                ▼                 ▼
                ┌──────────────────────┐  ┌──────────────────────────┐
                │      HIGH RISK      │  │  Does the system have    │
                │                      │  │  LIMITED RISK features?  │
                │  Obligations:       │  │  - Chatbot (disclosure)  │
                │  - Conformity assess │  │  - Deepfake (labeling)   │
                │  - Risk management  │  │  - Emotion recognition   │
                │  - Data governance  │  └────────────┬─────────────┘
                │  - Documentation    │               │
                │  - Human oversight  │      ┌────────┴────────┐
                │  - Audit trail      │      │                 │
                │  - EU DB registry   │     YES               NO
                └──────────────────────┘      │                 │
                                              ▼                 ▼
                                  ┌────────────────┐  ┌────────────────┐
                                  │   LIMITED      │  │   MINIMAL      │
                                  │   RISK         │  │   RISK         │
                                  │                │  │                │
                                  │  Obligations:  │  │  No specific   │
                                  │  - Transparency│  │  obligations   │
                                  │  - Disclosure  │  │                │
                                  │  - Labeling    │  │  Examples:     │
                                  │                │  │  - Spam filter │
                                  │                │  │  - AI games    │
                                  └────────────────┘  └────────────────┘
```

### Mermaid Diagram

```mermaid
flowchart TD
    START["AI System Assessment"] --> Q1{"Is it a<br/>PROHIBITED practice?<br/>(social scoring, real-time<br/>biometric surveillance,<br/>manipulation)"}

    Q1 -->|Yes| UNACCEPTABLE["UNACCEPTABLE RISK<br/>Cannot be deployed"]
    Q1 -->|No| Q2{"Is it a<br/>HIGH-RISK<br/>application?<br/>(biometrics, critical<br/>infra, education,<br/>employment, credit,<br/>law enforcement)"}

    Q2 -->|Yes| HIGH["HIGH RISK"]
    Q2 -->|No| Q3{"Does it have<br/>LIMITED RISK<br/>features?<br/>(chatbot, deepfake,<br/>emotion recognition)"}

    Q3 -->|Yes| LIMITED["LIMITED RISK"]
    Q3 -->|No| MINIMAL["MINIMAL RISK"]

    subgraph HighObligations["HIGH RISK Obligations"]
        HO1["Conformity Assessment"]
        HO2["Risk Management System"]
        HO3["Data Governance"]
        HO4["Technical Documentation"]
        HO5["Human Oversight"]
        HO6["EU Database Registration"]
    end

    subgraph LimitedObligations["LIMITED RISK Obligations"]
        LO1["Transparency Disclosure"]
        LO2["Content Labeling"]
    end

    HIGH --> HighObligations
    LIMITED --> LimitedObligations

    style UNACCEPTABLE fill:#c0392b,color:#fff
    style HIGH fill:#e67e22,color:#fff
    style LIMITED fill:#f1c40f,color:#000
    style MINIMAL fill:#27ae60,color:#fff
    style START fill:#3498db,color:#fff
```

---

## 4. Responsible AI Lifecycle

### ASCII Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  RESPONSIBLE AI LIFECYCLE                     │
│                                                               │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│   │  DESIGN  │───▶│  BUILD   │───▶│  TEST    │              │
│   │          │    │          │    │          │              │
│   │ Problem  │    │ Data     │    │ Bias     │              │
│   │ framing  │    │ sourcing │    │ testing  │              │
│   │ Ethics   │    │ Feature  │    │ Red-team │              │
│   │ review   │    │ engineer │    │ testing  │              │
│   │ Privacy  │    │ Model    │    │ Fairness │              │
│   │ impact   │    │ training │    │ metrics  │              │
│   │ assess   │    │ Guardrail│    │ Explaina-│              │
│   │          │    │ design   │    │ bility   │              │
│   └──────────┘    └──────────┘    └─────┬────┘              │
│                                         │                    │
│                                         ▼                    │
│                                    ┌──────────┐              │
│                                    │ APPROVAL │              │
│                                    │          │              │
│                                    │ Govern-  │              │
│                                    │ ance     │              │
│                                    │ Board    │              │
│                                    │ Review   │              │
│                                    └─────┬────┘              │
│                                          │                   │
│              ┌───────────────────────────┘                   │
│              │                                               │
│              ▼                                               │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│   │  DEPLOY  │───▶│ MONITOR  │───▶│  REVIEW  │──────────┐  │
│   │          │    │          │    │          │          │  │
│   │ Canary / │    │ Drift    │    │ Quarterly│          │  │
│   │ gradual  │    │ detection│    │ bias     │          │  │
│   │ rollout  │    │ Fairness │    │ audit    │          │  │
│   │ Human-in│    │ tracking │    │ Incident │          │  │
│   │ the-loop │    │ PII leak │    │ review   │          │  │
│   │ Rollback │    │ monitor  │    │ Model    │          │  │
│   │ ready    │    │ Alerting │    │ card     │          │  │
│   └──────────┘    └──────────┘    │ update   │          │  │
│                                   └──────────┘          │  │
│                                          │               │  │
│                                          └───────────────┘  │
│                                          (Continuous cycle)  │
└─────────────────────────────────────────────────────────────┘
```

### Mermaid Diagram

```mermaid
flowchart LR
    DESIGN["DESIGN<br/>Problem Framing<br/>Ethics Review<br/>Privacy Impact"] --> BUILD["BUILD<br/>Data Sourcing<br/>Model Training<br/>Guardrail Design"]
    BUILD --> TEST["TEST<br/>Bias Testing<br/>Red-teaming<br/>Fairness Metrics"]
    TEST --> APPROVE{"GOVERNANCE<br/>BOARD<br/>APPROVAL"}
    APPROVE -->|Approved| DEPLOY["DEPLOY<br/>Canary Rollout<br/>Human Oversight<br/>Rollback Ready"]
    APPROVE -->|Rejected| BUILD
    DEPLOY --> MONITOR["MONITOR<br/>Drift Detection<br/>Fairness Tracking<br/>PII Monitoring"]
    MONITOR --> REVIEW["REVIEW<br/>Quarterly Audit<br/>Incident Review<br/>Card Update"]
    REVIEW --> DESIGN

    style DESIGN fill:#3498db,color:#fff
    style BUILD fill:#2980b9,color:#fff
    style TEST fill:#e67e22,color:#fff
    style APPROVE fill:#e94560,color:#fff
    style DEPLOY fill:#27ae60,color:#fff
    style MONITOR fill:#8e44ad,color:#fff
    style REVIEW fill:#f39c12,color:#fff
```

---

## 5. GDPR Compliance Data Flow

### ASCII Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     GDPR-COMPLIANT AI DATA FLOW                      │
│                                                                      │
│  ┌───────────┐     ┌───────────────┐     ┌─────────────────────┐   │
│  │   USER    │────▶│  CONSENT      │────▶│  DATA COLLECTION    │   │
│  │           │     │  MANAGEMENT   │     │                     │   │
│  │ Provides  │     │               │     │  - Purpose limitation│   │
│  │ consent   │     │  - Granular   │     │  - Data minimization│   │
│  │ via       │     │  - Revocable  │     │  - Lawful basis     │   │
│  │ consent   │     │  - Logged     │     │  - Documented       │   │
│  │ form      │     │  - GDPR Art.7 │     │                     │   │
│  └───────────┘     └───────┬───────┘     └──────────┬──────────┘   │
│                            │                        │               │
│              ┌─────────────▼────────────────────────▼─────────┐    │
│              │              DATA PROCESSING                    │    │
│              │  ┌───────────┐  ┌──────────┐  ┌────────────┐  │    │
│              │  │ Anonymize │  │Pseudonym-│  │ Encryption │  │    │
│              │  │ (Art.25)  │  │ ize      │  │ at rest    │  │    │
│              │  └─────┬─────┘  └────┬─────┘  └─────┬──────┘  │    │
│              │        │             │               │         │    │
│              │        └─────────────┼───────────────┘         │    │
│              │                      │                         │    │
│              │              ┌───────▼───────┐                 │    │
│              │              │  AI TRAINING  │                 │    │
│              │              │  & INFERENCE  │                 │    │
│              │              └───────┬───────┘                 │    │
│              └──────────────────────┼─────────────────────────┘    │
│                                     │                               │
│              ┌──────────────────────▼─────────────────────────┐    │
│              │           DATA SUBJECT RIGHTS                  │    │
│              │                                                │    │
│              │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌─────┐│    │
│              │  │Access│ │Rec-  │ │Erase │ │Port- │ │Object││    │
│              │  │      │ │tify  │ │      │ │able  │ │     ││    │
│              │  │Art.15│ │Art.16│ │Art.17│ │Art.20│ │Art.21││    │
│              │  └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬──┘│    │
│              │     └────────┴────────┴────────┴────────┘    │    │
│              │              ┌───────────────┐                │    │
│              │              │  AUDIT TRAIL  │                │    │
│              │              │  (Art. 30)    │                │    │
│              │              └───────────────┘                │    │
│              └───────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Mermaid Diagram

```mermaid
flowchart TD
    USER["User / Data Subject"] --> CONSENT["Consent Management<br/>Granular, Revocable, Logged<br/>GDPR Art. 7"]
    CONSENT --> COLLECTION["Data Collection<br/>Purpose Limitation<br/>Data Minimization<br/>Lawful Basis"]

    COLLECTION --> PROCESSING["Data Processing"]

    subgraph PROC["Processing Pipeline"]
        ANON["Anonymization<br/>Irreversible<br/>Art. 25"]
        PSEUDO["Pseudonymization<br/>Reversible with key<br/>Art. 25"]
        ENCRYPT["Encryption at Rest<br/>Technical Safeguard"]
    end

    PROCESSING --> PROC
    PROC --> TRAIN["AI Training & Inference"]

    TRAIN --> RIGHTS["Data Subject Rights"]

    subgraph DSAR["DSAR Handling"]
        R1["Access - Art. 15"]
        R2["Rectification - Art. 16"]
        R3["Erasure - Art. 17"]
        R4["Portability - Art. 20"]
        R5["Object - Art. 21"]
    end

    RIGHTS --> DSAR

    DSAR --> AUDIT["Audit Trail<br/>Art. 30 Records"]

    style USER fill:#3498db,color:#fff
    style CONSENT fill:#e67e22,color:#fff
    style PROCESSING fill:#2980b9,color:#fff
    style RIGHTS fill:#e94560,color:#fff
    style AUDIT fill:#8e44ad,color:#fff
```

---

## Usage Notes

- **ASCII diagrams** render correctly in any terminal or plain text viewer
- **Mermaid diagrams** render in GitHub, GitLab, VS Code (with plugin), Notion, and most modern markdown viewers
- Use these diagrams in presentations by exporting Mermaid to SVG/PNG via [mermaid.live](https://mermaid.live)
