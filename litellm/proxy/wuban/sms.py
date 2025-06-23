from fastapi import APIRouter, status, Depends

from litellm.proxy.wuban.exceptions import ErrorCode, BusinessError
from litellm.proxy.wuban.user import Response, SMSCodeRequest, UserService, TokenResponse, SMSVerifyRequest, UserInfo
from litellm.proxy.wuban.wuban_auth_service import combined_auth, CombinedAuthResult

router = APIRouter(tags=["短信服务"])

@router.post(
    "/api/sms/code",
    summary="发送验证码",
    response_model=Response[dict],
)
async def send_verification_code(request: SMSCodeRequest):
    """发送手机验证码"""
    try:
        success = await UserService.send_sms_code(request.phone)
        if not success:
            raise BusinessError(ErrorCode.SMS_SEND_FAILED)
    except BusinessError as e:
        return Response.error(e.error_code.code, e.detail)

    return Response.success(
        data={"phone": request.phone},
        message= success["message"]
    )

@router.post(
    "/api/sms/verify",
    summary="验证码登录",
    response_model=Response[TokenResponse]
)
async def verify_code(request: SMSVerifyRequest):
    """验证码登录"""
    try:
        result = await UserService.verify_sms_code(request.phone, request.code)
    except BusinessError as e:
        return Response.error(e.error_code.code, e.detail)
    return Response.success(
        data=TokenResponse(
            token=result["token"],
            token_type="bearer",
            user=result["user"],
        ),
        message="Login success"
    )

