import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk_aws_wordpress.cdk_aws_wordpress_stack import CdkAwsWordpressStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_aws_wordpress/cdk_aws_wordpress_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CdkAwsWordpressStack(app, "cdk-aws-wordpress")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })