"""Client LLM GIẢ LẬP — test vòng lặp 2 agent offline, không cần API key.

- role="copywriter": luôn trả một kịch bản JSON hợp lệ (cải thiện nhẹ theo feedback).
- role="critic": lần đầu chấm thấp (<ngưỡng) để kích hoạt 1 vòng sửa, sau đó chấm đạt.
"""

from __future__ import annotations

import json

from module2_brain.llm.base import BaseLLMClient


class FakeLLMClient(BaseLLMClient):
    def __init__(self, role: str) -> None:
        self.role = role
        self.name = f"fake_{role}"
        self._calls = 0

    async def complete(self, system: str, prompt: str) -> str:
        self._calls += 1
        if self.role == "copywriter":
            revised = "đã chỉnh theo góp ý" if "FEEDBACK" in prompt else "bản đầu"
            return json.dumps(
                {
                    "hook_text": f"Bạn vẫn đang dọn nhà kiểu cũ? ({revised})",
                    "painpoint_text": "Hút bụi bằng tay vừa mỏi vừa không sạch khe kẽ.",
                    "solution_text": "Máy hút bụi không dây này hút sạch trong 10 phút.",
                    "cta_text": "Nhấn vào link để xem ưu đãi hôm nay!",
                    "bg_video_keywords": ["dọn nhà", "máy hút bụi", "sofa"],
                },
                ensure_ascii=False,
            )
        if self.role == "compliance":
            return json.dumps({"safe": True, "violations": [], "must_fix": []}, ensure_ascii=False)
        # critic: thấp -> cao để kiểm tra vòng lặp
        score = 7.0 if self._calls == 1 else 9.2
        return json.dumps(
            {"score": score, "feedback": "Hook chưa đủ giật, nêu rõ lợi ích ngay câu đầu."},
            ensure_ascii=False,
        )
