import aws_cdk.aws_elasticache as elasticache
from aws_cdk import Stack
from constructs import Construct


class CdkRedisStack(Stack):

    def __init__(self, scope: Construct, id: str, vpc, redis_sg, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        private_subnets_ids = [ps.subnet_id for ps in vpc.private_subnets]

        redis_subnet_group = elasticache.CfnSubnetGroup(
            self,
            'redis_subnet_group',
            subnet_ids=private_subnets_ids,
            description='subnet group for redis')

        self.redis_cluster = elasticache.CfnCacheCluster(
            scope=self,
            id='wp-redis',
            engine='redis',
            cluster_name='wordpress-redis',
            cache_node_type='cache.t3.micro',
            num_cache_nodes=1,
            cache_subnet_group_name=redis_subnet_group.ref,
            vpc_security_group_ids=[redis_sg.security_group_id])
