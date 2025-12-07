# eform_api/views/pdf_views.py

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse, Http404

from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from ..models import CustomerConsent


class ConsentPdfView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid):
        # --- 1. 同意データを取得 ---
        try:
            consent = CustomerConsent.objects.select_related("customer").get(uuid=uuid)
        except CustomerConsent.DoesNotExist:
            raise Http404("Consent not found")

        customer = consent.customer

        # --- 2. PDF をメモリ上で生成 ---
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        y = height - 50

        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, y, "タトゥー同意書（控え）")
        y -= 40

        p.setFont("Helvetica", 11)
        p.drawString(50, y, f"氏名: {customer.full_name or ''}")
        y -= 20

        p.drawString(50, y, f"生年月日: {customer.birth_date or ''}")
        y -= 20

        p.drawString(50, y, f"同意日時: {consent.signed_at}")
        y -= 20

        p.drawString(50, y, f"バージョン: {consent.consent_version or ''}")
        y -= 40

        p.drawString(50, y, "※このPDFは自動生成された控えです。")

        p.showPage()
        p.save()

        pdf = buffer.getvalue()
        buffer.close()

        # --- 3. レスポンスとして返す ---
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename=\"consent_{consent.uuid}.pdf\"'
        return response
