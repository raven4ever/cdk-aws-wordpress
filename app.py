#!/usr/bin/env python3
import aws_cdk as cdk

from stacks.ec2_stack import CdkEc2Stack
from stacks.rds_stack import CdkRdsStack
from stacks.redis_stack import CdkRedisStack
from stacks.vpc_stack import CdkVpcStack

app = cdk.App()

env_us = cdk.Environment(account='227656558133', region='us-east-1')

vpc_stack = CdkVpcStack(app, 'cdk-vpc',
                        env=env_us)

rds_stack = CdkRdsStack(app, 'cdk-rds',
                        vpc=vpc_stack.vpc,
                        rds_sg=vpc_stack.rds_sg,
                        env=env_us)

redis_stack = CdkRedisStack(app, 'cdk-redis',
                            vpc=vpc_stack.vpc,
                            redis_sg=vpc_stack.redis_sg,
                            env=env_us)

ec2_stack = CdkEc2Stack(app, 'cdk-ec2',
                        vpc=vpc_stack.vpc,
                        redis_cluster=redis_stack.redis_cluster,
                        rds_cluster=rds_stack.aurora_cluster,
                        asg_sg=vpc_stack.asg_sg,
                        alb_sg=vpc_stack.alb_sg,
                        efs_sg=vpc_stack.efs_sg,
                        env=env_us)

app.synth()
