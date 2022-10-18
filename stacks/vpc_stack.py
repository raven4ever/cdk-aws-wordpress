import aws_cdk.aws_ec2 as ec2
from aws_cdk import Stack
from constructs import Construct


class CdkVpcStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.vpc = ec2.Vpc(self, 'wp-vpc',
                           vpc_name='wordpress-vpc',
                           cidr='10.10.0.0/16',
                           subnet_configuration=[
                               ec2.SubnetConfiguration(
                                subnet_type=ec2.SubnetType.PUBLIC,
                                name='wp-public',
                                cidr_mask=24
                               ), ec2.SubnetConfiguration(
                                   subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                                   name='wp-private',
                                   cidr_mask=24
                               ), ec2.SubnetConfiguration(
                                   subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                                   name='wp-db',
                                   cidr_mask=24
                               )
                           ])

        self.alb_sg = ec2.SecurityGroup(
            self, 'alb-sg', vpc=self.vpc, security_group_name='wp-alb-sg', allow_all_outbound=True)

        self.asg_sg = ec2.SecurityGroup(
            self, 'asg-sg', vpc=self.vpc, security_group_name='wp-asg-sg', allow_all_outbound=True)

        self.rds_sg = ec2.SecurityGroup(
            self, 'rds-sg', vpc=self.vpc, security_group_name='wp-rds-sg', allow_all_outbound=True)

        self.redis_sg = ec2.SecurityGroup(
            self, 'redis-sg', vpc=self.vpc, security_group_name='wp-redis-sg', allow_all_outbound=True)

        self.efs_sg = ec2.SecurityGroup(
            self, 'efs-sg', vpc=self.vpc, security_group_name='wp-efs-sg', allow_all_outbound=True)

        # allow on 80 to ALB from Internet
        self.alb_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4('0.0.0.0/0'),
            description='Allow all to ALB',
            connection=ec2.Port.tcp(80)
        )

        # allow on 80 to ASG from ALB
        self.asg_sg.add_ingress_rule(
            peer=self.alb_sg,
            description='Allow from ALB',
            connection=ec2.Port.tcp(80)
        )

        # allow on 3306 to RDS from ASG
        self.rds_sg.add_ingress_rule(
            peer=self.asg_sg,
            description='Allow from ASG',
            connection=ec2.Port.tcp(3306)
        )

        # allow on 6379 to Redis from ASG
        self.redis_sg.add_ingress_rule(
            peer=self.asg_sg,
            description='Allow from ASG',
            connection=ec2.Port.tcp(6379)
        )

        # allow on 2049 to EFS from ASG
        self.efs_sg.add_ingress_rule(
            peer=self.asg_sg,
            description='Allow from ASG',
            connection=ec2.Port.tcp(2049)
        )
