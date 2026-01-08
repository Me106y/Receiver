import cv2
import yaml
import os
import time
from datetime import datetime

def load_config(config_path='config.yaml'):
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"错误：配置文件 {config_path} 未找到。")
        exit()
    except Exception as e:
        print(f"加载配置文件时出错: {e}")
        exit()

def main():
    """主函数"""
    config = load_config()
    rtsp_url = config.get('rtsp', {}).get('url')
    save_path = config.get('save_path', 'videos/')

    if not rtsp_url:
        print("错误：配置文件中未指定RTSP URL。")
        return

    # 如果保存目录不存在，则创建它
    if not os.path.exists(save_path):
        print(f"保存目录 {save_path} 不存在，正在创建...")
        os.makedirs(save_path)

    print(f"正在尝试连接到RTSP流: {rtsp_url}")
    cap = cv2.VideoCapture(rtsp_url)

    if not cap.isOpened():
        print("错误：无法打开RTSP流。请检查URL是否正确或网络连接是否正常。")
        return

    # 获取视频流的属性
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # 如果无法获取FPS，使用默认值
    if fps == 0:
        print("无法从流中获取FPS，使用默认值30。")
        fps = 30.0

    print(f"视频流属性: {frame_width}x{frame_height} @ {fps:.2f} FPS")

    # 定义视频编码器和片段时长
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    segment_duration = 30  # 秒

    out = None
    start_time = time.time()

    try:
        while True:
            ret, frame = cap.read()

            if not ret:
                print("无法读取视频帧，可能连接已断开。将在5秒后尝试重新连接")
                cap.release()
                if out:
                    out.release()
                time.sleep(5)
                cap = cv2.VideoCapture(rtsp_url)
                if not cap.isOpened():
                    print("重新连接失败。程序退出。")
                    break

                # 重置计时器和写入器
                start_time = time.time()
                out = None
                continue

            current_time = time.time()
            elapsed_time = current_time - start_time

            # 如果没有写入器或已达到片段时长，则创建新的视频文件
            if out is None or elapsed_time >= segment_duration:
                if out is not None:
                    out.release()
                    print(f"视频片段已保存")

                # 创建新的视频片段
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = os.path.join(save_path, f"{timestamp}.mp4")
                print(f"开始录制新片段: {filename}")
                out = cv2.VideoWriter(filename, fourcc, fps, (frame_width, frame_height))
                start_time = current_time

            if out is not None:
                out.write(frame)

    except KeyboardInterrupt:
        print("\n检测到手动中断，正在停止程序")
    finally:
        # 清理资源
        if out is not None:
            out.release()
            print("最后一个视频片段已保存")
        if cap.isOpened():
            cap.release()
        cv2.destroyAllWindows()
        print("程序已停止")

if __name__ == "__main__":
    main()