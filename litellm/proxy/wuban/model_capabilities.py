import os
import yaml
from typing import Dict, List, Tuple
import traceback
from .logger_util import WubanLogger

logger = WubanLogger.get_logger()

class ModelCapabilitiesManager:
    """模型能力管理器"""
    
    def __init__(self):
        self.capabilities = {}
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
                
            # 构建模型能力缓存
            for model in config.get('model_list', []):
                model_name = model['model_name']
                capabilities = model.get('litellm_params', {}).get('capabilities', [])
                self.capabilities[model_name] = capabilities
                
            logger.info(f"Loaded capabilities for {len(self.capabilities)} models")
            
        except Exception as e:
            logger.error(f"Error loading model capabilities: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def reload_capabilities(self):
        """重新加载模型能力配置"""
        self.capabilities.clear()
        self.load_capabilities()
    
    def check_capabilities(self, model_name: str, files: List[Dict]) -> Tuple[bool, str]:
        """检查模型是否支持文件处理能力"""
        if not files:
            return True, ""
            
        try:
            capabilities = self.capabilities.get(model_name, [])
            logger.info(f"Capabilities for {model_name}: {capabilities}")
            if not capabilities:
                logger.warning(f"No capabilities found for model {model_name}")
                return False, f"Model {model_name} capabilities not configured"
                
            for file in files:
                file_type = file.get("type", "").split("/")[0]
                if file_type not in capabilities:
                    return False, f"Model {model_name} does not support {file_type} input"
                    
            return True, ""
            
        except Exception as e:
            logger.error(f"Error checking model capabilities: {str(e)}")
            return False, str(e)
    
    def get_model_capabilities(self, model_name: str) -> List[str]:
        """获取指定模型的能力列表"""
        return self.capabilities.get(model_name, [])
    
    def list_models_with_capability(self, capability: str) -> List[str]:
        """列出支持指定能力的所有模型"""
        return [
            model_name 
            for model_name, caps in self.capabilities.items() 
            if capability in caps
        ]

# 创建全局单例实例
model_capabilities_manager = ModelCapabilitiesManager() 