"""MoMo adapter — gating chưa-cấu-hình + chữ ký IPN + resolve org. (Chưa có merchant thật.)"""

from __future__ import annotations

import uuid

from app_api import billing, config


def test_momo_topup_unconfigured_400(client, user):
    # server test KHÔNG set MoMo → cổng momo phải báo lỗi cấu hình (400), không crash.
    r = client.post("/v1/billing/topup", headers=user["headers"],
                    json={"pack_id": "starter", "provider": "momo"})
    assert r.status_code == 400
    assert "MoMo" in r.json()["detail"]


def test_momo_signature_and_reconcile(monkeypatch):
    # Bơm cấu hình MoMo giả để kiểm tra logic chữ ký + đối soát (không gọi mạng).
    monkeypatch.setattr(config, "MOMO_PARTNER_CODE", "MOMOTEST")
    monkeypatch.setattr(config, "MOMO_ACCESS_KEY", "accesskey123")
    monkeypatch.setattr(config, "MOMO_SECRET_KEY", "secretkey123")

    org = uuid.uuid4()
    order_id = org.hex + uuid.uuid4().hex[:8]
    p = {
        "amount": "100000", "extraData": "", "message": "Successful.",
        "orderId": order_id, "orderInfo": "Nap credit", "orderType": "momo_wallet",
        "partnerCode": "MOMOTEST", "payType": "qr", "requestId": "rq1",
        "responseTime": "1700000000000", "resultCode": "0", "transId": "999",
    }
    raw = (
        f"accessKey={config.MOMO_ACCESS_KEY}&amount={p['amount']}&extraData={p['extraData']}"
        f"&message={p['message']}&orderId={p['orderId']}&orderInfo={p['orderInfo']}"
        f"&orderType={p['orderType']}&partnerCode={p['partnerCode']}&payType={p['payType']}"
        f"&requestId={p['requestId']}&responseTime={p['responseTime']}&resultCode={p['resultCode']}"
        f"&transId={p['transId']}"
    )
    p["signature"] = billing._momo_sign(raw)

    ok, oid = billing.verify_momo_ipn(p)
    assert ok is True and oid == order_id
    # org resolve được từ orderId
    assert billing.org_from_momo_orderid(order_id) == str(org)

    # chữ ký sai → reject
    bad = dict(p, signature="deadbeef")
    assert billing.verify_momo_ipn(bad)[0] is False
    # chưa thanh toán (resultCode != 0) → reject dù chữ ký đúng
    p2 = dict(p, resultCode="1")
    raw2 = raw.replace("resultCode=0", "resultCode=1")
    p2["signature"] = billing._momo_sign(raw2)
    assert billing.verify_momo_ipn(p2)[0] is False
