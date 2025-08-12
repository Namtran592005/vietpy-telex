# VietPy Telex

VietPy Telex là một bộ gõ tiếng Việt Telex gọn nhẹ, mã nguồn mở, được xây dựng bằng Python và PyQt6. Chương trình được thiết kế với tiêu chí đơn giản, minh bạch và hiệu quả, tập trung vào việc đặt dấu thanh chuẩn xác cho các từ tiếng Việt, bao gồm cả các cụm nguyên âm phức tạp.

## ✨ Tính năng nổi bật

*   **Bộ gõ Telex chuẩn:** Hỗ trợ đầy đủ các quy tắc gõ dấu thanh (sắc, huyền, hỏi, ngã, nặng) và dấu mũ/móc (ă, â, ê, ô, ơ, ư, đ).
*   **Đặt dấu thông minh:** Tự động đặt dấu đúng vị trí trên các cụm nguyên âm dài (ví dụ: "nghĩa", "lại", "khuyến", "hiếu", "cuối").
*   **Mã nguồn mở & Minh bạch:** Toàn bộ mã nguồn được công khai, đảm bảo không có phần mềm độc hại, không thu thập dữ liệu và không quảng cáo.
*   **Giao diện trực quan:** Giao diện người dùng thân thiện, dễ sử dụng với tùy chọn theme sáng/tối (Light/Dark mode).
*   **Tùy chỉnh linh hoạt:**
    *   Phím tắt chuyển đổi nhanh trạng thái gõ (Ctrl+Shift hoặc Alt+Z).
    *   Tự động khởi động cùng hệ thống (chỉ Windows).
    *   Chế độ khởi động im lặng (ẩn cửa sổ khi khởi động).
    *   Âm thanh chuyển đổi trạng thái gõ tùy chỉnh.
*   **Gọn nhẹ và hiệu quả:** Tối ưu để hoạt động mượt mà, không tiêu tốn nhiều tài nguyên hệ thống.


## ⚙️ Hướng dẫn sử dụng cơ bản

Sau khi chạy, VietPy Telex sẽ hiển thị một cửa sổ điều khiển chính và một biểu tượng ở khay hệ thống (System Tray).

*   **Bật/Tắt gõ tiếng Việt:**
    *   Sử dụng nút radio "Tiếng Việt (Bật)" / "Tiếng Anh (Tắt)" trên cửa sổ chính.
    *   **Phím tắt:** Mặc định là `Ctrl + Shift`. Bạn có thể thay đổi thành `Alt + Z` trong cài đặt.
    *   Click chuột trái vào biểu tượng ở khay hệ thống để chuyển đổi nhanh trạng thái.
    *   Click chuột phải vào biểu tượng ở khay hệ thống để mở menu ngữ cảnh.

*   **Quy tắc gõ Telex:**
    *   **Dấu sắc:** `s` (ví dụ: `tieens` -> `tiến`)
    *   **Dấu huyền:** `f` (ví dụ: `tieenf` -> `tiền`)
    *   **Dấu hỏi:** `r` (ví dụ: `tieenr` -> `tiền`)
    *   **Dấu ngã:** `x` (ví dụ: `tieenx` -> `tiễn`)
    *   **Dấu nặng:** `j` (ví dụ: `tieenj` -> `tiện`)
    *   **Chữ có mũ/móc:**
        *   `w`: `aw` -> `ă`, `ow` -> `ơ`, `uw` -> `ư`
        *   `aa`: `aa` -> `â`
        *   `ee`: `ee` -> `ê`
        *   `oo`: `oo` -> `ô`
        *   `dd`: `dd` -> `đ`
    *   **Xóa dấu:** Gõ phím `z` sau từ. Lần đầu xóa dấu thanh, lần hai xóa dấu mũ/móc. (ví dụ: `tiếngz` -> `tien` -> `tieng`)

*   **Cài đặt:** Nhấn nút "Cài đặt..." trên cửa sổ chính để tùy chỉnh phím tắt, chế độ khởi động, theme giao diện và âm thanh.
*   **Đóng ứng dụng:** Nhấn nút "Kết thúc" để thoát hoàn toàn. Nhấn nút "Đóng" hoặc nút [X] trên cửa sổ sẽ thu nhỏ ứng dụng xuống khay hệ thống.

## 🤝 Đóng góp

Mọi đóng góp (pull requests, báo cáo lỗi, đề xuất tính năng) đều được chào đón! Hãy mở một `Issue` hoặc `Pull Request` trên GitHub.
