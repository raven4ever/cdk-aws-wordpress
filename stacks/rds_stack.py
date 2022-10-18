import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_rds as rds
from aws_cdk import Stack
from constructs import Construct


class CdkRdsStack(Stack):

    def __init__(self, scope: Construct, id: str, vpc, rds_sg, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.aurora_cluster = rds.DatabaseCluster(self, 'wp-db',
                                                  cluster_identifier='wordpress-db',
                                                  default_database_name='wordpressdb',
                                                  engine=rds.DatabaseClusterEngine.aurora_mysql(
                                                      version=rds.AuroraMysqlEngineVersion.VER_2_10_2
                                                  ),
                                                  instance_props=rds.InstanceProps(
                                                      vpc=vpc,
                                                      security_groups=[rds_sg],
                                                      vpc_subnets=ec2.SubnetSelection(
                                                          subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
                                                      instance_type=ec2.InstanceType(
                                                          instance_type_identifier='t2.small')
                                                  ),
                                                  instances=1
                                                  )
