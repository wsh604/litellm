from json import dumps
from typing import Callable

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status

from litellm.proxy._types import (
    UserAPIKeyAuth,
)
from litellm.proxy.auth.user_api_key_auth import user_api_key_auth
from .WLog import log

TAG = "librechat"
router = APIRouter()
model_list: Callable

inner_models = ("azureOpenAI", "openAI", "bingAI", "chatGPTBrowser", "google", "gptPlugins", "anthropic", "assistants", "azureAssistants", "agents", "bedrock")

def set_model_list_def(model_list_from_proxy: Callable):
    global model_list
    model_list = model_list_from_proxy

@router.get(
    "/api/models",
    dependencies=[Depends(user_api_key_auth)],
    tags=[TAG]
)
async def models(user_api_key_dict: UserAPIKeyAuth = Depends(user_api_key_auth)):
    originData = await model_list(user_api_key_dict)
    log(TAG, originData)

    # myTest = {'data': [{'id': 'deepseek/deepseek-chat', 'object': 'model', 'created': 1677610602, 'owned_by': 'openai'}
    #     ,{'id': 'deepseek/deepseek-chat2', 'object': 'model', 'created': 1677610602, 'owned_by': 'openai'}
    #     ,{'id': 'openai/deepseek-chat3', 'object': 'model', 'created': 1677610602, 'owned_by': 'openai'}], 'object': 'list'}
    # data = myTest['data']

    data = originData['data']
    if data is not None:
        if len(data) > 0:
            outData = {}
            for item in data:
                log(TAG, item)
                ## 模型名字为：模型分组/模型具体名
                name = str(item['id'])
                index = name.index("/")
                group_name = name[0:index]
                model_name = name[index+1:]
                group = outData.get(group_name)
                if group is None:
                    group = []
                    outData[group_name] = group
                group.append(model_name)
            print(TAG, outData)
            return outData
    return {}


@router.get(
    "/api/endpoints",
    dependencies=[Depends(user_api_key_auth)],
    tags=[TAG]
)
async def endpoints(user_api_key_dict: UserAPIKeyAuth = Depends(user_api_key_auth)):
    models_dict = await models(user_api_key_dict)
    log(TAG, models_dict)
    outData = {}
    idx = 0
    for key in models_dict:
        outData[key] = {
            'userProvide': True,
            'order': idx
        }
        idx += 1
        if not isInnerModel(key):
            outData[key]["type"] = "custom"

    return outData

def isInnerModel(name):
    return inner_models.__contains__(name)

@router.get(
    "/api/keys",
    dependencies=[Depends(user_api_key_auth)],
    tags=[TAG]
)
async def keys(name):
    return {
        'id': name,
        'expiresAt': "2034-11-17T06:58:35.462Z"
    }


@router.post(
    "/api/files/images",
    dependencies=[Depends(user_api_key_auth)],
    tags=[TAG]
)
async def image():
    return ""


@router.post(
    "/api/files",
    dependencies=[Depends(user_api_key_auth)],
    tags=[TAG]
)
async def file():
    return ""
