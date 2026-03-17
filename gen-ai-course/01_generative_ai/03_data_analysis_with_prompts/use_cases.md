# Use Cases: Data Analysis with Prompts

This document provides practical use cases demonstrating bad prompts vs good prompts across different business roles.

---

## Table of Contents

1. [Bad Prompt vs Good Prompt Examples](#bad-prompt-vs-good-prompt-examples)
2. [Sales Team Use Cases](#sales-team-use-cases)
3. [Business Analyst Use Cases](#business-analyst-use-cases)

---

## Bad Prompt vs Good Prompt Examples

### Example 1: Sales Data Analysis

#### ❌ Bad Prompt
```
Analyze my sales data
```

**Problems:**
- No context about what analysis is needed
- No data provided
- No format specified
- Too vague for useful output

---

#### ✅ Good Prompt
```
Analyze the Q4 2024 sales data below and provide:
1. Total revenue by product category (show as table)
2. Top 5 performing products by revenue
3. Month-over-month growth rate
4. Key insights and recommendations

Data:
| Product | Jan | Feb | Mar |
|---------|-----|-----|-----|
| Laptop  | 50000 | 55000 | 62000 |
| Phone   | 45000 | 48000 | 52000 |
| Tablet  | 30000 | 32000 | 35000 |
| Watch   | 25000 | 28000 | 31000 |
```

**Why it works:**
- Specifies time period (Q4 2024)
- Lists specific analysis requirements
- Provides data in structured format
- Asks for specific output format (table)
- Requests actionable insights

---

### Example 2: Customer Feedback Analysis

#### ❌ Bad Prompt
```
Look at these reviews and tell me what people think
```

**Problems:**
- No reviews provided
- No specific questions
- No output format
- Subjective "what people think"

---

#### ✅ Good Prompt
```
Categorize each customer review as: Positive, Negative, or Neutral

For each review, extract:
- Sentiment score (1-10)
- Key theme (Product Quality, Customer Service, Pricing, Shipping)
- Specific issue if any

Reviews:
1. "Absolutely love this product! Best purchase ever."
2. "Terrible quality, broke after one week."
3. "It's okay, not great but not bad either."
4. "Fast shipping but the product was damaged."

Return as a JSON array with fields: review, sentiment, theme, issue
```

**Why it works:**
- Clear categorization criteria
- Specific extraction fields
- Data provided inline
- Output format specified (JSON)

---

### Example 3: Market Research Summary

#### ❌ Bad Prompt
```
What's happening in the tech industry?
```

**Problems:**
- Too broad/vague
- No timeframe
- No specific focus area
- Could return anything

---

#### ✅ Good Prompt
```
Summarize the key trends in the AI software market for 2024, focusing on:
1. Top 5 market leaders and their recent product launches
2. Emerging technologies gaining traction
3. Investment trends (funding amounts, major deals)
4. Predictions for 2025

For each section, provide 3-5 bullet points with specific data points.
Format as a professional market research summary.
```

**Why it works:**
- Clear scope (AI software, 2024)
- Specific sections to cover
- Numbered requirements
- Output format specified
- Professional context provided

---

## Sales Team Use Cases

### Use Case 1: Lead Qualification

#### Prompt
```
As a sales expert, analyze the following lead information and provide:

1. Lead score (1-100) with justification
2. Recommended next action (Hot/Warm/Cold)
3. Key talking points for initial call
4. Potential objections and how to handle them

Lead Data:
- Company: TechStart Inc (50 employees)
- Industry: SaaS
- Annual Revenue: $5M
- Website Visits: 150/month
- Email Opens: 12% (4 emails sent)
- Webinar Attendance: 0
- Product Interest: "Looking for project management tool"
- Budget: "Not sure yet"
- Timeline: "Maybe next quarter"

Output format: Structured report
```

**Expected Output:**
- Lead score with breakdown
- Classification and rationale
- Customized talking points
- Pre-emptive objection handling

---

### Use Case 2: Sales Call Preparation

#### Prompt
```
Prepare for a sales call with the following prospect:

Prospect: Sarah Johnson, VP Operations at Healthcare Solutions Inc
Company Size: 200 employees
Industry: Healthcare IT
Current Pain Points mentioned:
- Manual data entry causing errors
- Compliance concerns with patient data
- Slow reporting turnaround

Research the healthcare IT market and provide:
1. 3 relevant industry statistics
2. Common challenges in this sector
3. How our solution addresses their pain points
4. 5 smart questions to ask
5. Recommended demo focus areas

Format: Sales preparation brief
```

---

### Use Case 3: Competitive Analysis

#### Prompt
```
Compare our solution (ProductX) vs CompetitorY for a mid-market SaaS company.

ProductX Features:
- AI-powered automation
- Real-time analytics
- Integrates with 50+ tools
- $99/user/month

CompetitorY Features:
- Basic automation
- Daily analytics updates
- Integrates with 20 tools
- $149/user/month

Provide:
1. Feature comparison matrix
2. Price advantage analysis
3. Best use cases for each product
4. Win strategy for ProductX
5. Likely competitor objections

Format: Competitive battlecard
```

---

### Use Case 4: Email Outreach

#### Prompt
```
Write a personalized cold email for:

Prospect: CTO at FinTech startup (50 people)
Context: They recently raised Series B funding
Trigger: Their company was featured in TechCrunch for expansion

Requirements:
- Subject line
- Opening hook (reference funding news)
- Value proposition (focus on security compliance)
- Specific example/relevant case study
- Call to action
- Professional sign-off

Tone: Professional but conversational
Length: Under 200 words
```

---

## Business Analyst Use Cases

### Use Case 1: Requirements Analysis

#### Prompt
```
Analyze the following feature request and create:

1. User story with acceptance criteria
2. Functional requirements (5-7 items)
3. Non-functional requirements
4. Technical considerations
5. Dependencies
6. Potential risks and mitigation

Feature Request:
"We want to add a dashboard that shows real-time sales metrics including revenue, conversion rates, and top products. Managers should be able to customize their view and set alerts for important metrics."

Format: Requirements document template
```

---

### Use Case 2: Process Documentation

#### Prompt
```
Document the current order fulfillment process and identify improvement opportunities:

Current Process (as described):
1. Customer places order
2. Order sent to warehouse
3. Warehouse picks and packs
4. Shipping label created
5. Package handed to carrier
6. Customer receives tracking email
7. Customer receives package

For each step, provide:
- Duration estimate
- Owner/role
- Current pain points
- Improvement suggestions

Finally, provide:
- Process efficiency score (0-100)
- Top 3 improvement recommendations
- Expected ROI of improvements

Format: Process analysis report
```

---

### Use Case 3: Data Validation Rules

#### Prompt
```
Define validation rules for a customer onboarding form.

Form Fields:
- Company Name (required)
- Contact Email (required)
- Phone Number (optional)
- Industry (required, select from list)
- Company Size (required, select from list)
- Annual Revenue (optional)
- Use Case Description (required, min 50 chars)

For each field, specify:
1. Validation type (required, format, range, custom)
2. Error message for invalid input
3. Data type
4. Sanitization needed (yes/no)
5. Compliance considerations (PII, etc.)

Output: Validation matrix table
```

---

### Use Case 4: Stakeholder Interview Questions

#### Prompt
```
Generate interview questions for gathering requirements for a new reporting dashboard.

Stakeholder: C-level executives
Goal: Understand what metrics matter most for strategic decisions

Include:
1. Opening questions (3)
2. Current pain points (4)
3. Metrics they track (4)
4. Decision-making process (3)
5. Visualization preferences (3)
6. Prioritization (2)

Also provide:
- Interview guide tips
- How to probe for deeper answers
- Common pitfalls to avoid

Format: Interview guide document
```

---

### Use Case 5: UAT Test Cases

#### Prompt
```
Create UAT (User Acceptance Testing) test cases for a login feature.

Features:
- Email/password login
- "Remember me" checkbox
- "Forgot password" link
- Account lockout after 5 failed attempts
- Multi-factor authentication (optional)

For each feature, create:
1. Test case ID
2. Test case description
3. Pre-conditions
4. Test steps
5. Expected result
6. Test data needed

Include both positive and negative test scenarios.
Also add:
- Login performance requirements
- Security test scenarios
- Browser compatibility checks

Format: Test case matrix
```

---

## Quick Reference: Prompt Templates

### Sales Team Template
```
Analyze [specific data/context] and provide:
1. [Specific output 1]
2. [Specific output 2]
3. [Specific output 3]

Data:
[Your data here]

Format: [Required format]
```

### Business Analyst Template
```
For [project/feature], create [deliverable type]:

Context:
- [Background information]
- [Stakeholders]
- [Goals]

Requirements:
1. [Specific requirement]
2. [Specific requirement]
3. [Specific requirement]

Format: [Document type]
```
