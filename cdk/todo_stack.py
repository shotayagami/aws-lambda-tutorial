from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack
from aws_cdk import aws_apigatewayv2 as apigw
from aws_cdk import aws_apigatewayv2_integrations as integrations
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_lambda as _lambda
from constructs import Construct


class TodoStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        table = dynamodb.Table(
            self,
            "TodoTable",
            partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,  # 学習用。本番では RETAIN を検討
        )

        fn = _lambda.Function(
            self,
            "TodoFunction",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="todo_api.app.handler",
            code=_lambda.Code.from_asset("../src"),
            timeout=Duration.seconds(10),
            memory_size=256,
            environment={"TABLE_NAME": table.table_name},
        )
        table.grant_read_write_data(fn)  # 最小権限の IAM ポリシーを自動生成

        api = apigw.HttpApi(self, "TodoApi")
        integration = integrations.HttpLambdaIntegration("TodoIntegration", fn)
        api.add_routes(path="/todos", methods=[apigw.HttpMethod.ANY], integration=integration)
        api.add_routes(path="/todos/{id}", methods=[apigw.HttpMethod.ANY], integration=integration)

        CfnOutput(self, "ApiUrl", value=f"{api.api_endpoint}/todos")
