## Automate VPC tagging with AWS Control Tower lifecycle events

Be sure to:

* Change the title in this README
* Edit your repository description on GitHub

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

##Introduction
When building an enterprise architecture for the cloud, customers often put much initial thought into ensuring they build a structure for success. In most cases, this consists of services like AWS Organizations (https://aws.amazon.com/organizations/) and AWS Control Tower (https://aws.amazon.com/controltower/), which deploy a foundation to support a scalable, multi-account structure. Into this foundation, you can automatically provision Amazon Web Services (AWS) accounts using AWS Control Tower Account Factory (https://docs.aws.amazon.com/controltower/latest/userguide/account-factory.html). But what about automated resource configuration in these new accounts? For example, can you automate manual tasks such as tagging (https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html) resources in virtual private clouds (VPCs)? With AWS Control Tower lifecycle events (https://docs.aws.amazon.com/controltower/latest/userguide/lifecycle-events.html) and Amazon EventBridge, the answer is yes. AWS Control Tower lifecycle events extend automation across the organization. It reduces or removes the need to perform manual configuration of resources after account provisioning.  

In this post, I demonstrate how to use lifecycle events to automatically configure resources in newly provisioned AWS accounts. Specifically, I use an AWS Lambda (https://aws.amazon.com/lambda/) function invoked by Amazon EventBridge (https://aws.amazon.com/eventbridge/) to tag resources in an AWS account created by AWS Control Tower. I’ve prepared a GitHub repository (https://github.com/rickaws/vpc-tagging-ct-lifecycle-events) that contains an AWS CloudFormation (https://aws.amazon.com/cloudformation/) template to deploy, and an AWS Lambda function to do the tagging.

Time  to read:        ~ 8 min.
Time  to complete:    ~30 min.
Learning  level:    	Advaned (300)
AWS  services:
                      AWS Control Tower
                      AWS  CloudFormation
                      Amazon Virtual Private Cloud (Amazon VPC)
                      Amazon Simple Storage Service (Amazon S3)
                      Amazon CloudWatch Events
                      AWS CloudTrail
                      Amazon EventBridge
                      AWS Lambda
##Overview

[Figure 1](CONTRIBUTING.md#security-issue-notifications) shows the architecture that you deployed in the walkthrough. In the diagram, “Management account” is where the CloudFormation template is deployed. “New account” is the account created by Account Factory.

The following points summarize the workflow and the resources deployed:

1. AWS Control Tower Account Factory provisions a new AWS account.
2. CloudTrail (https://aws.amazon.com/cloudtrail/) captures the new account creation as an AWS Control Tower lifecycle event.
3. In the management account, AWS Control Tower records the lifecycle event and invokes EventBridge. 

1. EventBridge receives the event and matches the event pattern to a rule. The rule in this case invokes an AWS Lambda function.
2. The AWS Lambda function assumes the ControlTowerExecutionRole created with the new account to tag resources in the account.
3. The CloudFormation template also deploys an Amazon Simple Queue Service (Amazon SQS) (https://aws.amazon.com/sqs/) dead-letter queue to receive EventBridge and AWS Lambda failure messages.

