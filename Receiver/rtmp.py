import cv2
import yaml
import time
import sys
import argparse

def load_config(config_path='config.yaml'):
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"错误：配置文件 {config_path} 未找到。")
        sys.exit()
    except Exception as e:
        print(f"加载配置文件时出错: {e}")
        sys.exit()

def handle(target_width=960, target_height=540, target_fps=30):
    config = load_config()
    rtmp_url = config.get('rtmp', {}).get('url')

    if not rtmp_url:
        print("错误：配置文件中未指定RTMP URL。")
        return

    print(f"正在尝试连接到RTMP流: {rtmp_url}")
    cap = cv2.VideoCapture(rtmp_url)

    if not cap.isOpened():
        print("错误：无法打开RTMP流。请检查URL是否正确或网络连接是否正常。")
        return

    # 用于通过控制显示间隔来近似实现目标帧率
    frame_interval = 1.0 / target_fps
    last_show_time = 0

    print(f"目标显示属性: {target_width}x{target_height} @ {target_fps:.2f} FPS")

    try:
        while True:
            ret, frame = cap.read()

            if not ret:
                print("无法读取视频帧，可能连接已断开。将在5秒后尝试重新连接")
                cap.release()
                cv2.destroyAllWindows() # 关闭窗口
                time.sleep(5)
                cap = cv2.VideoCapture(rtmp_url)
                if not cap.isOpened():
                    print("重新连接失败。程序退出。")
                    break
                last_show_time = 0 # 重置计时器
                continue

            current_time = time.time()
            # 通过控制显示间隔来近似实现目标帧率
            if current_time - last_show_time < frame_interval:
                continue  # 跳过此帧以匹配目标FPS

            last_show_time = current_time

            # 调整帧大小
            resized_frame = cv2.resize(frame, (target_width, target_height))

            """
            模型处理
            """

            # 显示视频帧
            cv2.imshow('RTMP Stream', resized_frame)

            # 检测按键，如果按下 'q' 则退出
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("检测到 'q' 键按下，正在停止程序")
                break

    except KeyboardInterrupt:
        print("\n检测到手动中断，正在停止程序")
    finally:
        # 清理资源
        if cap.isOpened():
            cap.release()
        cv2.destroyAllWindows()
        print("程序已停止")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RTMP Stream Receiver and Displayer.")
    parser.add_argument("--width", type=int, default=960, help="Target width for the displayed video.")
    parser.add_argument("--height", type=int, default=540, help="Target height for the displayed video.")
    parser.add_argument("--fps", type=float, default=30.0, help="Target FPS for the displayed video.")
    args = parser.parse_args()

    handle(target_width=args.width, target_height=args.height, target_fps=args.fps)