from PyQt5.QtWidgets import (QApplication, QComboBox, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QMessageBox, QFrame, QRadioButton, 
                            QButtonGroup, QScrollArea, QStackedWidget, QTextEdit, QLineEdit, QSlider)
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QTimer, QDateTime
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
import os
import json
import requests

from openai import OpenAI
client = OpenAI(api_key="sk-42d27f7d36474c108d648985219ab3c0", base_url="https://api.deepseek.com")


CURRENT_TYPE = None

# 模拟MBTI数据
MBTI_TYPES = ["ISTJ", "ISFJ", "INFJ", "INTJ", "ISTP", "ISFP", "INFP", "INTP",
              "ESTP", "ESFP", "ENFP", "ENTP", "ESTJ", "ESFJ", "ENFJ", "ENTJ"]

MBTI_QUESTIONS = [
    {"question": "在社交场合中，你通常", "options": ["主动与人交谈", "等待别人来找你"]},
    {"question": "你更倾向于", "options": ["关注现实和具体事物", "关注可能性和整体概念"]},
    {"question": "做决定时，你更注重", "options": ["逻辑和客观因素", "情感和人际关系"]},
    {"question": "你喜欢的生活方式是", "options": ["有计划有组织的", "灵活随性的"]}
] * 10  # 重复10次模拟40个问题


class MBTITestPage(QWidget):
    test_completed = pyqtSignal(str)  # 测试完成信号，传递MBTI类型
    
    def __init__(self):
        super().__init__()
        self.current_question = 0
        self.answers = []
        self.init_ui()
        
    def init_ui(self):
        self.setLayout(QVBoxLayout())
        
        # 顶部进度条
        self.progress_label = QLabel("问题 1/40")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("font-size: 14px; color: #555;")
        self.layout().addWidget(self.progress_label)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.layout().addWidget(scroll)
        
        # 问题容器
        container = QWidget()
        scroll.setWidget(container)
        container.setLayout(QVBoxLayout())
        container.layout().setContentsMargins(30, 20, 30, 20)
        
        # 问题标签
        self.question_label = QLabel()
        self.question_label.setWordWrap(True)
        self.question_label.setStyleSheet("font-size: 16px; margin-bottom: 20px;")
        container.layout().addWidget(self.question_label)
        
        # 选项按钮组
        self.button_group = QButtonGroup()
        self.option_buttons = []
        
        for i in range(2):  # 每个问题2个选项
            rb = QRadioButton()
            rb.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
            container.layout().addWidget(rb)
            self.option_buttons.append(rb)
            self.button_group.addButton(rb, i)
        
        # 底部按钮
        btn_container = QWidget()
        btn_container.setLayout(QHBoxLayout())
        self.layout().addWidget(btn_container)
        
        self.prev_btn = QPushButton("上一题")
        self.prev_btn.setStyleSheet("background-color: #95a5a6; color: white;")
        self.prev_btn.clicked.connect(self.prev_question)
        btn_container.layout().addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("下一题")
        self.next_btn.setStyleSheet("background-color: #3498db; color: white;")
        self.next_btn.clicked.connect(self.next_question)
        btn_container.layout().addWidget(self.next_btn)
        
        # 加载第一个问题
        self.load_question(0)
    
    def load_question(self, index):
        self.current_question = index
        question_data = MBTI_QUESTIONS[index]
        
        self.question_label.setText(f"问题 {index + 1}: {question_data['question']}")
        
        self.button_group.setExclusive(False)
        for i, option in enumerate(question_data['options']):
            self.option_buttons[i].setText(option)
        self.button_group.setExclusive(True)

        self.progress_label.setText(f"问题 {index + 1}/{len(MBTI_QUESTIONS)}")
        self.prev_btn.setEnabled(index > 0)
        self.next_btn.setText("完成测试" if index == len(MBTI_QUESTIONS) - 1 else "下一题")

    def prev_question(self):
        if self.current_question > 0:
            self.load_question(self.current_question - 1)

    def next_question(self):
        selected = self.button_group.checkedId()
        if selected == -1:
            QMessageBox.warning(self, "提示", "请选择一个选项")
            return
        
        # 记录答案
        if len(self.answers) > self.current_question:
            self.answers[self.current_question] = selected
        else:
            self.answers.append(selected)
        
        # 检查是否完成
        if self.current_question == len(MBTI_QUESTIONS) - 1:
            self.complete_test()
        else:
            self.load_question(self.current_question + 1)
    
    def complete_test(self):
        # 这里简化处理，随机返回一个MBTI类型
        mbti_type = random.choice(MBTI_TYPES)
        self.test_completed.emit(mbti_type)


