import cv2
import yaml
import sys
import time

def load_config(config_path='config.yaml'):
    """加载 YAML 配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"错误：配置文件 {config_path} 未找到。")
        sys.exit(1)
    except Exception as e:
        print(f"加载配置文件时出错: {e}")
        sys.exit(1)

def main():
    """主函数，用于接收和显示 rtmp_push 的视频流"""
    config = load_config()
    # 从配置中获取推流地址，因为我们要测试的是 rtmp.py 推流的结果
    rtmp_url = config.get('rtmp_push', {}).get('url')

    if not rtmp_url:
        print("错误：配置文件中未找到 'rtmp_push' 的 URL。")
        print("请确保 config.yaml 中有 rtmp_push 的配置。")
        return

    print(f"正在尝试连接到RTMP推流地址: {rtmp_url}")
    cap = cv2.VideoCapture(rtmp_url)

    try:
        while True:
            # 检查连接是否仍然打开
            if not cap.isOpened():
                print("无法连接到流，将在5秒后重试...")
                time.sleep(5)
                cap.release()
                cap = cv2.VideoCapture(rtmp_url)
                continue

            ret, frame = cap.read()

            if not ret:
                print("无法读取帧，流可能已中断。正在尝试重新连接...")
                cap.release()
                time.sleep(1) # 短暂等待后立即尝试重连
                cap = cv2.VideoCapture(rtmp_url)
                continue

            # 显示视频帧
            cv2.imshow('RTMP Push Test Receiver', frame)

            # 检测按键，如果按下 'q' 则退出
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("检测到 'q' 键按下，正在停止程序。")
                break

    except KeyboardInterrupt:
        print("\n检测到手动中断，正在停止程序。")
    finally:
        # 清理资源
        if cap.isOpened():
            cap.release()
        cv2.destroyAllWindows()
        print("程序已停止。")

if __name__ == "__main__":
    main()