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
