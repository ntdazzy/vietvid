"""V8 Video Engine — Plan C: Gemini Image + Seedance PiAPI + local compose/QA.

Pipeline: analyzer → director → image_stage → video_stage → voice → compose → qa.
Mọi provider trả phí đi qua budget gate (bảng provider_ledger, fail-closed).
"""
