from minio import Minio
from minio.error import S3Error
from config import Config
import io
from urllib.parse import quote

class MinIOClient:
    """MinIO客户端封装"""
    
    def __init__(self):
        self.client = Minio(
            Config.MINIO_ENDPOINT,
            access_key=Config.MINIO_ACCESS_KEY,
            secret_key=Config.MINIO_SECRET_KEY,
            secure=Config.MINIO_SECURE
        )
        self.bucket_name = Config.MINIO_BUCKET
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """确保bucket存在"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"Created bucket: {self.bucket_name}")
        except S3Error as e:
            print(f"MinIO bucket error: {e}")
    
    def upload_file(self, file_data, object_name, content_type='application/octet-stream'):
        """上传文件"""
        try:
            if isinstance(file_data, bytes):
                file_data = io.BytesIO(file_data)
            
            # 获取文件大小
            file_data.seek(0, 2)
            file_size = file_data.tell()
            file_data.seek(0)
            
            self.client.put_object(
                self.bucket_name,
                object_name,
                file_data,
                file_size,
                content_type=content_type
            )
            
            # 返回永久可用的后端代理地址（非预签名，无过期时间）
            return self.get_file_url(object_name)
        except S3Error as e:
            print(f"MinIO upload error: {e}")
            return None
    
    def get_file_url(self, object_name):
        """
        生成入库与前端使用的永久 URL：仅走本服务 /api/media/ 读 MinIO，不使用预签名直链。
        （S3/MinIO 预签名最长约 7 天，故统一用代理 + Cache-Control 长期缓存。）
        """
        base = (getattr(Config, 'PUBLIC_API_BASE_URL', None) or 'http://127.0.0.1:5000').rstrip('/')
        safe_path = '/'.join(quote(part, safe='') for part in object_name.split('/'))
        return f"{base}/api/media/{safe_path}"
    
    def delete_file(self, object_name):
        """删除文件"""
        try:
            self.client.remove_object(self.bucket_name, object_name)
            return True
        except S3Error as e:
            print(f"MinIO delete error: {e}")
            return False
    
    def download_file(self, object_name):
        """下载文件"""
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            print(f"MinIO download error: {e}")
            return None

# 全局MinIO客户端实例
minio_client = MinIOClient()
