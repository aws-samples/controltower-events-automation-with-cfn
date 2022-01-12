# Automate VPC tagging with AWS Control Tower lifecycle events

## Security
See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License
This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.

## Introduction
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
## Overview
![aws-control-tower-lifecycle-events](https://user-images.githubusercontent.com/83367938/149060901-2fb3e518-fae7-4983-a1ad-8bded2e646f1.png)

The diagram above shows the architecture that you deployed in the walkthrough. In the diagram, “Management account” is where the CloudFormation template is deployed. “New account” is the account created by Account Factory.

The following points summarize the workflow and the resources deployed:

1. AWS Control Tower Account Factory provisions a new AWS account.
2. CloudTrail (https://aws.amazon.com/cloudtrail/) captures the new account creation as an AWS Control Tower lifecycle event.
3. In the management account, AWS Control Tower records the lifecycle event and invokes EventBridge. 

1. EventBridge receives the event and matches the event pattern to a rule. The rule in this case invokes an AWS Lambda function.
2. The AWS Lambda function assumes the ControlTowerExecutionRole created with the new account to tag resources in the account.
3. The CloudFormation template also deploys an Amazon Simple Queue Service (Amazon SQS) (https://aws.amazon.com/sqs/) dead-letter queue to receive EventBridge and AWS Lambda failure messages.

## Prerequisites
For the deployment, you must have the following:

* An AWS account. If you don’t have an AWS account, sign up at https://aws.amazon.com (https://aws.amazon.com/). You must have administrative credentials to this account. This is the account referred to as “Management account” in Figure 1.
* An AWS Control Tower landing zone in the AWS account. For instructions, see AWS Control Tower – Set up & Govern a Multi-Account AWS Environment (https://aws.amazon.com/blogs/aws/aws-control-tower-set-up-govern-a-multi-account-aws-environment/).

## Walkthrough

### Step 1: Prepare your environment
To prepare your environment for the walkthrough, do the following:

1. Download the GitHub repository (https://github.com/rickaws/vpc-tagging-ct-lifecycle-events) I’ve prepared.
2. Sign in to your AWS account that contains the AWS Control Tower landing zone, configured previously. Select the AWS Region where AWS Control Tower is deployed in the top toolbar.
3. Open the Amazon S3 console (https://console.aws.amazon.com/s3/home).
4. Create a new S3 bucket (https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html) in the Region in which AWS Control Tower is deployed. Give the bucket a unique name (for example, your 12-digit AWS account number) and make a note of it.
5. Upload AutomatedTaggingLambda.zip from the *Lambda* folder of the repository to the new S3 bucket.


### Step 2: Deploy the automation stack
Next, deploy the stack using the .yaml template in the repository.

1. Open the CloudFormation console (https://console.aws.amazon.com/cloudfront/home?). Select the Region where AWS Control Tower is deployed from the top toolbar.
2. On the *Stacks* page, choose *Create stack*, then choose *With new resources (standard)*.
3. On the *Create stack* page, in the *Specify template* section, choose *Upload a template* file.
4. Choose *Choose file*. Select vpc-tagging-ct-lifecycle-stack.yml in the *CloudFormation* folder of the repository. Then choose *Next*.
5. On the *Specify stack details* page, enter a stack name. You can keep or edit the default event bus name. For *S3BucketName*, enter the name of the S3 bucket you created previously. For *S3LambdaZipName*, enter AutomatedTaggingLambda.zip. Then choose *Next*.
6. On the *Configure stack options* page, choose *Next*.
7. On the *Review* page, review the parameters and select *I acknowledge that AWS CloudFormation might create IAM resources with custom names*.
8. Choose *Create stack*.

### Step 3. Review the EventBridge rule

After the stack is created, you can review the deployed EventBridge rule in the EventBridge console (https://console.aws.amazon.com/events/home?region=us-east-1#/). The rule, which is named VPCTaggingHub-Rule, has the following event pattern:

```json
{
  "source": ["aws.controltower"],
  "detail-type": ["AWS Service Event via CloudTrail"],
  "detail": {
    "eventName": ["CreateManagedAccount"]
  }
}
```

### Step 4. Test the automation
There are two methods to test the automation and demonstrate the tagging carried out by the AWS Lambda function. You can emulate a real-world scenario in which you provision an account using AWS Control Tower Account Factory. Or, you can run a test set using JSON parameters that would be passed as part of a typical CreateManagedAccount lifecycle event. In other words, you can manually invoke the AWS Lambda function to tag resources in an existing account. For this second option, you must have previously created an account with AWS Control Tower Account Factory.

#### Method A. Test by creating a new account with Account Factory
With this method, first create a new AWS account with Account Factory. Then, sign in to the new account to see the tags the AWS Lambda function creates automatically.

1. Open the Account Factory page (https://us-west-2.console.aws.amazon.com/controltower/home/accountfactory?region=us-west-2) in the AWS Control Tower console. In the top toolbar, choose the Region where you previously deployed the AWS Control Tower landing zone.
2. Choose *Enroll account*.
3. Complete the *Account details* page and choose *Enroll account*. Enrollment can take up to 45 minutes. After enrollment is complete, VPCTaggingHub-Rule initiates the AWS Lambda function automatically. The function tags the VPC and its subnets, internet gateway, NAT gateway, and route table with the Region and Availability Zone.
4. To see the results, sign in to the new account and open the VPC console (https://console.aws.amazon.com/vpc/home?region=us-east-1).
5. Choose a resource in navigation pane. For example, to review tags for the subnets, choose *Subnets*.
6. On the resource page, choose the *Tags* tab.

##### Method B. Test by manually invoking AWS Lambda
Run the AWS Lambda function manually to tag resources in an existing AWS account. To use this method, the AWS account to be tagged must have been created with Account Factory.

1. Open the Functions page (https://console.aws.amazon.com/lambda/home?%2Ffunctions=&r=&region=us-east-1#/functions) in the AWS Lambda console. Choose the Region where the CloudFormation stack is deployed in the top toolbar.
2. In the *Function name* column, choose <<Account-ID>>- CTLifeCycleEventLambda-AutomatedVPCTagging.
3. On the function’s detail page, choose the *Test* tab.
4. Choose *New event*.
5. Enter an event name (for example, test). 
6. Copy and paste the following code into the body of the event. Replace <<MGMT_ACCOUNT_ID>> with the 12-digit account number for your management AWS account. Replace <<FIRST_ACCOUNT_ID>> with the account number of the AWS account that you want to tag.

```json
{
  "detail-type": "AWS Service Event via CloudTrail",
  "source": "aws.controltower",
  "account": "<<MGMT_ACCOUNT_ID>>",
  "detail": {
    "eventSource": "controltower.amazonaws.com",
    "eventName": "CreateManagedAccount",
    "recipientAccountId": "<<TEST_ACCOUNT_ID>>",
    "serviceEventDetails": {
      "createManagedAccountStatus": {
        "account": {
          "accountName": "SampleAccount",
          "accountId": "<<MGMT_ACCOUNT_ID>>"
        },
        "state": "SUCCEEDED"
      }
    }
  }
}
```
  
7. Choose *Save changes*.
8. Choose *Test*. The function can take 2–3 minutes to run, depending on the number of Regions with VPCs deployed with AWS Control Tower. Test results appear on the *Test* tab, with resources labeled by the function listed in the *Log output* field.
9. To see the tags on resources in the target account, sign in to the account and open the VPC console (https://console.aws.amazon.com/vpc/home?region=us-east-1).

## Cleanup
  
To avoid incurring future charges, delete the resources you created during the walkthrough. Follow these steps:

1. Open the CloudFormation console (https://console.aws.amazon.com/cloudformation).
2. On the *Stacks* page, select the stack you created during the walkthrough.
3. Choose *Delete*.

To decommission or remove accounts you created with Account Factory during testing, see Unmanaging a Member Account (https://docs.aws.amazon.com/controltower/latest/userguide/account-factory.html?icmpid=docs_ctower_console#unmanage-account).

## Conclusion
In this post, I explained how to use AWS Control Tower lifecycle events to automate the tagging of VPC resources in a new account created with AWS Control Tower.

I invite you to adapt the AWS Lambda function I’ve provided in my GitHub repository (https://github.com/aws-samples/controltower-events-automation-with-cfn/tree/main/lambda). Edit the Python code to customize tagging standards. Or, program it to automate a task other than tagging. For an example of an AWS Solution Implementation that also uses CloudFormation templates to customize landing zones, see Customizations for AWS Control Tower (https://aws.amazon.com/solutions/implementations/customizations-for-aws-control-tower/?did=sl_card&trk=sl_card). Let me know your questions or findings in the comments, and have fun!

