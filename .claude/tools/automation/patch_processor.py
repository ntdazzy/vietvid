import os
import re

class SecurityException(Exception):
    """Ngoại lệ dùng khi phát hiện tấn công ghi đè file hệ thống"""
    pass

def normalize_newlines(text):
    """Chuẩn hóa mọi định dạng xuống dòng về \n để tránh lệch byte-level"""
    return text.replace("\r\n", "\n").replace("\r", "\n")

def safe_resolve_path(base_workspace, relative_path):
    """Workspace Jail: Đảm bảo AI không thể dùng '../' để ghi file ra ngoài thư mục làm việc"""
    safe_root = os.path.abspath(base_workspace)
    target_path = os.path.abspath(os.path.join(safe_root, relative_path))
    if not target_path.startswith(safe_root):
        raise SecurityException(f"CẢNH BÁO BẢO MẬT: Phát hiện hành vi Path Traversal nguy hiểm qua đường dẫn: {relative_path}")
    return target_path

def apply_mode_b(file_path, content):
    """Xử lý Mode B: Tạo mới hoặc Ghi đè toàn bộ file"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ [SUCCESS] Mode B applied: {file_path}")
        return True
    except Exception as e:
        print(f"❌ [ERROR] Failed to write file in Mode B {file_path}: {str(e)}")
        return False

def apply_mode_a(file_path, diff_blocks):
    """Xử lý Mode A: Vá đa khối tuần tự bảo vệ Runtime Assertion"""
    if not os.path.exists(file_path):
        print(f"❌ [ERROR] Target file does not exist for Mode A: {file_path}")
        return False
        
    with open(file_path, "r", encoding="utf-8") as f:
        file_content = normalize_newlines(f.read())

    # Khử bẫy Whitespace Drift trên marker của AI
    pattern = r"<<<<<<< SEARCH[ \t]*\n(.*?)\n=======[ \t]*\n(.*?)\n>>>>>>> REPLACE[ \t]*(?=\n|$)"
    matches = re.findall(pattern, normalize_newlines(diff_blocks), re.DOTALL)

    if not matches:
        print(f"⚠️ [WARNING] No valid Diff Blocks found or marker syntax error for: {file_path}")
        return False

    execution_plan = []
    for search_block, replace_block in matches:
        occurrences = file_content.count(search_block)
        if occurrences == 0:
            print(f"❌ [PATCH FAIL] Structural Drift! Search block not found in {file_path}.")
            return False
        elif occurrences > 1:
            print(f"❌ [PATCH FAIL] Ambiguity error! Search block matches {occurrences} places in {file_path}.")
            return False
        execution_plan.append((search_block, replace_block))

    # Thực thi đột biến chuỗi an toàn kết hợp Runtime Validation
    for i, (search_block, replace_block) in enumerate(execution_plan, 1):
        old_content = file_content
        file_content = file_content.replace(search_block, replace_block, 1)
        
        # Bẫy Runtime Assertion: Nếu chuỗi không thay đổi tức là cấu trúc đã bị dịch biến bởi khối phía trước
        if file_content == old_content:
            print(f"❌ [RUNTIME CRITICAL FAIL] Block {i} áp dụng thất bại âm thầm! Ngữ cảnh đã bị phá vỡ bởi khối trước đó trong {file_path}.")
            return False

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(file_content)
    print(f"✅ [SUCCESS] Mode A patches applied securely: {file_path}")
    return True

def process_ai_response(raw_ai_text, workspace_root="."):
    """Bộ bóc tách ranh giới hệ thống bảo mật (Secure Enclosure Token Parser)"""
    raw_ai_text = normalize_newlines(raw_ai_text)
    patch_pattern = r"---START_FILE_PATCH---\n(.*?)\n---END_FILE_PATCH---"
    patches = re.findall(patch_pattern, raw_ai_text, re.DOTALL)
    
    if not patches:
        print("ℹ️ No automated patches found in AI response.")
        return

    for patch in patches:
        file_match = re.search(r"\* Target File:\s*`([^`]+)`", patch)
        type_match = re.search(r"\* Update Type:\s*([A-Z_]+)", patch)
        
        if not file_match or not type_match:
            print("❌ [PARSER ERROR] Missing core metadata headers.")
            continue
            
        raw_file_path = file_match.group(1).strip()
        update_type = type_match.group(1).strip()

        # Áp dụng bộ lọc bảo mật đường dẫn
        try:
            file_path = safe_resolve_path(workspace_root, raw_file_path)
        except SecurityException as se:
            print(str(se))
            continue # Bỏ qua tệp độc hại, tiếp tục xử lý tệp khác trong hàng đợi

        if update_type in ["NEW_FILE", "FULL_OVERWRITE"]:
            # Chiến lược bóc tách kép: Ưu tiên Custom Non-Markdown Tag mới để miễn dịch 100% lỗi lồng code block
            custom_start = "* Content Block:\n---START_RAW_CONTENT---\n"
            custom_end = "\n---END_RAW_CONTENT---"
            
            start_idx = patch.find(custom_start)
            if start_idx != -1:
                payload_zone = patch[start_idx + len(custom_start):]
                end_idx = payload_zone.find(custom_end)
                if end_idx != -1:
                    content = payload_zone[:end_idx]
                    apply_mode_b(file_path, content)
                    continue

            # Fallback tương thích ngược nếu AI dùng định dạng cũ ```text
            fallback_start = "* Content Block:\n```text\n"
            start_idx_fb = patch.find(fallback_start)
            if start_idx_fb != -1:
                payload_zone = patch[start_idx_fb + len(fallback_start):]
                end_idx_fb = payload_zone.rfind("```")
                if end_idx_fb != -1:
                    content = payload_zone[:end_idx_fb].rstrip()
                    apply_mode_b(file_path, content)
                else:
                    print(f"❌ [PARSER ERROR] Core closure tokens (```) missing for {file_path}")
            else:
                print(f"❌ [PARSER ERROR] Could not find structured Content Block opening for {file_path}")
                    
        elif update_type == "MODIFIED":
            apply_mode_a(file_path, patch)