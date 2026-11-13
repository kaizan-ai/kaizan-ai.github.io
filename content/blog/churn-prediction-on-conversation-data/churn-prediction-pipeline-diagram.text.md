**Churn prediction on conversation data: How a churn prediction pipeline reads conversation data**

- **Input:** Calls, emails, chat

1. **Signal capture.** Every call, email and chat attached to the client record.
2. **Feature extraction.** Raw conversation turned into signals a model can use.
3. **The model.** Trained on your own retained, expanded and lost accounts.
4. **Alerting and next action.** A score, an owner and a suggested first move.

- **Output:** Account owner acts

**Inside feature extraction**
- Sentiment trend (30/60/90 days)
- Response time and recency
- Risk-mention frequency
- Decision-maker recency and stakeholder coverage

Prediction only pays off when the score reaches an owner with a next step.
