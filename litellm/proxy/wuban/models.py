import os
import shutil
import uuid
from datetime import datetime
from typing import Callable

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status, UploadFile
from fastapi.params import File, Form
from starlette.responses import FileResponse

from .WLog import log
from ..utils import PrismaClient
from .wuban_auth_service import combined_auth, CombinedAuthResult

TAG = "librechat"
router = APIRouter()

router.model_list = None
router.file_upload_prisma_client = None

inner_models = ("azureOpenAI", "openAI", "bingAI", "chatGPTBrowser", "google", "gptPlugins", "anthropic", "assistants", "azureAssistants", "agents", "bedrock")

@router.get(
    "/api/models",
    dependencies=[Depends(combined_auth)],
    tags=[TAG]
)
async def models(auth_result: CombinedAuthResult = Depends(combined_auth)):
    originData = await router.model_list(auth_result.litellm_auth)
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
    dependencies=[Depends(combined_auth)],
    tags=[TAG]
)
async def endpoints(auth_result: CombinedAuthResult = Depends(combined_auth)):
    models_dict = await models(auth_result)
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
    dependencies=[Depends(combined_auth)],
    tags=[TAG]
)
async def keys(name):
    return {
        'id': name,
        'expiresAt': "2034-11-17T06:58:35.462Z"
    }

@router.get(
    "/api/cdn/{file_path:path}",
    tags=[TAG]
)
async def upload_file(file_path: str):
    """
    根据path查找到对应的文件内容。
    """
    file_base_dir = os.getenv("FILE_UPLOAD_BASE_DIR")
    real_full_path = os.path.join(file_base_dir, file_path)
    if not os.path.isfile(real_full_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(real_full_path)


@router.post(
    "/api/files/images",
    dependencies=[Depends(combined_auth)],
    tags=[TAG]
)
async def image(auth_result: CombinedAuthResult = Depends(combined_auth),
                     file: UploadFile = File(),
                     file_id: str = Form(...)):
    """
    单图上传
    """
    result = await upload_file_inner(auth_result, [file], "image")
    result[0]["temp_file_id"] = file_id
    return result[0]


@router.post(
    "/api/files",
    dependencies=[Depends(combined_auth)],
    tags=[TAG]
)
async def upload_file(auth_result: CombinedAuthResult = Depends(combined_auth),
                      file: UploadFile = File(),
                      file_id: str = Form(...)):
    """
    单文件上传
    """
    result = await upload_file_inner(auth_result, [file])
    result[0]["temp_file_id"] = file_id
    return result[0]

async def upload_file_inner(auth_result: CombinedAuthResult,
                            files: list[UploadFile], file_type = "file"):
    """
    处理多文件上传
    """
    saved_file_result = []
    file_base_dir, current_date  = ensure_today_dir()
    for file in files:
        file_name = _create_file_name(file)
        file_path = os.path.join(file_base_dir, file_name)
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_path = os.path.join(current_date, file_name)
        ret = await insert_db(file_name, file_type, saved_path, auth_result.wuban_id, file)
        saved_file_result.append(ret)
    return saved_file_result

async def insert_db(file_new_name, file_type, file_path, user_id, file: UploadFile):
    base_info = {
            "bytes": file.size, #文件大小
            "filename": file.filename, #文件原始名
            "filepath": "/api/cdn/" + str(file_path), # 文件在服务器上的路径
            "object": file_type, # 文件类型
            "source": "custom", # 来源
            "type": file.content_type, # 文件内容类型
            "usage": 1,
            "userId": user_id # 上传用户
    }
    if router.file_upload_prisma_client is None:
        print("db not supported")
        base_info["message"] = "db not supported!"
        return base_info

    # add to db
    result: File = await router.file_upload_prisma_client.db.file.create(
        data= {
            "fileId": file_new_name,
            "userId": user_id,
            "name": file.filename,
            "type": file.content_type,
            "size": file.size,
            "url": file_path,
            "updatedAt": datetime.now()
        }
    )
    base_info["message"] = "File uploaded and processed successfully"
    base_info["_id"] = str(result.id)
    print(result)
    return base_info


def _create_file_name(file: UploadFile):
    """
    生成新文件名
    """
    # 生成UUID作为新的文件名
    file_uuid = str(uuid.uuid4())
    # 获取文件的原始后缀名（例如.txt、.jpg等）
    file_extension = os.path.splitext(file.filename)[-1]
    # 组合成新的文件名（UUID + 原始后缀名）
    return file_uuid + file_extension


def ensure_today_dir():
    current_date = datetime.now().strftime('%Y-%m-%d')
    # FILE_UPLOAD_BASE_DIR
    file_base_dir = os.getenv("FILE_UPLOAD_BASE_DIR")
    if file_base_dir is None:
        raise Exception("FILE_UPLOAD_BASE_DIR is not config, can't upload file.")
    work_dir = os.path.join(file_base_dir, current_date)
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)
    return work_dir, current_date

@router.get(
    "/api/files",
    dependencies=[Depends(combined_auth)],
    tags=["files"]
)
async def get_files(auth_result: CombinedAuthResult = Depends(combined_auth),
                     page:int = 1,
                     size:int = 20):
    return await get_db_files(auth_result, page, size)

@router.get(
    "/api/files/images",
    dependencies=[Depends(combined_auth)],
    tags=["files/images"]
)
async def get_db_files(auth_result: CombinedAuthResult = Depends(combined_auth),
                       page:int = 1,
                       size:int = 20):
    user_id = auth_result.wuban_id
    where = {
        "userId": user_id
    }
    skip = (page - 1) * size
    result = await router.file_upload_prisma_client.db.file.find_many(
        where=where,  # type: ignore
        skip=skip,  # type: ignore
        take=size )
    return list(map(lambda item: transform_file_2_resp(item), result))

def transform_file_2_resp(file):
    return {
        "_id": file.id,
        "file_id": file.fileId,
        "bytes": file.size,
        "createdAt": file.createdAt,
        "filename": file.name,
        "filepath": "/api/cdn/" + str(file.url),
        "source": "custom",
        "type": file.type,
        "updatedAt": file.updatedAt,
        "user": file.userId
    }