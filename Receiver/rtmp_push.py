import cv2
import subprocess
import numpy as np


def process_and_push_stream():
    # 1. 配置参数
    input_url = "rtmp://116.62.11.13:1935/live/test"  # 无人机视频流地址
    output_url = "rtmp://116.62.11.13:1935/live/push"  # 处理后推流地址

    cap = cv2.VideoCapture(input_url)

    # 获取输入流的原始参数
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    if fps <= 0: fps = 30  # 如果获取不到则设为默认值

    # 2. 构建 FFmpeg 推流命令行
    # 这里的参数针对实时推流进行了优化：
    # - preset: ultrafast (降低延迟)
    # - tune: zerolatency (零延迟优化)
    # - pix_fmt: yuv420p (RTMP最通用的格式)
    command = [
        'ffmpeg',
        '-y',
        '-f', 'rawvideo',  # 输入格式为原始视频
        '-vcodec', 'rawvideo',
        '-pix_fmt', 'bgr24',  # OpenCV 处理完默认是 BGR 格式
        '-s', f"{width}x{height}",  # 帧大小
        '-r', str(fps),  # 帧率
        '-i', '-',  # 从管道读取输入
        '-c:v', 'libx264',  # 使用 H.264 编码
        '-pix_fmt', 'yuv420p',  # 输出像素格式
        '-preset', 'ultrafast',
        '-tune', 'zerolatency',
        '-f', 'flv',  # RTMP 必须使用 flv 格式封装
        output_url
    ]

    # 3. 启动 FFmpeg 进程
    pipe = subprocess.Popen(command, stdin=subprocess.PIPE)

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("读取视频帧失败")
                break

            # --- 在这里进行你的无人机图像处理逻辑 ---
            # 例如：目标检测、边缘提取、打水印等
            # processed_frame = your_model.predict(frame)
            processed_frame = cv2.putText(frame, "Drone Live Tracking", (50, 50),
                                          cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # ---------------------------------------

            # 4. 将处理后的帧写入管道发送给 FFmpeg
            pipe.stdin.write(processed_frame.tobytes())

    except KeyboardInterrupt:
        print("停止推流")
    finally:
        cap.release()
        pipe.stdin.close()
        pipe.wait()


if __name__ == "__main__":
    process_and_push_stream()