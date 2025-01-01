import os
import yaml
from typing import Dict, List, Tuple
import traceback
from .logger_util import WubanLogger
from litellm import supports_vision, supports_audio_input, supports_audio_output

logger = WubanLogger.get_logger()

class ModelCapabilitiesManager:
    """模型能力管理器"""
    
    def __init__(self):
        self.model_info = {}
        self.load_capabilities()
    
    def load_capabilities(self):
        """加载模型能力配置"""
        try:
            # 获取配置文件路径
            cwd = os.getcwd()
            config_paths = [
                os.path.join(cwd, 'lite_config.yaml'),
                os.getenv('CONFIG_FILE_PATH'),
                '/app/lite_config.yaml',
            ]
            
            # 读取配置文件
            config = None
            for path in config_paths:
                if path and os.path.exists(path):
                    logger.debug(f"Loading model capabilities from: {path}")
                    with open(path, 'r') as f:
                        config = yaml.safe_load(f)
                    break
                    
            if not config:
                logger.warning("No config file found, using empty capabilities")
                return
                
            # 构建模型信息缓存
            for model in config.get('model_list', []):
                model_name = model['model_name']
                model_info = model.get('model_info', {})
                self.model_info[model_name] = model_info
                
            logger.info(f"Loaded model info for {len(self.model_info)} models")
            
        except Exception as e:
            logger.error(f"Error loading model capabilities: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def reload_capabilities(self):
        """重新加载模型能力配置"""
        self.model_info.clear()
        self.load_capabilities()
    
    def check_file_capabilities(self, model_name: str, files: List[Dict]) -> Tuple[List[Dict], List[Dict], str]:
        """
        检查模型的文件处理能力并返回支持和不支持的文件列表
        """
        if not files:
            logger.debug("No files to check capabilities for")
            return [], [], ""
        
        supported_files = []
        unsupported_files = []
        warnings = []
        
        try:
            logger.info(f"Checking file capabilities for model: {model_name}")
            logger.info(f"Files to check: {[f.get('type', 'unknown') for f in files]}")
            
            for file in files:
                file_type = file.get("type", "").split("/")[0]
                logger.debug(f"Checking capability for file type: {file_type}")
                
                # 检查图片处理能力
                if file_type == "image":
                    has_vision = supports_vision(model=model_name)
                    logger.info(f"Model {model_name} vision support: {has_vision}")
                    if has_vision:
                        supported_files.append(file)
                        logger.debug(f"Added image file to supported list: {file.get('filename', 'unknown')}")
                    else:
                        unsupported_files.append(file)
                        warning = f"Model does not support image processing"
                        warnings.append(warning)
                        logger.warning(warning)
                
                # 检查音频处理能力    
                elif file_type == "audio":
                    has_audio = supports_audio_input(model=model_name)
                    logger.info(f"Model {model_name} audio support: {has_audio}")
                    if has_audio:
                        supported_files.append(file)
                        logger.debug(f"Added audio file to supported list: {file.get('filename', 'unknown')}")
                    else:
                        unsupported_files.append(file)
                        warning = f"Model does not support audio processing"
                        warnings.append(warning)
                        logger.warning(warning)
                
                # 对于其他类型的文件，暂时都加入支持列表
                else:
                    supported_files.append(file)
                    logger.debug(f"Added other type file to supported list: {file.get('filename', 'unknown')} ({file.get('type', 'unknown')})")
            
            warning_message = "; ".join(warnings) if warnings else ""
            
            # 添加结果日志
            logger.info(f"File capability check completed for model {model_name}:")
            logger.info(f"- Supported files: {[f.get('type', 'unknown') for f in supported_files]}")
            logger.info(f"- Unsupported files: {[f.get('type', 'unknown') for f in unsupported_files]}")
            logger.info(f"- Warning message: {warning_message}")
            
            return supported_files, unsupported_files, warning_message
            
        except Exception as e:
            error_msg = f"Error checking model capabilities: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")
            return [], files, error_msg
    
    def get_model_info(self, model_name: str) -> Dict:
        """获取指定模型的完整信息"""
        return self.model_info.get(model_name, {})
    
    def get_model_capabilities(self, model_name: str) -> Dict[str, bool]:
        """获取模型的完整能力信息"""
        model_info = self.get_model_info(model_name)
        return {
            "text": "text" in model_info.get('capabilities', []),
            "chat": "chat" in model_info.get('capabilities', []),
            "vision": model_info.get('supports_vision', False),
            "audio": model_info.get('supports_audio', False),
            "file": model_info.get('supports_file', False),
            "stream": "stream" in model_info.get('capabilities', []),
            "function_calling": "function-calling" in model_info.get('capabilities', []),
            "code": any(cap in model_info.get('capabilities', []) 
                       for cap in ["code-completion", "code-generation"])
        }
    
    def list_models_with_capability(self, capability: str) -> List[str]:
        """列出支持指定能力的所有模型"""
        return [
            model_name 
            for model_name, info in self.model_info.items() 
            if capability in info.get('capabilities', [])
        ]
    
    def has_transcription_model(self) -> bool:
        """检查是否配置了音频转写能力"""
        # 只要有 OPENAI_API_KEY 就认为可以使用 Whisper 进行转写
        return bool(os.getenv("OPENAI_API_KEY"))
    
    def check_model_capabilities(self, model_name: str, required_capabilities: List[str]) -> bool:
        """检查模型是否支持所需的能力"""
        model_info = self.get_model_info(model_name)
        model_capabilities = model_info.get('capabilities', [])
        
        return all(cap in model_capabilities for cap in required_capabilities)

# 创建全局单例实例
model_capabilities_manager = ModelCapabilitiesManager() 