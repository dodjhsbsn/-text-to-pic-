import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from PIL import Image, ImageDraw, ImageFont, ImageTk
import threading
import os

class TextToImageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("文字转图片工具")
        self.root.geometry("1400x680")
        
        # 居中窗口
        self.center_window()
        
        # 存储生成的图片对象
        self.generated_image = None
        
        # 当前选择的图片格式
        self.image_format = tk.StringVar(value="PNG")
        
        # 当前选择的分辨率类型
        self.resolution_type = tk.StringVar(value="预设")
        self.preset_resolution = tk.StringVar(value="1920×1080 (Full HD)")
        self.custom_width = tk.StringVar(value="1920")
        self.custom_height = tk.StringVar(value="1080")
        
        # 颜色设置
        self.text_color = (0, 0, 0)  # 默认黑色
        self.bg_color = (255, 255, 255)  # 默认白色
        self.text_color_hex = "#000000"
        self.bg_color_hex = "#FFFFFF"
        self.bg_transparent = False
        
        # 字体大小设置
        self.font_size = tk.IntVar(value=40)
        
        # 预览相关
        self.preview_canvas = None
        self.preview_image_tk = None
        self.preview_update_timer = None
        
        # 设置UI
        self.setup_ui()
    
    def center_window(self):
        """居中显示窗口"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_ui(self):
        """创建所有UI组件"""
        # 创建主布局容器（左右分割）
        self.setup_main_layout()
    
    def setup_main_layout(self):
        """设置主布局（左右分割）"""
        # 创建主容器Frame
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # 左侧容器
        left_frame = tk.Frame(main_container)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 右侧预览容器
        right_frame = tk.Frame(main_container, width=600)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10, pady=10)
        right_frame.pack_propagate(False)  # 保持固定宽度
        
        # 设置左侧UI
        self.setup_left_ui(left_frame)
        
        # 设置右侧预览UI
        self.setup_preview_area(right_frame)
        
        # 初始化预览（延迟执行，确保所有组件已创建）
        self.root.after(100, self.update_preview)
    
    def setup_left_ui(self, parent):
        """设置左侧UI组件"""
        # 标题
        title_label = tk.Label(parent, text="文字转图片工具", font=("Arial", 20, "bold"))
        title_label.pack(pady=10)
        
        # 文字输入区域
        input_frame = tk.LabelFrame(parent, text="输入文字", padx=10, pady=10)
        input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.text_input = tk.Text(input_frame, wrap=tk.WORD, font=("Arial", 12), height=10)
        self.text_input.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(self.text_input)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_input.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.text_input.yview)
        
        # 绑定文字输入变化事件，触发预览更新
        self.text_input.bind('<KeyRelease>', lambda e: self.schedule_preview_update())
        self.text_input.bind('<Button-1>', lambda e: self.schedule_preview_update())
        
        # 控制区域
        control_frame = tk.Frame(parent)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 图片格式选择
        format_frame = tk.LabelFrame(control_frame, text="图片格式", padx=10, pady=10)
        format_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        formats = [("JPG", "JPG"), ("PNG", "PNG"), ("BMP", "BMP"), ("GIF", "GIF"), ("WEBP", "WEBP")]
        for text, value in formats:
            rb = tk.Radiobutton(format_frame, text=text, variable=self.image_format, value=value, 
                              command=self.on_image_format_change)
            rb.pack(side=tk.LEFT, padx=5)
        
        # 分辨率选择
        resolution_frame = tk.LabelFrame(control_frame, text="分辨率", padx=10, pady=10)
        resolution_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        preset_resolutions = ["1920×1080 (Full HD)", "1280×720 (HD)", "2560×1440 (2K)", 
                             "3840×2160 (4K)", "800×600 (SVGA)", "1024×768 (XGA)", "自定义"]
        resolution_combo = ttk.Combobox(resolution_frame, textvariable=self.preset_resolution, 
                                       values=preset_resolutions, state="readonly", width=20)
        resolution_combo.pack(side=tk.LEFT, padx=5)
        resolution_combo.bind("<<ComboboxSelected>>", self.on_resolution_change)
        
        # 自定义分辨率输入区域
        self.custom_resolution_frame = tk.Frame(resolution_frame)
        
        width_label = tk.Label(self.custom_resolution_frame, text="宽:")
        width_label.pack(side=tk.LEFT, padx=2)
        width_entry = tk.Entry(self.custom_resolution_frame, textvariable=self.custom_width, width=8)
        width_entry.pack(side=tk.LEFT, padx=2)
        width_entry.bind('<KeyRelease>', lambda e: self.schedule_preview_update())
        
        height_label = tk.Label(self.custom_resolution_frame, text="高:")
        height_label.pack(side=tk.LEFT, padx=2)
        height_entry = tk.Entry(self.custom_resolution_frame, textvariable=self.custom_height, width=8)
        height_entry.pack(side=tk.LEFT, padx=2)
        height_entry.bind('<KeyRelease>', lambda e: self.schedule_preview_update())
        
        # 颜色选择区域
        color_frame = tk.LabelFrame(parent, text="颜色设置", padx=10, pady=10)
        color_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 文字颜色选择
        text_color_frame = tk.Frame(color_frame)
        text_color_frame.pack(side=tk.LEFT, padx=10)
        
        text_color_label = tk.Label(text_color_frame, text="文字颜色:")
        text_color_label.pack(side=tk.LEFT, padx=5)
        
        self.text_color_button = tk.Button(text_color_frame, text="#000000", bg="#000000", fg="white",
                                          command=self.choose_text_color, width=12, height=1)
        self.text_color_button.pack(side=tk.LEFT, padx=5)
        
        # 背景颜色选择
        bg_color_frame = tk.Frame(color_frame)
        bg_color_frame.pack(side=tk.LEFT, padx=10)
        
        bg_color_label = tk.Label(bg_color_frame, text="背景颜色:")
        bg_color_label.pack(side=tk.LEFT, padx=5)
        
        self.bg_color_button = tk.Button(bg_color_frame, text="#FFFFFF", bg="#FFFFFF", fg="black",
                                        command=self.choose_bg_color, width=12, height=1)
        self.bg_color_button.pack(side=tk.LEFT, padx=5)
        
        # 透明背景复选框
        self.bg_transparent_var = tk.BooleanVar(value=False)
        self.bg_transparent_check = tk.Checkbutton(color_frame, text="透明背景 (仅PNG)", 
                                                   variable=self.bg_transparent_var,
                                                   command=self.on_bg_transparent_change)
        self.bg_transparent_check.pack(side=tk.LEFT, padx=10)
        
        # 文字大小选择区域
        font_frame = tk.LabelFrame(parent, text="文字设置", padx=10, pady=10)
        font_frame.pack(fill=tk.X, padx=10, pady=5)
        
        font_size_label = tk.Label(font_frame, text="文字大小:")
        font_size_label.pack(side=tk.LEFT, padx=5)
        
        font_size_spinbox = tk.Spinbox(font_frame, from_=10, to=200, textvariable=self.font_size,
                                       width=10, command=self.on_font_size_change)
        font_size_spinbox.pack(side=tk.LEFT, padx=5)
        font_size_spinbox.bind('<KeyRelease>', lambda e: self.on_font_size_change())
        
        font_size_unit_label = tk.Label(font_frame, text="像素")
        font_size_unit_label.pack(side=tk.LEFT, padx=5)
        
        # 操作区域
        action_frame = tk.Frame(parent)
        action_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 转换按钮
        self.convert_button = tk.Button(action_frame, text="转换", command=self.on_convert_click, 
                                       font=("Arial", 12), bg="#4CAF50", fg="white", padx=20, pady=5)
        self.convert_button.pack(side=tk.LEFT, padx=5)
        
        # 进度条
        self.progress_bar = ttk.Progressbar(action_frame, mode='determinate', length=300)
        self.progress_bar.pack(side=tk.LEFT, padx=10)
        self.progress_bar.pack_forget()  # 初始隐藏
        
        # 保存按钮
        self.save_button = tk.Button(action_frame, text="保存", command=self.on_save_click, 
                                    font=("Arial", 12), bg="#2196F3", fg="white", padx=20, pady=5, 
                                    state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        # 状态标签
        self.status_label = tk.Label(parent, text="请输入文字并选择格式和分辨率，然后点击转换", 
                                     fg="gray", font=("Arial", 10))
        self.status_label.pack(pady=5)
    
    def setup_preview_area(self, parent):
        """设置右侧预览区域"""
        # 预览标题
        preview_title = tk.Label(parent, text="预览", font=("Arial", 16, "bold"))
        preview_title.pack(pady=10)
        
        # 预览Canvas
        preview_frame = tk.Frame(parent, relief=tk.SUNKEN, borderwidth=2)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.preview_canvas = tk.Canvas(preview_frame, width=580, height=400, bg="white")
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 分辨率信息标签
        self.resolution_label = tk.Label(parent, text="分辨率: 1920 × 1080", 
                                         fg="gray", font=("Arial", 10))
        self.resolution_label.pack(pady=5)
    
    def on_font_size_change(self, event=None):
        """字体大小变化处理"""
        # 延迟更新预览（防抖）
        self.schedule_preview_update()
    
    def schedule_preview_update(self, delay=300):
        """安排预览更新（防抖）"""
        if self.preview_update_timer:
            self.root.after_cancel(self.preview_update_timer)
        self.preview_update_timer = self.root.after(delay, self.update_preview)
    
    def generate_preview_image(self):
        """生成预览图片"""
        try:
            # 获取当前设置
            text = self.text_input.get("1.0", tk.END).strip()
            if not text:
                return None
            
            try:
                width, height = self.get_resolution()
            except:
                return None
            
            font_size = self.font_size.get()
            format_type = self.image_format.get()
            text_color = self.text_color
            bg_color = self.bg_color
            
            # 验证颜色值
            if not isinstance(text_color, (tuple, list)) or len(text_color) < 3:
                text_color = (0, 0, 0)
            if not isinstance(bg_color, (tuple, list)) or len(bg_color) < 3:
                bg_color = (255, 255, 255)
            
            bg_transparent = (format_type == "PNG" and self.bg_transparent_var.get())
            
            # 预览区域大小
            preview_width = 580
            preview_height = 400
            
            # 计算缩放比例（保持宽高比，留10%边距）
            scale = min(preview_width / width, preview_height / height) * 0.9
            
            # 计算预览图尺寸
            preview_img_width = int(width * scale)
            preview_img_height = int(height * scale)
            
            # 按比例缩放字体大小
            preview_font_size = int(font_size * scale)
            preview_font_size = max(8, min(preview_font_size, 100))  # 限制范围
            
            # 生成预览图（使用缩小后的分辨率和字体）
            if format_type == "PNG" and bg_transparent:
                preview_image = Image.new("RGBA", (preview_img_width, preview_img_height), (0, 0, 0, 0))
            elif format_type == "PNG":
                preview_image = Image.new("RGBA", (preview_img_width, preview_img_height), (*bg_color, 255))
            else:
                preview_image = Image.new("RGB", (preview_img_width, preview_img_height), bg_color)
            
            draw = ImageDraw.Draw(preview_image)
            
            # 加载字体
            try:
                if os.name == 'nt':
                    font_path = "C:/Windows/Fonts/msyh.ttc"
                    if os.path.exists(font_path):
                        font = ImageFont.truetype(font_path, preview_font_size)
                    else:
                        font = ImageFont.load_default()
                else:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", preview_font_size)
            except:
                font = ImageFont.load_default()
            
            # 计算文字位置（简化版，不做复杂的换行处理）
            lines = text.split('\n')
            line_height = font.getbbox('A')[3] - font.getbbox('A')[1] if hasattr(font, 'getbbox') else preview_font_size + 5
            total_height = len(lines) * line_height * 1.2
            start_y = (preview_img_height - total_height) / 2
            
            # 根据图片模式确定文字颜色格式
            if preview_image.mode == "RGBA":
                text_color_rgba = (*text_color[:3], 255)
            else:
                text_color_rgba = text_color[:3]
            
            # 绘制文字（简化版）
            for i, line in enumerate(lines[:10]):  # 最多显示10行
                if line.strip():
                    bbox = draw.textbbox((0, 0), line, font=font) if hasattr(draw, 'textbbox') else draw.textsize(line, font=font)
                    text_width = bbox[2] - bbox[0] if isinstance(bbox, tuple) and len(bbox) == 4 else bbox[0]
                    text_x = (preview_img_width - text_width) / 2
                    y = start_y + i * line_height * 1.2
                    
                    # 如果文字太长，截断
                    if text_width > preview_img_width - 20:
                        # 简单截断处理
                        chars_per_line = int(len(line) * (preview_img_width - 20) / text_width)
                        line = line[:chars_per_line] + "..."
                        bbox = draw.textbbox((0, 0), line, font=font) if hasattr(draw, 'textbbox') else draw.textsize(line, font=font)
                        text_width = bbox[2] - bbox[0] if isinstance(bbox, tuple) and len(bbox) == 4 else bbox[0]
                        text_x = (preview_img_width - text_width) / 2
                    
                    draw.text((text_x, y), line, fill=text_color_rgba, font=font)
            
            return preview_image
            
        except Exception as e:
            print(f"预览生成错误: {e}")
            return None
    
    def update_preview(self):
        """更新预览显示"""
        try:
            # 生成预览图
            preview_image = self.generate_preview_image()
            
            if preview_image:
                # 转换为tkinter可用的图像
                self.preview_image_tk = ImageTk.PhotoImage(preview_image)
                
                # 清除Canvas
                self.preview_canvas.delete("all")
                
                # 计算居中位置
                canvas_width = self.preview_canvas.winfo_width()
                canvas_height = self.preview_canvas.winfo_height()
                if canvas_width <= 1 or canvas_height <= 1:
                    canvas_width = 580
                    canvas_height = 400
                
                x = (canvas_width - preview_image.width) // 2
                y = (canvas_height - preview_image.height) // 2
                
                # 绘制预览图
                self.preview_canvas.create_image(x, y, anchor=tk.NW, image=self.preview_image_tk)
                
                # 更新分辨率信息
                try:
                    width, height = self.get_resolution()
                    self.resolution_label.config(text=f"分辨率: {width} × {height}")
                except:
                    pass
            else:
                # 显示占位提示
                self.preview_canvas.delete("all")
                self.preview_canvas.create_text(290, 200, text="请输入文字以查看预览", 
                                               fill="gray", font=("Arial", 14))
                self.resolution_label.config(text="分辨率: -- × --")
                
        except Exception as e:
            print(f"预览更新错误: {e}")
            self.preview_canvas.delete("all")
            self.preview_canvas.create_text(290, 200, text="预览生成失败", 
                                           fill="red", font=("Arial", 12))
    
    def on_resolution_change(self, event=None):
        """处理分辨率选择变化"""
        selected = self.preset_resolution.get()
        if selected == "自定义":
            self.custom_resolution_frame.pack(side=tk.LEFT, padx=5)
        else:
            self.custom_resolution_frame.pack_forget()
        # 更新预览
        self.schedule_preview_update()
    
    def rgb_to_hex(self, rgb):
        """将RGB元组转换为十六进制字符串"""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}".upper()
    
    def choose_text_color(self):
        """选择文字颜色"""
        # 确保当前颜色值正确
        initial_rgb = tuple(map(int, self.text_color[:3])) if isinstance(self.text_color, (tuple, list)) and len(self.text_color) >= 3 else (0, 0, 0)
        
        # 确保十六进制字符串格式正确（必须是大写）
        initial_hex = self.rgb_to_hex(initial_rgb)
        self.text_color_hex = initial_hex  # 同步更新十六进制值
        
        # 使用十六进制字符串格式作为初始颜色（确保格式正确）
        color = colorchooser.askcolor(initialcolor=initial_hex, title="选择文字颜色")
        if color and color[0] is not None:  # 用户没有取消
            try:
                rgb = tuple(map(int, color[0]))
                self.text_color = rgb
                self.text_color_hex = color[1] if color[1] else self.rgb_to_hex(rgb)
                self.update_color_preview()
                # 更新预览
                self.schedule_preview_update()
                print(f"文字颜色已更新: RGB={rgb}, HEX={self.text_color_hex}")
            except Exception as e:
                print(f"颜色选择错误: {e}")
                messagebox.showerror("错误", f"颜色选择失败: {e}")
    
    def choose_bg_color(self):
        """选择背景颜色"""
        # 确保当前颜色值正确
        initial_rgb = tuple(map(int, self.bg_color[:3])) if isinstance(self.bg_color, (tuple, list)) and len(self.bg_color) >= 3 else (255, 255, 255)
        
        # 确保十六进制字符串格式正确（必须是大写）
        initial_hex = self.rgb_to_hex(initial_rgb)
        self.bg_color_hex = initial_hex  # 同步更新十六进制值
        
        # 使用十六进制字符串格式作为初始颜色（确保格式正确）
        color = colorchooser.askcolor(initialcolor=initial_hex, title="选择背景颜色")
        if color and color[0] is not None:  # 用户没有取消
            try:
                rgb = tuple(map(int, color[0]))
                self.bg_color = rgb
                self.bg_color_hex = color[1] if color[1] else self.rgb_to_hex(rgb)
                self.update_color_preview()
                # 更新预览
                self.schedule_preview_update()
                print(f"背景颜色已更新: RGB={rgb}, HEX={self.bg_color_hex}")
            except Exception as e:
                print(f"背景颜色选择错误: {e}")
                messagebox.showerror("错误", f"背景颜色选择失败: {e}")
    
    def update_color_preview(self):
        """更新颜色预览按钮"""
        self.text_color_button.config(text=self.text_color_hex, bg=self.text_color_hex,
                                     fg="white" if sum(self.text_color) < 382 else "black")
        if not self.bg_transparent_var.get():
            self.bg_color_button.config(text=self.bg_color_hex, bg=self.bg_color_hex,
                                       fg="white" if sum(self.bg_color) < 382 else "black")
    
    def on_bg_transparent_change(self):
        """处理透明背景复选框变化"""
        self.bg_transparent = self.bg_transparent_var.get()
        if self.bg_transparent:
            self.bg_color_button.config(state=tk.DISABLED)
        else:
            self.bg_color_button.config(state=tk.NORMAL)
            self.update_color_preview()
        # 更新预览
        self.schedule_preview_update()
    
    def on_image_format_change(self):
        """处理图片格式变化"""
        format_type = self.image_format.get()
        if format_type == "PNG":
            self.bg_transparent_check.config(state=tk.NORMAL)
        else:
            # 非PNG格式时禁用透明背景选项
            self.bg_transparent_var.set(False)
            self.bg_transparent = False
            self.bg_transparent_check.config(state=tk.DISABLED)
            self.bg_color_button.config(state=tk.NORMAL)
            self.update_color_preview()
        # 更新预览
        self.schedule_preview_update()
    
    def get_resolution(self):
        """获取当前选择的分辨率，返回(width, height)元组"""
        selected = self.preset_resolution.get()
        if selected == "自定义":
            try:
                width = int(self.custom_width.get())
                height = int(self.custom_height.get())
                # 验证分辨率范围
                if width < 100 or width > 10000 or height < 100 or height > 10000:
                    raise ValueError("分辨率超出有效范围")
                return (width, height)
            except ValueError as e:
                raise ValueError(f"无效的自定义分辨率: {e}")
        else:
            # 解析预设分辨率
            parts = selected.split("×")
            if len(parts) == 2:
                width = int(parts[0].strip())
                height = int(parts[1].split()[0].strip())
                return (width, height)
            else:
                raise ValueError("无法解析预设分辨率")
    
    def validate_inputs(self):
        """验证用户输入"""
        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            raise ValueError("请输入要转换的文字")
        
        try:
            width, height = self.get_resolution()
        except ValueError as e:
            raise ValueError(str(e))
        
        return text, width, height
    
    def update_progress(self, value):
        """线程安全的进度条更新"""
        self.root.after(0, lambda: self.progress_bar.config(value=value))
        self.root.after(0, lambda: self.status_label.config(text=f"转换中... {int(value)}%"))
    
    def generate_text_image(self, text, width, height, format_type, text_color, bg_color, bg_transparent, font_size_param, progress_callback):
        """生成文字图片"""
        print(f"生成图片 - 文字长度: {len(text)}, 分辨率: {width}x{height}, 字体大小: {font_size_param}, 文字颜色: {text_color}, 背景颜色: {bg_color}")
        
        # 进度: 0-30% - 准备图片画布
        progress_callback(10)
        
        # 验证颜色值
        if not isinstance(text_color, (tuple, list)) or len(text_color) < 3:
            print(f"警告: 文字颜色格式错误: {text_color}，使用默认黑色")
            text_color = (0, 0, 0)
        if not isinstance(bg_color, (tuple, list)) or len(bg_color) < 3:
            print(f"警告: 背景颜色格式错误: {bg_color}，使用默认白色")
            bg_color = (255, 255, 255)
        
        # 创建图片（根据背景颜色和透明选项）
        if format_type == "PNG" and bg_transparent:
            # PNG格式且选择透明背景
            image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        elif format_type == "PNG":
            # PNG格式但不透明，使用RGBA模式
            image = Image.new("RGBA", (width, height), (*bg_color[:3], 255))
        else:
            # 其他格式使用RGB模式
            image = Image.new("RGB", (width, height), bg_color[:3])
        
        progress_callback(20)
        
        draw = ImageDraw.Draw(image)
        
        # 进度: 30-60% - 计算文字布局
        progress_callback(35)
        
        # 使用指定的字体大小
        font_size = int(font_size_param)
        font_size = max(8, min(font_size, 300))  # 限制字体大小范围
        
        # 尝试使用系统字体，如果失败则使用默认字体
        font = None
        try:
            # Windows系统字体路径
            if os.name == 'nt':
                font_path = "C:/Windows/Fonts/msyh.ttc"  # 微软雅黑
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, font_size)
                    print(f"加载字体成功: {font_path}, 大小: {font_size}")
                else:
                    font = ImageFont.load_default()
                    print(f"字体文件不存在，使用默认字体")
            else:
                # Linux/Mac系统字体
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
                    print(f"加载字体成功: DejaVuSans, 大小: {font_size}")
                except:
                    font = ImageFont.load_default()
                    print(f"字体加载失败，使用默认字体")
        except Exception as e:
            font = ImageFont.load_default()
            print(f"字体加载异常: {e}，使用默认字体")
        
        if font is None:
            font = ImageFont.load_default()
            print("使用默认字体")
        
        progress_callback(50)
        
        # 处理多行文字
        lines = [line.strip() for line in text.split('\n') if line.strip()]  # 过滤空行
        if not lines:
            lines = [text.strip()] if text.strip() else [" "]  # 如果全是空行，至少显示一个空格
        
        # 计算行高（使用更可靠的方法）
        try:
            if hasattr(font, 'getbbox'):
                bbox = font.getbbox('Ag')
                line_height = bbox[3] - bbox[1]
            elif hasattr(font, 'getsize'):
                line_height = font.getsize('Ag')[1]
            else:
                line_height = font_size + 10  # 默认值
        except:
            line_height = font_size + 10
        
        # 计算总高度和起始位置，确保在图片范围内
        spacing = 1.3
        total_height = len(lines) * line_height * spacing
        start_y = max(20, (height - total_height) / 2)  # 至少距离顶部20像素
        
        print(f"文字行数: {len(lines)}, 行高: {line_height}, 总高度: {total_height}, 起始Y: {start_y}")
        
        progress_callback(60)
        
        # 进度: 60-90% - 渲染文字
        # 根据图片模式确定文字颜色格式
        if image.mode == "RGBA":
            text_color_rgba = (*text_color[:3], 255)
        else:
            text_color_rgba = text_color[:3]
        
        print(f"使用文字颜色: {text_color_rgba}")
        
        # 简化渲染逻辑，确保每行文字都被绘制
        for i, line in enumerate(lines):
            if not line.strip():
                continue
                
            y = start_y + i * line_height * spacing
            
            # 确保y坐标在图片范围内
            if y < 0 or y >= height:
                print(f"警告: 行{i}的y坐标{y}超出范围，跳过")
                continue
            
            try:
                # 获取文字宽度
                if hasattr(draw, 'textbbox'):
                    bbox = draw.textbbox((0, 0), line, font=font)
                    text_width = bbox[2] - bbox[0]
                elif hasattr(draw, 'textsize'):
                    text_width = draw.textsize(line, font=font)[0]
                else:
                    text_width = len(line) * font_size // 2  # 粗略估算
                
                # 如果文字太宽，进行简单截断
                max_width = width - 40
                if text_width > max_width:
                    # 计算可以显示的字符数
                    chars = int(len(line) * max_width / text_width * 0.9)
                    line = line[:chars] + "..."
                    if hasattr(draw, 'textbbox'):
                        bbox = draw.textbbox((0, 0), line, font=font)
                        text_width = bbox[2] - bbox[0]
                    elif hasattr(draw, 'textsize'):
                        text_width = draw.textsize(line, font=font)[0]
                    else:
                        text_width = len(line) * font_size // 2
                
                # 居中绘制文字
                text_x = max(20, (width - text_width) / 2)  # 至少距离左边20像素
                
                draw.text((text_x, y), line, fill=text_color_rgba, font=font)
                print(f"绘制文字行{i}: '{line[:20]}...' 位置: ({text_x}, {y})")
                
            except Exception as e:
                print(f"绘制行{i}时出错: {e}")
                # 即使出错也尝试简单绘制
                try:
                    text_x = max(20, (width - len(line) * font_size // 2) / 2)
                    draw.text((text_x, y), line, fill=text_color_rgba, font=font)
                except:
                    pass
            
            progress_callback(60 + (i + 1) / len(lines) * 30)
        
        progress_callback(90)
        
        # 进度: 90-100% - 完成处理
        progress_callback(100)
        
        print("图片生成完成")
        return image
    
    def convert_thread(self):
        """后台转换线程函数"""
        try:
            # 验证输入
            text, width, height = self.validate_inputs()
            
            # 获取选择的格式
            format_type = self.image_format.get()
            
            # 获取颜色设置
            text_color = self.text_color
            bg_color = self.bg_color
            # 判断是否使用透明背景（需要是PNG格式且选中了透明背景选项）
            bg_transparent = (format_type == "PNG" and self.bg_transparent_var.get())
            
            # 获取字体大小
            font_size = self.font_size.get()
            
            # 验证颜色值
            print(f"转换线程 - 文字颜色: {text_color}, 背景颜色: {bg_color}, 字体大小: {font_size}")
            if not isinstance(text_color, (tuple, list)) or len(text_color) < 3:
                print(f"警告: 文字颜色格式错误，重置为黑色")
                text_color = (0, 0, 0)
            if not isinstance(bg_color, (tuple, list)) or len(bg_color) < 3:
                print(f"警告: 背景颜色格式错误，重置为白色")
                bg_color = (255, 255, 255)
            
            # 生成图片
            self.generated_image = self.generate_text_image(text, width, height, format_type, 
                                                           text_color, bg_color, bg_transparent, 
                                                           font_size, self.update_progress)
            
            # 转换完成后更新UI
            self.root.after(0, self.on_convert_complete)
            
        except Exception as e:
            self.root.after(0, lambda: self.on_convert_error(str(e)))
    
    def on_convert_complete(self):
        """转换完成后的UI更新"""
        self.progress_bar.pack_forget()
        self.save_button.config(state=tk.NORMAL)
        self.convert_button.config(state=tk.NORMAL)
        self.status_label.config(text="转换完成！请点击保存按钮保存图片", fg="green")
    
    def on_convert_error(self, error_msg):
        """转换出错时的处理"""
        self.progress_bar.pack_forget()
        self.convert_button.config(state=tk.NORMAL)
        self.status_label.config(text=f"转换失败: {error_msg}", fg="red")
        messagebox.showerror("错误", error_msg)
    
    def on_convert_click(self):
        """转换按钮点击事件处理"""
        # 禁用转换按钮
        self.convert_button.config(state=tk.DISABLED)
        
        # 隐藏保存按钮
        self.save_button.config(state=tk.DISABLED)
        
        # 显示进度条
        self.progress_bar.pack(side=tk.LEFT, padx=10)
        self.progress_bar.config(value=0)
        
        # 更新状态
        self.status_label.config(text="正在转换...", fg="blue")
        
        # 启动后台转换线程
        thread = threading.Thread(target=self.convert_thread, daemon=True)
        thread.start()
    
    def on_save_click(self):
        """保存按钮点击事件处理"""
        if self.generated_image is None:
            messagebox.showwarning("警告", "没有可保存的图片")
            return
        
        # 获取文件扩展名
        format_map = {
            "JPG": ".jpg",
            "PNG": ".png",
            "BMP": ".bmp",
            "GIF": ".gif",
            "WEBP": ".webp"
        }
        ext = format_map.get(self.image_format.get(), ".png")
        
        # 打开文件保存对话框
        filename = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=[
                (f"{self.image_format.get()} files", f"*{ext}"),
                ("All files", "*.*")
            ],
            title="保存图片"
        )
        
        if filename:
            try:
                # 根据格式保存图片
                format_type = self.image_format.get()
                if format_type == "JPG":
                    # JPG不支持透明背景，需要转换为RGB
                    if self.generated_image.mode == "RGBA":
                        # 使用当前选择的背景颜色作为JPG背景
                        rgb_image = Image.new("RGB", self.generated_image.size, self.bg_color)
                        rgb_image.paste(self.generated_image, mask=self.generated_image.split()[3])
                        rgb_image.save(filename, "JPEG", quality=95)
                    else:
                        self.generated_image.save(filename, "JPEG", quality=95)
                else:
                    self.generated_image.save(filename, format_type)
                
                # 显示成功消息
                self.status_label.config(text=f"图片已保存到: {filename}", fg="green")
                messagebox.showinfo("成功", f"图片已成功保存到:\n{filename}")
                
                # 重置UI状态
                self.save_button.config(state=tk.DISABLED)
                self.progress_bar.pack_forget()
                self.generated_image = None
                
            except Exception as e:
                error_msg = f"保存失败: {str(e)}"
                self.status_label.config(text=error_msg, fg="red")
                messagebox.showerror("错误", error_msg)

def main():
    root = tk.Tk()
    app = TextToImageApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

