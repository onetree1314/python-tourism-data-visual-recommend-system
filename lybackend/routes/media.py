"""MinIO 对象通过后端代理访问，URL 永不过期（不依赖预签名）"""
import mimetypes
from flask import Blueprint, Response, abort
from utils.minio_client import minio_client

media_bp = Blueprint('media', __name__, url_prefix='/api')


@media_bp.route('/media/<path:object_name>')
def serve_media(object_name):
    if not object_name or '..' in object_name:
        abort(404)
    data = minio_client.download_file(object_name)
    if data is None:
        abort(404)
    mime, _ = mimetypes.guess_type(object_name)
    if not mime:
        mime = 'application/octet-stream'
    return Response(
        data,
        mimetype=mime,
        headers={'Cache-Control': 'public, max-age=31536000'},
    )