class RelaxingPage(QWidget):
    back_to_home = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())

        self.player = QMediaPlayer()
        self.playlist = [
            {"title": "轻音乐 - 呼吸放松", "file": "assets/music/relax1.mp3"},
            {"title": "自然之声 - 海浪", "file": "assets/music/relax2.mp3"},
            {"title": "背景钢琴 - 冥想", "file": "assets/music/relax3.mp3"}
        ]
        self.current_index = 0

        # 标题
        title = QLabel("🎵 放松一下")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        self.layout().addWidget(title)

        # 歌曲选择下拉框
        self.combo = QComboBox()
        self.combo.setFixedWidth(300)
        self.combo.addItems([track["title"] for track in self.playlist])
        self.combo.currentIndexChanged.connect(self.select_track)
        self.layout().addWidget(self.combo, alignment=Qt.AlignCenter)

        # 歌曲名称
        self.track_label = QLabel()
        self.track_label.setAlignment(Qt.AlignCenter)
        self.track_label.setStyleSheet("font-size: 16px; margin-top: 10px;")
        self.layout().addWidget(self.track_label)

        # 播放控制按钮
        btn_row = QHBoxLayout()
        self.prev_btn = QPushButton("⏮️")
        self.play_btn = QPushButton("▶️")
        self.next_btn = QPushButton("⏭️")
        for btn in [self.prev_btn, self.play_btn, self.next_btn]:
            btn.setFixedSize(60, 40)
            btn.setStyleSheet("font-size: 18px; background-color: #3498db; color: white; border-radius: 6px;")
            btn_row.addWidget(btn, alignment=Qt.AlignCenter)
        self.layout().addLayout(btn_row)

        # 播放进度
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.layout().addWidget(self.slider)

        # 时间
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.layout().addWidget(self.time_label)

        # 返回按钮
        self.back_btn = QPushButton("🔙 返回主页")
        self.back_btn.setFixedHeight(40)
        self.back_btn.setStyleSheet("font-size: 14px; background-color: #95a5a6; color: white; border-radius: 6px;")
        self.back_btn.clicked.connect(lambda: self.back_to_home.emit())
        self.layout().addWidget(self.back_btn, alignment=Qt.AlignCenter)

        # 连接事件
        self.prev_btn.clicked.connect(self.play_previous)
        self.play_btn.clicked.connect(self.toggle_play)
        self.next_btn.clicked.connect(self.play_next)
        self.slider.sliderMoved.connect(self.seek_position)
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)

        # 加载第一首
        self.load_track(0)

    def format_time(self, ms):
        s = ms // 1000
        return f"{s//60:02}:{s%60:02}"

    def load_track(self, index):
        track = self.playlist[index]
        self.track_label.setText(f"当前播放：{track['title']}")
        path = os.path.abspath(track["file"])
        if os.path.exists(path):
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
            self.player.play()
            self.play_btn.setText("⏸️")
        else:
            self.track_label.setText(f"❌ 文件不存在: {track['file']}")

    def toggle_play(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.play_btn.setText("▶️")
        else:
            self.player.play()
            self.play_btn.setText("⏸️")

    def play_next(self):
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self.combo.setCurrentIndex(self.current_index)

    def play_previous(self):
        self.current_index = (self.current_index - 1 + len(self.playlist)) % len(self.playlist)
        self.combo.setCurrentIndex(self.current_index)

    def select_track(self, index):
        self.current_index = index
        self.load_track(index)

    def update_position(self, position):
        self.slider.setValue(position)
        duration = self.player.duration()
        self.time_label.setText(f"{self.format_time(position)} / {self.format_time(duration)}")

    def update_duration(self, duration):
        self.slider.setRange(0, duration)

    def seek_position(self, pos):
        self.player.setPosition(pos)


class DoubaoChatWidget(QWidget):
    """豆包API对话窗口"""
    back_to_main = pyqtSignal()  # 添加返回主页面的信号

    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)  # 设置边距
        
        # 标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel(" 智能心理咨询")

        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        
        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(30,30)
        close_btn.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 15px;
                background-color: #e74c3c;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        close_btn.clicked.connect(self.return_to_main)

        
        title_layout.addStretch() 
        title_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)  # 标题居中
        title_layout.addStretch()  # 伸缩空间（让标题真正居中）
        title_layout.addWidget(close_btn)

        
        layout.addLayout(title_layout)
        
        # 对话显示区域
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            background-color: #f0f0f0;
            border-radius: 8px;
            padding: 10px;
            font-size: 14px;
        """)
        layout.addWidget(self.chat_display)
        
        # 输入区域
        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("输入问题，按回车发送...")
        self.message_input.setMinimumHeight(50)
        self.message_input.setStyleSheet("""
            border: 1px solid #ddd;
            border-radius: 25px;
            padding: 8px 15px;
            font-size: 20px;
        """)
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input)
                
        self.send_btn = QPushButton("↑")  # 使用更标准的箭头符号
        self.send_btn.setFixedSize(50, 50)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #07c160;
                color: white;
                border: none;
                border-radius: 25px;
                font-size: 24px;
                font-weight: 900;
                padding-bottom: 12px;  
            }
            QPushButton:hover {
                background-color: #05a14e;
            }
        """)
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)
        
        layout.addLayout(input_layout)
        
        # 初始问候
        self.show_message("豆包助手", "你好！我是智能心理咨询助手，有什么可以帮助你的吗？")
    # 气泡可以显示的版本
    # def show_message(self, sender, message):
    #     """在对话窗口中显示消息，使用微信风格的气泡"""
    #     timestamp = QDateTime.currentDateTime().toString("hh:mm")
        
    #     if sender == "你":
    #         # 用户消息（右对齐）
    #         self.chat_display.append(f"""
    #             <div style="text-align: right; margin: 12px 0;">
    #                 <div style="display: inline-block; text-align: right; margin-right: 12px;">
    #                     <span style="font-size: 13px; color: #666;">{timestamp}</span>
    #                     <div style="display: inline-block; background-color: #07c160; color: white; 
    #                                 border-radius: 20px; padding: 14px 20px; min-height: 42px; margin-top: 6px;
    #                                 width: fit-content; max-width: 75%; word-wrap: break-word; position: relative;
    #                                 font-size: 20px; line-height: 1.4;">  <!-- 字体大小调整为20px -->
    #                         {message}
    #                         <div style="position: absolute; right: -8px; top: 14px; 
    #                                     width: 0; height: 0; border-top: 8px solid transparent; 
    #                                     border-left: 16px solid #07c160; border-bottom: 8px solid transparent;"></div>
    #                     </div>
    #                 </div>
    #                 <img src="path/to/user/avatar.png" style="width: 48px; height: 48px; 
    #                         border-radius: 50%; vertical-align: top;" />
    #             </div>
    #         """)
    #     else:
    #         # AI消息（左对齐）
    #         self.chat_display.append(f"""
    #             <div style="text-align: left; margin: 12px 0;">
    #                 <img src="path/to/ai/avatar.png" style="width: 48px; height: 48px; 
    #                         border-radius: 50%; vertical-align: top;" />
    #                 <div style="display: inline-block; text-align: left; margin-left: 12px;">
    #                     <div style="font-size: 18px; font-weight: bold; color: #333;">{sender}</div>
    #                     <span style="font-size: 13px; color: #666;">{timestamp}</span>
    #                     <div style="display: inline-block; background-color: white; color: #333; 
    #                                 border-radius: 20px; padding: 14px 20px; min-height: 42px; margin-top: 6px;
    #                                 width: fit-content;max-width: 75%; word-wrap: break-word; position: relative;
    #                                 box-shadow: 0 1px 3px rgba(0,0,0,0.15);
    #                                 font-size: 20px; line-height: 1.4;">  <!-- 字体大小调整为20px -->
    #                         {message}
    #                         <div style="position: absolute; left: -8px; top: 14px; 
    #                                     width: 0; height: 0; border-top: 8px solid transparent; 
    #                                     border-right: 16px solid white; border-bottom: 8px solid transparent;"></div>
    #                     </div>
    #                 </div>
    #             </div>
    #         """)

    def show_message(self, sender, message):
        """在对话窗口中显示消息，使用微信风格的气泡"""
        timestamp = QDateTime.currentDateTime().toString("hh:mm")
        
        if sender == "你":
            # 用户消息（右对齐）
            self.chat_display.append(f"""
                <div style="text-align: right; margin: 12px 0; overflow: hidden;">  <!-- 添加overflow:hidden -->
                    <div style="display: inline-block; text-align: right; margin-right: 12px;">
                        <span style="font-size: 13px; color: #666;">{timestamp}</span>
                        <div style="display: inline-block; background-color: #07c160; color: white; 
                                    border-radius: 20px; padding: 14px 20px; margin-top: 6px;
                                    min-width: 40px;  <!-- 最小宽度 -->
                                    max-width: 75%;  <!-- 最大宽度 -->
                                    word-wrap: break-word; position: relative;
                                    font-size: 20px; line-height: 1.4;
                                    box-sizing: border-box;  <!-- 确保内边距包含在尺寸内 -->
                                    vertical-align: top;">  <!-- 垂直对齐顶部 -->
                            {message}
                            <div style="position: absolute; right: -8px; top: 16px;  <!-- 微调位置 -->
                                        width: 0; height: 0; border-top: 8px solid transparent; 
                                        border-left: 16px solid #07c160; border-bottom: 8px solid transparent;"></div>
                        </div>
                    </div>
                    <img src="path/to/user/avatar.png" style="width: 48px; height: 48px; 
                            border-radius: 50%; vertical-align: top; display: inline-block;" />  <!-- 确保图片是内联块 -->
                </div>
            """)
        else:
            # AI消息（左对齐）
            self.chat_display.append(f"""
                <div style="text-align: left; margin: 12px 0; overflow: hidden;">  <!-- 添加overflow:hidden -->
                    <img src="path/to/ai/avatar.png" style="width: 48px; height: 48px; 
                            border-radius: 50%; vertical-align: top; display: inline-block;" />  <!-- 确保图片是内联块 -->
                    <div style="display: inline-block; text-align: left; margin-left: 12px;">
                        <div style="font-size: 18px; font-weight: bold; color: #333;">{sender}</div>
                        <span style="font-size: 13px; color: #666;">{timestamp}</span>
                        <div style="display: inline-block; background-color: white; color: #333; 
                                    border-radius: 20px; padding: 14px 20px; margin-top: 6px;
                                    min-width: 40px;  <!-- 最小宽度 -->
                                    max-width: 75%;  <!-- 最大宽度 -->
                                    word-wrap: break-word; position: relative;
                                    box-shadow: 0 1px 3px rgba(0,0,0,0.15);
                                    font-size: 20px; line-height: 1.4;
                                    box-sizing: border-box;  <!-- 确保内边距包含在尺寸内 -->
                                    vertical-align: top;">  <!-- 垂直对齐顶部 -->
                            {message}
                            <div style="position: absolute; left: -8px; top: 16px;  <!-- 微调位置 -->
                                        width: 0; height: 0; border-top: 8px solid transparent; 
                                        border-right: 16px solid white; border-bottom: 8px solid transparent;"></div>
                        </div>
                    </div>
                </div>
            """)

    def return_to_main(self):
        """发送返回主页面信号"""
        self.back_to_main.emit()
    
    def send_message(self):
        """发送消息到豆包API并获取回复"""
        message = self.message_input.text().strip()
        if not message:
            return
            
        # 显示用户消息
        self.show_message("你", message)
        self.message_input.clear()
        
        # 显示"正在思考"
        self.show_message("豆包助手", "正在思考...")
        
        # 模拟调用豆包API（实际使用时需要替换为真实API调用）
        QTimer.singleShot(1000, lambda: self.get_doubao_response(message))
    
    def get_doubao_response(self, message):
        """模拟从豆包API获取回复"""
        # 这里应该替换为真实的API调用
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                        {"role": "system", "content": "You are a helpful assistant"},
                        {"role": "user", "content": message},
                    ],
            stream=False
        )
        reply_content = response.choices[0].message.content
        self.show_message("豆包助手", reply_content)  # 只显示内容部分


class MentalHealthApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("心理健康助手")
        self.setFixedSize(1000, 600)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # 创建豆包对话窗口
        self.doubao_chat = DoubaoChatWidget()
        self.doubao_chat.back_to_main.connect(lambda: self.stack.setCurrentWidget(self.main_page))  
        
        # 主窗口部件
        self.main_page = self.create_main_page()
        self.stack.addWidget(self.main_page)

        self.mbti_test_page = MBTITestPage()
        self.mbti_test_page.test_completed.connect(self.show_mbti_result)
        self.stack.addWidget(self.mbti_test_page)
        
        self.relaxing_page = RelaxingPage()
        self.relaxing_page.back_to_home.connect(lambda: self.stack.setCurrentWidget(self.main_page))
        self.stack.addWidget(self.relaxing_page)
        
        # 添加豆包对话窗口
        self.stack.addWidget(self.doubao_chat)

        # 结果页面
        self.mbti_result_page = None

    def create_main_page(self):
        page = QWidget()
        layout = QHBoxLayout()
        page.setLayout(layout)
        
        # 左侧图片区域
        left_frame = QFrame()
        left_frame.setFixedWidth(500)
        left_layout = QVBoxLayout()
        left_frame.setLayout(left_layout)
        
        image_label = QLabel()
        image_label.setFixedSize(480, 480)
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setStyleSheet("border: 1px solid #ddd;")
        
        pixmap = QPixmap("mbti-program/asset/mbti-icons/16-personalities.png")
        if not pixmap.isNull():
            pixmap = pixmap.scaled(480, 480, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.setPixmap(pixmap)
        else:
            image_label.setText("图片加载失败")
            image_label.setStyleSheet("color: red; font-size: 14px;")
        
        left_layout.addWidget(image_label)
        layout.addWidget(left_frame)
        
        # 右侧选项区域
        right_frame = QFrame()
        right_layout = QVBoxLayout()
        right_frame.setLayout(right_layout)
        
        title = QLabel("您的心理健康助手")
        title.setFont(QFont("Microsoft YaHei", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            color: #2c3e50; 
            margin-bottom: 30px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
        """)
        right_layout.addWidget(title)
        
        # 功能按钮
        buttons = [
            ("MBTI性格自测", self.start_mbti_test),
            ("与豆包聊聊", self.show_doubao_chat),
            ("放松一下", self.show_relaxing_page)
        ]
        
        for text, callback in buttons:
            btn = QPushButton(text)
            btn.setFont(QFont("Microsoft YaHei", 14))
            btn.setFixedHeight(50)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    min-width: 250px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            btn.clicked.connect(callback)
            right_layout.addWidget(btn, alignment=Qt.AlignCenter)
            right_layout.addSpacing(20)
        
        right_layout.addStretch()
        layout.addWidget(right_frame)
        
        return page

    def start_mbti_test(self):
        QMessageBox.information(self, "MBTI人格测试", 
                              "即将开始MBTI性格测试...\n\n"
                              "本测试包含40个问题，约需10分钟完成。")
        self.stack.setCurrentWidget(self.mbti_test_page)
    
    def show_doubao_chat(self):
        """显示豆包对话窗口"""
        self.stack.setCurrentWidget(self.doubao_chat)
    
    def show_relaxing_page(self):
        """显示放松音乐页面"""
        self.stack.setCurrentWidget(self.relaxing_page)

    def show_mbti_result(self, mbti_type):
        # 创建结果页面
        result_page = QWidget()
        layout = QVBoxLayout()
        result_page.setLayout(layout)
        
        # 结果标题
        title = QLabel(f"您的MBTI类型是: {mbti_type}")
        title.setFont(QFont("Microsoft YaHei", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 30px;")
        layout.addWidget(title)
        
        # 类型描述
        desc = QLabel(self.get_mbti_description(mbti_type))
        desc.setWordWrap(True)
        desc.setFont(QFont("Microsoft YaHei", 12))
        desc.setStyleSheet("margin: 0 50px;")
        layout.addWidget(desc)
        
        # 豆包分析按钮
        analyze_btn = QPushButton("让豆包分析我的性格")
        analyze_btn.setFont(QFont("Microsoft YaHei", 14))
        analyze_btn.setFixedHeight(50)
        analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                min-width: 200px;
            }
        """)
        analyze_btn.clicked.connect(lambda: self.analyze_mbti_with_doubao(mbti_type))
        layout.addWidget(analyze_btn, alignment=Qt.AlignCenter)
        
        # 返回按钮
        back_btn = QPushButton("返回主页")
        back_btn.setFont(QFont("Microsoft YaHei", 14))
        back_btn.setFixedHeight(50)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                min-width: 200px;
            }
        """)
        back_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.main_page))
        layout.addWidget(back_btn, alignment=Qt.AlignCenter)
        layout.addStretch()
        
        # 添加到堆叠窗口并切换
        if self.mbti_result_page:
            self.stack.removeWidget(self.mbti_result_page)
        self.mbti_result_page = result_page
        self.stack.addWidget(self.mbti_result_page)
        self.stack.setCurrentWidget(self.mbti_result_page)
    
    def get_mbti_description(self, mbti_type):
        """获取MBTI类型的描述"""
        descriptions = {
            "ISTJ": "ISTJ型的人是严肃的、有责任心的和通情达理的社会坚定分子。他们值得信赖，重视承诺，是传统主义者。",
            "ISFJ": "ISFJ型的人忠诚、有奉献精神和同情心，理解别人的感受。他们重视和谐与合作，乐于支持和帮助他人。",
            "INFJ": "INFJ型的人生活在思想的世界里，是独立的、有独创性的思想家，具有强烈的感情、坚定的原则和正直的人性。",
            "INTJ": "INTJ型的人是完美主义者，他们强烈地要求个人自由和能力，同时在他们独创的思想中，不可动摇的信仰促使他们达到目标。",
            "ISTP": "ISTP型的人坦率、诚实、讲求实效，他们喜欢行动而非漫谈。他们很谦逊，对于完成工作的方法有很好的理解力。",
            "ISFP": "ISFP型的人平和、敏感，他们保持着许多强烈的个人理想和自己的价值观念。他们更多地是通过行为而不是言辞表达自己深沉的情感。",
            "INFP": "INFP型的人把内在的和谐视为高于一切，他们敏感、理想化、忠诚，对于个人价值具有一种强烈的荣誉感。",
            "INTP": "INTP型的人是解决理性问题者，他们很有才智和条理性，以及创造才华的突出表现。他们外表平静、缄默、超然，内心却专心致志于分析问题。",
            "ESTP": "ESTP型的人不会焦虑，他们是快乐的。ESTP型的人活跃、随遇而安、天真率直。他们喜欢物质享受和冒险。",
            "ESFP": "ESFP型的人乐意与人相处，有一种真正的生活热情。他们顽皮活泼，通过真诚和玩笑使别人感到事情更加有趣。",
            "ENFP": "ENFP型的人充满热情和新思想，他们乐观、自然、富有创造性和自信，具有独创性的思想和对可能性的强烈感受。",
            "ENTP": "ENTP型的人喜欢兴奋与挑战，他们热情开放、足智多谋、健谈而聪明，擅长于许多事情，不断追求增加能力和个人权力。",
            "ESTJ": "ESTJ型的人高效率地工作，自我负责，监督他人工作，合理分配和处置资源，主次分明，井井有条。",
            "ESFJ": "ESFJ型的人通过直接的行动和合作积极地以真实、实际的方法帮助别人，他们友好、富有同情心和责任感。",
            "ENFJ": "ENFJ型的人热爱人类，他们认为人的感情是最重要的，而且他们很自然地关心别人。他们以热情的态度对待生活，感受很深。",
            "ENTJ": "ENTJ型的人是伟大的领导者和决策人，他们能轻易地看出事物具有的可能性，很高兴指导别人，使他们的想象成为现实。"
        }
        return descriptions.get(mbti_type, "这是一种神秘而独特的MBTI类型，充满了未知的可能性。")
    
    def analyze_mbti_with_doubao(self, mbti_type):
        """使用豆包API分析MBTI类型"""
        # 切换到豆包对话窗口
        self.stack.setCurrentWidget(self.doubao_chat)
        
        # 发送分析请求
        message = f"请分析一下MBTI类型为{mbti_type}的人的性格特点，以及适合他们的减压方法和职业建议"
        self.doubao_chat.message_input.setText(message)
        self.doubao_chat.send_message()


if __name__ == "__main__":
    app = QApplication([])
    app.setStyle("Fusion")
    
    # 尝试加载样式表
    try:
        with open("style.qss", "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except:
        pass
    
    window = MentalHealthApp()
    window.show()
    app.exec_()
