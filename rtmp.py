import cv2
import yaml
import time
import sys
import argparse
import subprocess

def load_config(config_path='config.yaml'):
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"错误：配置文件 {config_path} 未找到。")
        sys.exit(1)
    except Exception as e:
        print(f"加载配置文件时出错: {e}")
        sys.exit(1)

def handle(target_width, target_height, target_fps):
    config = load_config()
    rtmp_url_pull = config.get('rtmp_pull', {}).get('url')
    rtmp_url_push = config.get('rtmp_push', {}).get('url')

    if not rtmp_url_pull or not rtmp_url_push:
        print("错误：配置文件中必须同时指定 'rtmp_pull' 和 'rtmp_push' 的 URL。")
        return

    # FFmpeg 推流命令
    command_push = [
        'ffmpeg',
        '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-pix_fmt', 'bgr24',
        '-s', f'{target_width}x{target_height}',
        '-r', str(target_fps),
        '-i', '-',
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-preset', 'ultrafast',
        '-f', 'flv',
        rtmp_url_push
    ]

    print(f"从 {rtmp_url_pull} 拉流")
    print(f"推流到 {rtmp_url_push}")
    print(f"处理参数: {target_width}x{target_height} @ {target_fps} FPS")

    # 启动推流的 FFmpeg 子进程
    push_process = subprocess.Popen(command_push, stdin=subprocess.PIPE)

    cap = cv2.VideoCapture(rtmp_url_pull)

    if not cap.isOpened():
        print("错误：无法打开RTMP拉流地址。请检查URL或网络。")
        push_process.terminate()
        return

    try:
        while True:
            ret, frame = cap.read()

            if not ret:
                print("无法读取视频帧，可能连接已断开。将在5秒后尝试重新连接...")
                cap.release()
                time.sleep(5)
                cap = cv2.VideoCapture(rtmp_url_pull)
                if not cap.isOpened():
                    print("重新连接失败。程序退出。")
                    break
                continue

            # 调整帧大小
            resized_frame = cv2.resize(frame, (target_width, target_height))


            """
            # -----------------------------------
            # 在这里进行模型处理
            # processed_frame = your_model_function(resized_frame)
            # 暂时直接使用调整大小后的帧
            # -----------------------------------
            """

            processed_frame = resized_frame


            try:
                # 将处理后的帧写入推流进程
                push_process.stdin.write(processed_frame.tobytes())
            except BrokenPipeError:
                print("错误: 推流的 FFmpeg 进程已关闭。可能是推流地址有问题。")
                break

    except KeyboardInterrupt:
        print("\n检测到手动中断，正在停止程序")
    finally:
        # 清理资源
        if cap.isOpened():
            cap.release()
        
        print("正在关闭推流进程...")
        if push_process.stdin:
            push_process.stdin.close()
        if push_process.poll() is None:
            push_process.terminate()
            push_process.wait(timeout=5)
        if push_process.poll() is None:
            push_process.kill()

        cv2.destroyAllWindows()
        print("程序已停止")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RTMP Stream Processor (Pull -> Process -> Push).")
    parser.add_argument("--width", type=int, default=960, help="Target width for processing and pushing.")
    parser.add_argument("--height", type=int, default=540, help="Target height for processing and pushing.")
    parser.add_argument("--fps", type=float, default=30, help="Target FPS for processing and pushing.")
    args = parser.parse_args()

    handle(target_width=args.width, target_height=args.height, target_fps=args.fps)