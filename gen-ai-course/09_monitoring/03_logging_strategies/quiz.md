# Quiz

## Question 1

What is the primary reason AI logging differs from traditional application logging?

A) AI systems use more storage
B) AI outputs are probabilistic and require capturing confidence scores
C) AI systems are faster
D) AI logging is required by law

---

## Answer: B

AI outputs are probabilistic, not deterministic. This requires capturing model confidence, reasoning traces, and token-level information that traditional logging doesn't need.

---

## Question 2

Which technique is best for handling PII in logs while maintaining the ability to identify user sessions?

A) Deletion
B) Hashing
C) Encryption
D) Compression

---

## Answer: B

Hashing provides one-way transformation that allows identifying the same user across sessions while keeping the original PII unrecoverable.

---

## Question 3

What correlation ID is used to track requests across distributed systems?

A) request_id
B) session_id
C) trace_id
D) user_id

---

## Answer: C

trace_id is used across distributed systems to correlate all the individual service calls that make up a single user request.

---

## Question 4

Which log level should be used for recoverable issues like automatic retries?

A) DEBUG
B) INFO
C) WARNING
D) ERROR

---

## Answer: C

WARNING is appropriate for recoverable issues like automatic retries, as these indicate potential problems that don't immediately affect the user experience.
