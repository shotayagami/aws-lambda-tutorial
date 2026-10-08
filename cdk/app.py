#!/usr/bin/env python3
"""CDK (Python) 版の Todo API。template.yaml と同等の構成を Python コードで書く。

    cd cdk
    pip install -r requirements.txt
    cdk synth      # CloudFormation テンプレートを生成して確認
    cdk deploy
    cdk destroy    # 後片付け
"""
import aws_cdk as cdk

from todo_stack import TodoStack

app = cdk.App()
TodoStack(app, "LambdaTodoCdk")
app.synth()
