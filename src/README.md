# CHANGELOG
* So the code change goes into the API Lambda that stores orders, not Lambda B.
Lambda B only consumes from Step Functions and S3, it doesn’t touch the DB *** 

```bash
const table = new dynamodb.Table(this, "OrdersTable", {
  partitionKey: { name: "record_id", type: dynamodb.AttributeType.STRING },
  billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
  timeToLiveAttribute: "ttl",   // <-- TTL enabled
  removalPolicy: cdk.RemovalPolicy.DESTROY
});
```

* lambda a
When random.choice([True, False]) returns False:
```bash
{
  "results": false
}
```

When random.choice([True, False]) returns True:
```bash
{
  "results": true,
  "orders": [
    {
      "status": "accepted",
      "power": 1
    },
    {
      "status": "rejected",
      "power": 2
    }
  ]
}
```

* Lambda B
Accepted Order (successful S3 save)
```bash{
  "status": "accepted",
  "order_id": "12345",
  "customer": "John Doe",
  "items": [
    {"item_id": "A1", "quantity": 2},
    {"item_id": "B2", "quantity": 1}
  ],
  "total": 59.99
}
```

This will pass, save the order to S3, and return:

```bash{
  "status": "success",
  "file": "orders/order_<timestamp>.json"
}
```
2️⃣ Rejected Order (triggers notification)
```bash{
  "status": "rejected",
  "order_id": "12346",
  "customer": "Jane Smith"
}
```

This will fail, log an error, send a Slack notification, and raise a ValueError.

3️⃣ Missing Status (invalid event)
```bash{
  "order_id": "12347",
  "customer": "Alice"
}
```

This will raise:

ValueError: Missing 'status' field in event



* code pipeline
Source Stage → pulls your repo from GitHub using a token stored in Secrets Manager.

Build Stage → runs CodeBuild: installs CDK + Python deps, synthesizes the CloudFormation templates.

Deploy Stage → deploys the synthesized CDK app (with Lambdas, DynamoDB TTL, S3 bucket, Step Functions).

Artifacts Bucket → stores pipeline artifacts (rotated every 7 days).


* appstack
What this stack gives you

DynamoDB (TTL = 24h) for orders

S3 bucket (order-results) for accepted orders

API Lambda → saves incoming orders with TTL

Lambda A → generates results (True/False + orders)

Lambda B → processes orders, saves accepted, sends Slack-like alerts on errors

Step Functions →

Run Lambda A until results ready

Send results to Lambda B

On failure → NotifyFailure (here we re-use LambdaB with Slack notify)
