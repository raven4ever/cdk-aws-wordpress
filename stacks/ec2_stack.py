from string import Template

import aws_cdk.aws_autoscaling as autoscaling
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_efs as efs
import aws_cdk.aws_elasticloadbalancingv2 as elb
import aws_cdk.aws_iam as iam
import aws_cdk.aws_rds as rds
from aws_cdk import CfnOutput, RemovalPolicy, Stack
from constructs import Construct


class CustomTemplate(Template):
    delimiter = '%$%'


ec2_type = 't2.nano'
linux_ami = ec2.AmazonLinuxImage(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX,
                                 edition=ec2.AmazonLinuxEdition.STANDARD,
                                 virtualization=ec2.AmazonLinuxVirt.HVM,
                                 storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE
                                 )
with open('./utils/user_data.sh') as f:
    user_data_template = CustomTemplate(f.read())


class CdkEc2Stack(Stack):

    def __init__(self, scope: Construct, id: str, vpc, redis_cluster, rds_cluster: rds.DatabaseCluster, alb_sg, asg_sg, efs_sg, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create ALB
        alb = elb.ApplicationLoadBalancer(self, 'wp-alb',
                                          vpc=vpc,
                                          internet_facing=True,
                                          load_balancer_name='wordpress-alb',
                                          security_group=alb_sg)

        listener = alb.add_listener('wp-80-listener',
                                    port=80,
                                    open=True)

        shared_efs = efs.FileSystem(self, 'wp-efs',
                                    file_system_name='wordpress-efs',
                                    vpc=vpc,
                                    vpc_subnets=ec2.SubnetSelection(
                                        subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
                                    removal_policy=RemovalPolicy.DESTROY,
                                    security_group=efs_sg)

        user_data = user_data_template.safe_substitute({
            'efs_id': shared_efs.file_system_id,
            'region': Stack.of(self).region,
            'rds_secret_id': rds_cluster.secret.secret_name,
            'redis_url': redis_cluster.attr_redis_endpoint_address
        })

        # Create Autoscaling Group
        self.asg = autoscaling.AutoScalingGroup(self, 'wp-asg',
                                                auto_scaling_group_name='wordpress-asg',
                                                vpc=vpc,
                                                vpc_subnets=ec2.SubnetSelection(
                                                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
                                                instance_type=ec2.InstanceType(
                                                    instance_type_identifier=ec2_type),
                                                machine_image=linux_ami,
                                                associate_public_ip_address=False,
                                                min_capacity=2,
                                                max_capacity=3,
                                                user_data=ec2.UserData.custom(
                                                    user_data),
                                                security_group=asg_sg)

        self.asg.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSSMManagedInstanceCore'))
        self.asg.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name('SecretsManagerReadWrite'))

        listener.add_targets('addTargetGroup',
                             port=80,
                             targets=[self.asg])

        CfnOutput(self, 'alb-dns',
                  value=alb.load_balancer_dns_name)
