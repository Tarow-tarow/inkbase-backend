from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import connections
from django.db.utils import OperationalError

@api_view(["GET"])
def health(request):
    """
    シンプルなヘルスチェック:
    - Django が動いているか
    - DB(PostgreSQL/RDS) に接続できるか
    """
    db_status = "ok"
    try:
        conn = connections["default"]
        conn.cursor()
    except OperationalError:
        db_status = "error"

    return Response({
        "status": "ok",
        "db": db_status,
    })
