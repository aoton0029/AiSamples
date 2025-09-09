import logging

def setup_logger(name: str, log_file: str, level: int = logging.INFO) -> logging.Logger:
    """Loggerの設定を行う関数"""
    handler = logging.FileHandler(log_file)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    
    return logger

# 例: アプリケーション全体のロガーを設定
app_logger = setup_logger('rag_multi_db_system', 'app.log')